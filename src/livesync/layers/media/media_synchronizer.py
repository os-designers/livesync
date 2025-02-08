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
class MediaSynchronizerLayer(CallableLayer[dict[str, MediaFrameType] | MediaFrameType, MediaFrameType | None]):
    """A synchronizer that waits for both audio and video frames before returning an output.

    When a new frame comes in (audio or video), it finds the counterpart frame from the other
    stream, compares their timestamps (computed from pts and time_base), and adjusts the incoming
    frame's pts to be as close as possible to the counterpart's timestamp. This ensures that the
    frames—when later saved to a media file—are in proper sync and order.

    Parameters
    ----------
    sync_enabled : bool, default True
        Whether synchronization should be active.
    max_delay : float, default 0.1
        Maximum allowed delay (in seconds) between matching audio and video frames. If the time
        gap exceeds this value, the incoming frame is not released.
    sync_tolerance : float, default 0.005
        Time tolerance (in seconds) below which frames are considered in-sync. If the gap is less
        than this value, the matching counterpart is removed from its buffer.
    buffer_size : int, default 30
        Maximum number of frames to buffer for each stream.
    """

    def __init__(
        self,
        sync_enabled: bool = True,
        max_delay: float = 0.1,
        sync_tolerance: float = 0.005,
        buffer_size: int = 30,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.sync_enabled = sync_enabled
        self.max_delay = max_delay
        self.sync_tolerance = sync_tolerance
        self.buffer_size = buffer_size

        self._audio_buffer: Deque[AudioFrame] = deque(maxlen=self.buffer_size)
        self._video_buffer: Deque[VideoFrame] = deque(maxlen=self.buffer_size)

        self._lock = asyncio.Lock()

    async def process_frame(self, frame: MediaFrameType) -> MediaFrameType | None:
        """
        Process an incoming audio or video frame. It buffers frames and only returns an output once
        both audio and video frames are available. When a new frame is processed, it finds the best
        matching counterpart frame from the other buffer and—if the time difference is within the
        allowed maximum delay—adjusts the new frame's pts based on the average of both timestamps.

        If synchronization cannot be achieved (either because the counterpart is not available or
        the time gap is too large), None is returned.

        Returns
        -------
        MediaFrameType or None
            The adjusted frame (synchronized with its counterpart) or None if sync is not possible.
        """
        # async with self._lock:
        if not self.sync_enabled:
            return frame

        try:
            frame_time = frame.pts * float(frame.time_base)
        except Exception as e:
            raise ValueError("Frame must have a valid time_base") from e

        if isinstance(frame, VideoFrame):
            self._video_buffer.append(frame)
            if not self._audio_buffer:
                # No audio frame yet, so we cannot compare.
                return None

            # Find the audio frame with the closest timestamp.
            best_audio = min(self._audio_buffer, key=lambda af: abs(frame_time - (af.pts * float(af.time_base))))
            audio_time = best_audio.pts * float(best_audio.time_base)
            time_diff = frame_time - audio_time

            if abs(time_diff) > self.max_delay:
                # The difference is too large; either wait for a better matchup or skip.
                return None

            # Adjust the video frame's pts to the average time between video and its matching audio.
            sync_time = (frame_time + audio_time) / 2
            frame.pts = int(sync_time / float(frame.time_base))

            # Optionally remove the audio frame if it’s practically in sync.
            if abs(frame_time - audio_time) < self.sync_tolerance:
                self._audio_buffer.remove(best_audio)

            return frame

        else:
            self._audio_buffer.append(frame)
            if not self._video_buffer:
                return None

            best_video = min(self._video_buffer, key=lambda vf: abs(frame_time - (vf.pts * float(vf.time_base))))
            video_time = best_video.pts * float(best_video.time_base)
            time_diff = frame_time - video_time

            if abs(time_diff) > self.max_delay:
                return None

            sync_time = (frame_time + video_time) / 2
            frame.pts = int(sync_time / float(frame.time_base))

            if abs(frame_time - video_time) < self.sync_tolerance:
                self._video_buffer.remove(best_video)

            return frame

    async def call(self, x: dict[str, MediaFrameType] | MediaFrameType) -> MediaFrameType | None:
        try:
            # async with self._lock:
            if isinstance(x, dict):
                if len(x.values()) != 1:
                    raise ValueError("Expected exactly one stream")

            frame = next(iter(x.values())) if isinstance(x, dict) else x
            return await self.process_frame(frame)
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return None
