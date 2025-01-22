import asyncio

import cv2

from ..._utils.logs import logger
from ..._utils.codec import get_video_codec
from ...frames.video_frame import VideoFrame
from ..core.callable_layer import CallableLayer


class VideoRecorderLayer(CallableLayer[VideoFrame, None]):
    """A layer that records video frames to a file."""

    def __init__(self, filename: str, fps: float = 30.0, name: str | None = None) -> None:
        super().__init__(name=name)
        self.fps = fps
        self.filename = filename

        self._codec = get_video_codec(self.filename)
        self._writer: cv2.VideoWriter | None = None
        self._recording: bool = False
        self._lock = asyncio.Lock()

    async def call(self, x: VideoFrame) -> None:
        """Records video frames to a file."""
        try:
            async with self._lock:
                if self._writer is None:
                    self._writer = cv2.VideoWriter(self.filename, self._codec, self.fps, (x.width, x.height))

                bgr_frame_data = cv2.cvtColor(x.data, cv2.COLOR_RGB2BGR)  # type: ignore
                self._writer.write(bgr_frame_data)  # type: ignore
        except Exception as e:
            logger.error(f"Error recording video frame: {e}")

    async def cleanup(self) -> None:
        """Finalizes the file writing process."""
        self._recording = False
        async with self._lock:
            if self._writer is not None:
                self._writer.release()
                self._writer = None
