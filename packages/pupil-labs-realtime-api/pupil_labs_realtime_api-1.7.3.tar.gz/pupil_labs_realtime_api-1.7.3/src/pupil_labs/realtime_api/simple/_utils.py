from __future__ import annotations

import asyncio
import logging
import weakref
from collections import deque
from collections.abc import Hashable, Iterable, Mapping
from types import MappingProxyType
from typing import Any, Generic, TypeVar

from ..models import Sensor, SensorName
from ..streaming import (
    AudioFrame,
    RTSPEyeEventStreamer,
    RTSPGazeStreamer,
    RTSPImuStreamer,
    RTSPRawStreamer,
    RTSPVideoFrameStreamer,
)
from .models import (
    MATCHED_GAZE_EYES_LABEL,
    MATCHED_ITEM_LABEL,
    MATCHED_SCENE_AUDIO_LABEL,
    GazeDataType,
    MatchedGazeEyesSceneItem,
    MatchedItem,
    MatchedSceneAudioItem,
    SimpleVideoFrame,
)

logger_name = "pupil_labs.realtime_api.simple"
logger = logging.getLogger(logger_name)
logger_receive_data = logging.getLogger(logger_name + ".Device.receive_data")
logger_receive_data.setLevel(logging.INFO)

ItemType = SimpleVideoFrame | GazeDataType | AudioFrame | Any
EventKey = TypeVar("EventKey", bound=Hashable)
StreamerClassType = type[
    RTSPVideoFrameStreamer
    | RTSPGazeStreamer
    | RTSPImuStreamer
    | RTSPEyeEventStreamer
    | RTSPRawStreamer
]
"""Type of streamer classes used for streaming data from sensors."""


class _AsyncEventManager(Generic[EventKey]):
    """Manages a collection of named asyncio events.

    Provides mechanisms to trigger events (including thread-safe triggering)
    and wait for the first event among the managed collection to be set.

    Designed for internal use within asynchronous contexts.

    Attributes:
        events: A read-only mapping of registered event keys to their
                corresponding asyncio.Event objects.
        name_to_register: An iterable of event keys to register.

    """

    def __init__(
        self,
        names_to_register: Iterable[EventKey],
    ) -> None:
        self._loop = asyncio.get_running_loop()
        self._events = {name: asyncio.Event() for name in names_to_register}
        if not self._events:
            raise ValueError("Requires at least one event key to register")

    @property
    def events(self) -> Mapping[EventKey, asyncio.Event]:
        """Provides read-only access to the managed events dictionary."""
        return MappingProxyType(self._events)

    def trigger(self, name: EventKey) -> None:
        """Set the event associated with the given name.

        Args:
            name: The key of the event to trigger (set).

        Raises:
            KeyError: If `name` is not a registered event key.

        """
        self._events[name].set()

    def trigger_threadsafe(
        self,
        name: EventKey,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        """Set the event associated with the given name in a thread-safe manner.

        Schedules the event's `set()` method to be called within the specified
        event loop (or the loop the manager was created in).

        Args:
            name: The key of the event to trigger.
            loop: The asyncio event loop to run the trigger in. Defaults to the
                loop the manager was initialized with.

        Raises:
            KeyError: If `name` is not a registered event key.

        """
        loop = loop or self._loop
        loop.call_soon_threadsafe(self.trigger, name)

    async def wait_for_first_event(self) -> EventKey:
        """Wait until any one of the managed events is set.

        Once an event is set, this method returns the key associated with that
        event. It also clears the triggered event and cancels the waits for
        any other pending events within this specific call.

        Returns:
            The key of the first event that was triggered.

        """
        tasks = {
            asyncio.create_task(event.wait()): name
            for name, event in self._events.items()
        }
        done, pending = await asyncio.wait(
            tasks.keys(), return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        first_task = next(iter(done))
        event_key = tasks[first_task]
        self._events[event_key].clear()
        return event_key


class _MatchingHandler:
    """A stateless handler that encapsulates the logic for processing and matching."""

    def process_item(self, item: ItemType, sensor_name: str, device: Any) -> None:
        """Handle an incoming items, performing caching and matching logic."""
        if sensor_name == SensorName.GAZE.value:
            device._cached_gaze_for_matching.append((
                item.timestamp_unix_seconds,
                item,
            ))
        elif sensor_name == SensorName.EYES.value:
            device._cached_eyes_for_matching.append((
                item.timestamp_unix_seconds,
                item,
            ))
        elif sensor_name == SensorName.AUDIO.value:
            device._cached_audio_for_matching.append((
                item.timestamp_unix_seconds,
                item,
            ))
        elif sensor_name == SensorName.WORLD.value:
            self._match(item, device)  # type: ignore[arg-type]
        elif sensor_name in (SensorName.IMU.value, SensorName.EYE_EVENTS.value):
            pass
        else:
            logger.error(f"Unhandled {item} for sensor {sensor_name}")

    def _match(self, world_frame: SimpleVideoFrame, device: Any) -> None:
        """Perform the matching logic for a world frame and matched items."""
        gaze = eyes = audio_frames = None
        nan = float("nan")
        gaze_match_time_diff = eyes_match_time_diff = gaze_eyes_time_diff = (
            audio_time_diff
        ) = nan

        try:
            gaze = _get_closest_item(
                device._cached_gaze_for_matching, world_frame.timestamp_unix_seconds
            )
        except IndexError:
            logger_receive_data.info("No gaze data to match with world frame.")
        else:
            gaze_match_time_diff = (
                world_frame.timestamp_unix_seconds - gaze.timestamp_unix_seconds
            )
            matched_item = MatchedItem(world_frame, gaze)
            device._most_recent_item[MATCHED_ITEM_LABEL].append(matched_item)
            device._event_new_item[MATCHED_ITEM_LABEL].set()

        if gaze:
            try:
                eyes = _get_closest_item(
                    device._cached_eyes_for_matching, world_frame.timestamp_unix_seconds
                )
            except IndexError:
                logger_receive_data.debug("No eyes data for matching.")
            else:
                eyes_match_time_diff = (
                    world_frame.timestamp_unix_seconds - eyes.timestamp_unix_seconds
                )
                gaze_eyes_time_diff = (
                    gaze.timestamp_unix_seconds - eyes.timestamp_unix_seconds
                )
                matched_item = MatchedGazeEyesSceneItem(world_frame, eyes, gaze)  # type: ignore
                device._most_recent_item[MATCHED_GAZE_EYES_LABEL].append(matched_item)
                device._event_new_item[MATCHED_GAZE_EYES_LABEL].set()

        try:
            audio_frames = _get_closest_items(
                device._cached_audio_for_matching, world_frame.timestamp_unix_seconds
            )
            if audio_frames:
                matched_item = MatchedSceneAudioItem(world_frame, audio_frames, gaze)  # type: ignore
                device._most_recent_item[MATCHED_SCENE_AUDIO_LABEL].append(matched_item)
                device._event_new_item[MATCHED_SCENE_AUDIO_LABEL].set()
                audio_time_diff = (
                    world_frame.timestamp_unix_seconds
                    - audio_frames[-1].timestamp_unix_seconds
                )
        except IndexError:
            logger_receive_data.debug("No audio data for matching.")

        logger_receive_data.debug(
            f"Matching results for world frame ts={world_frame.timestamp_unix_seconds:.3f}:\n"  # noqa: E501
            f"\tscene - gaze: {gaze_match_time_diff:.3f}s\n"
            f"\tscene - eyes: {eyes_match_time_diff:.3f}s\n"
            f"\tgaze - eyes: {gaze_eyes_time_diff:.3f}s\n"
            f"\tscene - audio: {audio_time_diff:.3f}s"
        )


class _StreamManager:
    """Manages a single RTSP stream connection and data processing.

    Handles starting and stopping the stream based on sensor connectivity
    and an externally controlled 'should_be_streaming' flag. It also
    performs timestamp-based matching between world camera frames, gaze data,
    and eye camera frames when processing world camera streams.

    Designed for internal use, associated with a `Device` instance.

    Args:
        device_weakref: A weak reference to the parent `Device` object. Used
            to access shared data queues and caches without creating circular
            references.
        streaming_cls: The specific RTSP streamer class (either for video frames
            or gaze data) to be used for this stream.
        should_be_streaming_by_default: The initial intended state of the
            stream (whether it should attempt to stream immediately if a
            sensor is available).

    """

    def __init__(
        self,
        device_weakref: weakref.ReferenceType,
        streaming_cls: StreamerClassType,
        should_be_streaming_by_default: bool = False,
    ) -> None:
        self._device = device_weakref
        self._streaming_cls = streaming_cls
        self._streaming_task: asyncio.Task | None = None
        self._should_be_streaming: bool = should_be_streaming_by_default
        self._recent_sensor: Sensor | None = None
        self.matching_handler = _MatchingHandler()

    @property
    def should_be_streaming(self) -> bool:
        """Indicates whether the stream is intended to be active."""
        return self._should_be_streaming

    @should_be_streaming.setter
    def should_be_streaming(self, should_stream: bool) -> None:
        """Set the intended streaming state and starts/stops the stream task.

        If the state changes and `should_stream` is True, it attempts to start
        streaming using the most recent sensor information (if available and
        connected). If `should_stream` is False, it stops any active streaming task.

        Args:
            should_stream: The desired streaming state (True to stream, False to stop).

        """
        if self._should_be_streaming == should_stream:
            return  # state is already set to desired value
        self._should_be_streaming = should_stream
        if should_stream and self._recent_sensor is not None:
            self._start_streaming_task_if_intended(self._recent_sensor)
        elif not should_stream:
            self._stop_streaming_task_if_running()

    async def handle_sensor_update(self, sensor: Sensor) -> None:
        """Update the manager with new sensor information and adjusts streaming.

        Stops any currently running stream associated with the previous sensor state.
        Then, if streaming is intended (`should_be_streaming` is True) and the
        new sensor is connected, it starts a new streaming task.

        Args:
            sensor: The updated Sensor information.

        """
        self._stop_streaming_task_if_running()
        self._start_streaming_task_if_intended(sensor)
        self._recent_sensor = sensor

    def _start_streaming_task_if_intended(self, sensor: Sensor) -> None:
        """Start the streaming task if streaming is intended and sensor is connected.

        Checks if `should_be_streaming` is True and the provided `sensor` is
        connected. If both conditions are met and no task is currently running,
        it creates and starts the `append_data_from_sensor_to_queue` task.

        Args:
            sensor: The Sensor information used to establish the stream.

        """
        if sensor.connected and self.should_be_streaming:
            logger_receive_data.info(f"Starting stream to {sensor}")
            self._streaming_task = asyncio.create_task(
                self.append_data_from_sensor_to_queue(sensor)
            )

    def _stop_streaming_task_if_running(self) -> None:
        """Cancel and clears the current streaming task if it exists."""
        if self._streaming_task is not None:
            sensor_name = (
                self._recent_sensor.sensor if self._recent_sensor else "unknown sensor"
            )
            logger_receive_data.info(
                f"Cancelling prior streaming connection to {sensor_name}"
            )
            self._streaming_task.cancel()
            self._streaming_task = None

    async def append_data_from_sensor_to_queue(self, sensor: Sensor) -> None:
        """Connect to the sensor's RTSP stream and processes incoming data.

        Establishes a connection using the provided `sensor` URL and the
        manager's `_streaming_cls`. It receives items (e.g. gaze data or video frames),
        converts video frames if necessary, appends them to the appropriate queue
        in the parent `Device` (via weakref), performs timestamp-based matching
        for world camera frames with gaze and eyes data, and triggers events
        on the parent `Device` upon receiving new or matched items.

        Args:
            sensor: The Sensor whose stream should be processed.

        Raises:
            Various exceptions from the underlying streaming class (`_streaming_cls`)
            if connection or data reception fails.
            AttributeError: If the parent Device accessed via weakref no longer exists.

        """
        if self._device() is None:
            raise AttributeError(
                "Device reference no longer exists. Cannot append data to queue."
            )
        self._device()._cached_gaze_for_matching.clear()  # type: ignore[union-attr]
        self._device()._cached_eyes_for_matching.clear()  # type: ignore[union-attr]
        self._device()._cached_audio_for_matching.clear()  # type: ignore[union-attr]

        async with self._streaming_cls(
            sensor.url, run_loop=True, log_level=logging.WARNING
        ) as streamer:
            async for item in streamer.receive():
                device = self._device()
                if device is None:
                    logger_receive_data.info("Device reference does no longer exist")
                    break
                name = sensor.sensor

                if name in (SensorName.WORLD.value, SensorName.EYES.value):
                    # convert to simple video frame
                    item = SimpleVideoFrame.from_video_frame(item)  # type: ignore[arg-type, assignment]

                logger_receive_data.debug(f"{self} received {item}")
                device._most_recent_item[name].append(item)

                self.matching_handler.process_item(item, name, device)

                device._event_new_item[name].set()
                del device  # remove Device reference


def _get_closest_item(
    cache: deque[tuple[float, GazeDataType]], timestamp: float
) -> GazeDataType:
    """Get the closest item in the cache to the given timestamp."""
    item_ts, item = cache.popleft()
    # assumes monotonically increasing timestamps
    if item_ts > timestamp:
        return item
    while True:
        try:
            next_item_ts, next_item = cache.popleft()
        except IndexError:
            return item
        else:
            if next_item_ts > timestamp:
                return next_item
            item_ts, item = next_item_ts, next_item


def _get_closest_items(
    cache: deque[tuple[float, AudioFrame]], timestamp: float, tolerance: float = 34
) -> list[AudioFrame]:
    """Get the closest items in the cache to the given timestamp."""
    items = []
    while cache:
        item_ts, _ = cache[0]
        if item_ts > timestamp + tolerance:
            break
        if item_ts < timestamp - tolerance:
            cache.popleft()
            continue

        items.append(cache.popleft()[1])

    return items


__all__ = ["_AsyncEventManager", "_StreamManager"]
