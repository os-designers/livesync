import asyncio
from logging import getLogger

import cv2

from ...core.nodes import Node
from ...core.fields import Field
from ...core.frames import VideoFrame
from ...utils.codec import get_video_codec

logger = getLogger(__name__)


class VideoRecorderNode(Node):
    """A node that records video frames to a file."""

    filename: str = Field(default=..., description="Path to the output video file (e.g., .mp4, .avi)")
    fps: float = Field(default=30.0, description="Frames per second for the output video")

    def bootstrap(self) -> None:
        """Initializes the video file writer."""
        if len(self.parents) != 1:
            raise ValueError("VideoRecorderNode must have a single parent")

        self._parent_node = self.parents[0]
        self._codec = get_video_codec(self.filename)
        self._writer: cv2.VideoWriter | None = None
        self._recording: bool = False
        self._lock = asyncio.Lock()

    async def step(self):
        """Receives video frames and writes them to the file."""
        frame: VideoFrame = await self.get_input(self._parent_node.name)

        async with self._lock:
            if self._writer is None:
                self._writer = cv2.VideoWriter(self.filename, self._codec, self.fps, (frame.width, frame.height))

            bgr_frame_data = cv2.cvtColor(frame.data, cv2.COLOR_RGB2BGR)  # type: ignore
            self._writer.write(bgr_frame_data)  # type: ignore

    async def shutdown(self):
        """Finalizes the file writing process."""
        self._recording = False
        async with self._lock:
            if self._writer is not None:
                self._writer.release()
                self._writer = None
