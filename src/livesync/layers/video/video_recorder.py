import asyncio

import av
import av.container

from ..._utils.logs import logger
from ...frames.video_frame import VideoFrame
from ..core.callable_layer import CallableLayer


class VideoRecorderLayer(CallableLayer[VideoFrame, None]):
    """A layer that records video frames to a file."""

    def __init__(self, filename: str, codec: str = "h264", name: str | None = None) -> None:
        super().__init__(name=name)
        self.filename = filename
        self.codec = codec

        self._container: av.container.OutputContainer | None = None
        self._stream: av.VideoStream | None = None
        self._lock = asyncio.Lock()
        self._first_pts: float | None = None

    async def call(self, x: VideoFrame) -> None:
        """Records video frames to a file using `av`."""
        try:
            async with self._lock:
                if self._container is None:
                    self._container = av.open(self.filename, mode="w")
                    self._stream = self._container.add_stream(self.codec)  # type: ignore
                    self._stream.width = x.width  # type: ignore
                    self._stream.height = x.height  # type: ignore
                    self._stream.pix_fmt = "yuv420p"  # type: ignore

                frame = av.VideoFrame.from_ndarray(x.data, format=x.buffer_type)  # type: ignore
                frame.pts = x.pts
                packet = self._stream.encode(frame)  # type: ignore
                self._container.mux(packet)
        except Exception as e:
            logger.error(f"Error recording video frame: {e}")

    async def cleanup(self) -> None:
        """Finalizes the file writing process."""
        async with self._lock:
            if self._stream is not None and self._container is not None:
                self._container.mux(self._stream.encode())
                self._container.close()
                self._container = None
                self._stream = None
