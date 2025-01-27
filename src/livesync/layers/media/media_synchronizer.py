import asyncio
from typing import Deque
from logging import getLogger
from collections import deque

from ...types import MediaFrameType
from ..._utils.logs import logger
from ...frames.audio_frame import AudioFrame
from ...frames.video_frame import VideoFrame
from ..core.callable_layer import CallableLayer

logger = getLogger(__name__)


# Reference:
# https://github.com/livekit/python-sdks/blob/main/livekit-rtc/livekit/rtc/synchronizer.py#L16
class MediaSynchronizerLayer(CallableLayer[dict[str, MediaFrameType], MediaFrameType | None]):
    """A layer that synchronizes video and audio frames.
    Always outputs the input frame, but adjusts timestamps if needed to maintain sync.

    Parameters
    ----------
    max_threshold : float, default=0.005
        Maximum synchronization threshold in seconds (default: 5ms)
    buffer_size : int, default=30
        Maximum number of frames to keep in buffer
    """

    def __init__(self, max_threshold: float = 0.005, buffer_size: int = 30, name: str | None = None) -> None:
        super().__init__(name=name)
        self.max_threshold = max_threshold
        self.buffer_size = buffer_size

        self._lock = asyncio.Lock()
        self._video_buffer: Deque[tuple[float, VideoFrame]] = deque(maxlen=self.buffer_size)
        self._audio_buffer: Deque[tuple[float, AudioFrame]] = deque(maxlen=self.buffer_size)
        self._last_video_pts = 0.0
        self._last_audio_pts = 0.0

    async def call(self, x: dict[str, MediaFrameType]) -> MediaFrameType | None:
        try:
            async with self._lock:
                if len(x.values()) != 1:
                    raise ValueError("Expected exactly one stream")

                frame = next(iter(x.values()))
                if isinstance(frame, VideoFrame):
                    return await self._process_video(frame)
                else:
                    return await self._process_audio(frame)
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return None

    async def _process_video(self, video_frame: VideoFrame) -> VideoFrame:
        if video_frame.time_base is None:
            raise ValueError("Video frame must have a time_base")

        self._video_buffer.append((video_frame.pts, video_frame))

        if not self._audio_buffer:
            self._last_video_pts = video_frame.pts
            return video_frame

        # Find closest audio timestamp for reference
        audio_timestamps = [(pts, frame.time_base) for pts, frame in self._audio_buffer]

        # Convert timestamps to seconds for comparison
        video_time = video_frame.pts * float(video_frame.time_base)
        audio_times = [pts * float(time_base) if time_base else pts for pts, time_base in audio_timestamps]

        closest_idx = min(range(len(audio_times)), key=lambda i: abs(audio_times[i] - video_time))
        closest_audio_pts = audio_timestamps[closest_idx][0]
        closest_audio_time_base = audio_timestamps[closest_idx][1]

        if closest_audio_time_base is None:
            return video_frame

        # Compare timestamps in seconds
        time_diff = video_time - (closest_audio_pts * float(closest_audio_time_base))

        # Adjust video timestamp if needed
        if abs(time_diff) > self.max_threshold:
            # If video is too far ahead, slow it down
            if time_diff > 0:
                adjusted_time = closest_audio_pts * float(closest_audio_time_base) + self.max_threshold
            # If video is too far behind, speed it up
            else:
                adjusted_time = closest_audio_pts * float(closest_audio_time_base) - self.max_threshold

            # Convert back to PTS units
            video_frame.pts = int(adjusted_time / float(video_frame.time_base))

        self._last_video_pts = video_frame.pts
        return video_frame

    async def _process_audio(self, audio_frame: AudioFrame) -> AudioFrame:
        if audio_frame.time_base is None:
            raise ValueError("Audio frame must have a time_base")

        self._audio_buffer.append((audio_frame.pts, audio_frame))

        if not self._video_buffer:
            self._last_audio_pts = audio_frame.pts
            return audio_frame

        # Find closest video timestamp for reference
        video_timestamps = [(pts, frame.time_base) for pts, frame in self._video_buffer]

        # Convert timestamps to seconds for comparison
        audio_time = audio_frame.pts * float(audio_frame.time_base)
        video_times = [pts * float(time_base) if time_base else pts for pts, time_base in video_timestamps]

        closest_idx = min(range(len(video_times)), key=lambda i: abs(video_times[i] - audio_time))
        closest_video_pts = video_timestamps[closest_idx][0]
        closest_video_time_base = video_timestamps[closest_idx][1]

        if closest_video_time_base is None:
            return audio_frame

        # Compare timestamps in seconds
        time_diff = audio_time - (closest_video_pts * float(closest_video_time_base))

        # Adjust audio timestamp if needed
        if abs(time_diff) > self.max_threshold:
            # If audio is too far ahead, slow it down
            if time_diff > 0:
                adjusted_time = closest_video_pts * float(closest_video_time_base) + self.max_threshold
            # If audio is too far behind, speed it up
            else:
                adjusted_time = closest_video_pts * float(closest_video_time_base) - self.max_threshold

            # Convert back to PTS units
            audio_frame.pts = int(adjusted_time / float(audio_frame.time_base))

        self._last_audio_pts = audio_frame.pts
        return audio_frame
