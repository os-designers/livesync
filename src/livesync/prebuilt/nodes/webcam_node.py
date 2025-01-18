import time
from logging import getLogger

import cv2

from ...core.nodes import Node
from ...core.fields import Field
from ...core.frames import VideoFrame

logger = getLogger(__name__)


class WebcamNode(Node):
    """A node that captures frames from a webcam device."""

    device_id: int = Field(default=0, description="The device ID of the webcam")
    fps: int = Field(default=30, description="The frame rate of the webcam")

    def bootstrap(self) -> None:
        """Bootstraps the webcam node."""
        self._capture = cv2.VideoCapture(self.device_id)
        if not self._capture.isOpened():
            raise RuntimeError(f"Failed to open webcam (device_id: {self.device_id})")

        self._capture.set(cv2.CAP_PROP_FPS, self.fps)
        self._frame_interval = 1 / self.fps
        self._last_capture_time: float | None = None

    def step(self) -> VideoFrame:
        """Captures frames from the webcam and puts them into the queue."""
        ret, frame_bgr_data = self._capture.read()
        if not ret:
            raise RuntimeError("Failed to read frame from webcam")

        current_time = time.time()

        if self._last_capture_time:
            time_diff = current_time - self._last_capture_time
            if time_diff < self._frame_interval:
                time.sleep(self._frame_interval - time_diff)
                current_time = time.time()

        self._last_capture_time = current_time

        # Convert BGR to RGB
        frame_data = cv2.cvtColor(frame_bgr_data, cv2.COLOR_BGR2RGB)

        height, width = frame_data.shape[:2]
        video_frame = VideoFrame(
            data=frame_data,
            timestamp_us=int(current_time * 1_000_000),
            width=width,
            height=height,
            buffer_type="rgb24",
        )
        return video_frame

    def shutdown(self) -> None:
        """Releases the webcam capture and stops the node."""
        if self._capture:
            self._capture.release()
            logger.info(f"Webcam (device_id={self.device_id}) released.")
