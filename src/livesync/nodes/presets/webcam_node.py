import time
import asyncio
from typing import AsyncIterator
from logging import getLogger
from dataclasses import dataclass
from typing_extensions import override

import cv2

from ..source_node import SourceNode
from ...frames.video_frame import VideoFrame

logger = getLogger(__name__)


@dataclass
class WebcamNode(SourceNode):
    """Captures frames from a webcam device."""

    device_id: int = 0
    fps: int = 30

    @override
    def __post_init__(self):
        """Initializes the webcam capture."""
        super().__post_init__()
        self._capture: cv2.VideoCapture | None = None
        self._loop = asyncio.get_event_loop()

    @override
    async def _source_frames(self) -> AsyncIterator[VideoFrame]:  # type: ignore[override]
        """Captures frames from the webcam and puts them into the queue."""
        self._capture = cv2.VideoCapture(self.device_id)
        if not self._capture.isOpened():
            raise RuntimeError(f"Failed to open webcam (device_id: {self.device_id})")

        self._capture.set(cv2.CAP_PROP_FPS, self.fps)

        frame_delay = 1 / self.fps

        while self._is_running:
            ret, frame = await self._loop.run_in_executor(None, self._capture.read)
            if not ret:
                raise RuntimeError("Failed to read frame from webcam")

            # Convert BGR to RGB
            frame_rgb = await self._loop.run_in_executor(None, cv2.cvtColor, frame, cv2.COLOR_BGR2RGB)

            height, width = frame_rgb.shape[:2]
            video_frame = VideoFrame(
                width=width,
                height=height,
                buffer_type="rgb24",
                data=frame_rgb,
                timestamp_us=int(time.time() * 1_000_000),
            )
            yield video_frame
            await asyncio.sleep(frame_delay)

    @override
    async def _stop_source(self):
        """Releases the webcam capture and stops the node."""
        if self._capture:
            self._capture.release()
