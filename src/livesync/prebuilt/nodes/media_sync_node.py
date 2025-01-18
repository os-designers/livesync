from typing import Deque
from logging import getLogger
from collections import deque

from ...core.nodes import Node
from ...core.fields import Field
from ...core.frames import AudioFrame, VideoFrame

logger = getLogger(__name__)


class MediaSyncNode(Node):
    max_sync_threshold_us: int = Field(
        default=5000, description="Maximum synchronization threshold in microseconds (default: 5ms)"
    )
    buffer_size: int = Field(default=30, description="Maximum number of frames to keep in buffer")
    audio_node: str = Field(default=..., description="Name of the audio node to synchronize with")
    video_node: str = Field(default=..., description="Name of the video node to synchronize with")

    def bootstrap(self) -> None:
        if len(self.parents) != 2:
            raise ValueError("MediaSyncNode must have exactly 2 parents (video and audio)")
        self._processing = False
        self._video_buffer: Deque[tuple[int, VideoFrame]] = deque(maxlen=self.buffer_size)
        self._audio_buffer: Deque[tuple[int, AudioFrame]] = deque(maxlen=self.buffer_size)

    async def step(self) -> tuple[VideoFrame, AudioFrame] | None:
        # If either node is empty, return None
        if self.is_input_empty(self.video_node) or self.is_input_empty(self.audio_node):
            return None

        # Get frames from each node
        video_frame: VideoFrame = await self.get_input(self.video_node)
        audio_frame: AudioFrame = await self.get_input(self.audio_node)

        time_diff = abs(video_frame.timestamp_us - audio_frame.timestamp_us)

        if time_diff > self.max_sync_threshold_us:
            # Get timestamps from buffers
            audio_timestamps = [ts for ts, _ in self._audio_buffer]
            video_timestamps = [ts for ts, _ in self._video_buffer]

            if audio_timestamps and video_timestamps:
                # Find closest matching frames
                closest_audio_ts = min(audio_timestamps, key=lambda x: abs(x - video_frame.timestamp_us))
                closest_video_ts = min(video_timestamps, key=lambda x: abs(x - audio_frame.timestamp_us))

                # Get the frame with better sync
                if abs(closest_audio_ts - video_frame.timestamp_us) < abs(closest_video_ts - audio_frame.timestamp_us):
                    audio_frame = next(frame for ts, frame in self._audio_buffer if ts == closest_audio_ts)
                else:
                    video_frame = next(frame for ts, frame in self._video_buffer if ts == closest_video_ts)

        # Store synchronized frames in buffers
        self._video_buffer.append((video_frame.timestamp_us, video_frame))
        self._audio_buffer.append((audio_frame.timestamp_us, audio_frame))

        return video_frame, audio_frame
