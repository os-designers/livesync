import time
import asyncio
from typing import AsyncIterator
from fractions import Fraction

import cv2

from ..._utils.logs import logger
from ..core.input_layer import InputLayer
from ...frames.video_frame import VideoFrame


class WebcamInput(InputLayer[VideoFrame]):
    """A layer that captures frames from a webcam device.

    Parameters
    ----------
    device_id : int, default=0
        The ID of the webcam device to capture from
    fps : int, default=30
        Target frames per second for capture
    name : str | None, default=None
        The name of the layer

    Raises
    ------
    RuntimeError
        If webcam device cannot be opened
    """

    def __init__(self, device_id: int = 0, fps: int = 30, name: str | None = None):
        super().__init__(dtype=VideoFrame, name=name)
        self.device_id = device_id
        self.fps = fps
        self.time_base = Fraction(1, fps)

        self._capture = cv2.VideoCapture(self.device_id)
        if not self._capture.isOpened():
            raise RuntimeError(f"Failed to open webcam (device_id: {self.device_id})")

        # Set camera properties
        self._capture.set(cv2.CAP_PROP_FPS, self.fps)
        # Verify if the requested FPS was actually set
        actual_fps = self._capture.get(cv2.CAP_PROP_FPS)
        if abs(actual_fps - self.fps) > 1:  # Allow 1 FPS difference
            logger.warning(f"Requested FPS {self.fps} but camera reports {actual_fps}")
            self.fps = int(actual_fps)
            self.time_base = Fraction(1, int(actual_fps))

        self._frame_interval = 1 / self.fps

    async def aiter(self) -> AsyncIterator[VideoFrame]:
        """Captures frames from the webcam.

        Yields
        ------
        VideoFrame
            Video frames captured from the webcam at specified FPS

        Raises
        ------
        RuntimeError
            If frame capture fails
        """
        start_time = time.time()
        last_capture_time = start_time

        while True:
            try:
                # Calculate the target time for the next frame
                next_frame_time = last_capture_time + self._frame_interval

                # Wait until it's time to capture the next frame
                current_time = time.time()
                if current_time < next_frame_time:
                    await asyncio.sleep(next_frame_time - current_time)

                # Capture frame
                ret, frame_bgr_data = self._capture.read()
                if not ret:
                    raise RuntimeError("Failed to read frame from webcam")

                current_time = time.time()
                last_capture_time = current_time

                pts = int((current_time - start_time) / self.time_base)

                # Convert BGR to RGB
                frame_data = cv2.cvtColor(frame_bgr_data, cv2.COLOR_BGR2RGB)

                height, width = frame_data.shape[:2]
                video_frame = VideoFrame(
                    data=frame_data,
                    width=width,
                    height=height,
                    buffer_type="rgb24",
                    pts=pts,
                    time_base=self.time_base,
                )
                yield video_frame
            except Exception as e:
                logger.error(f"Error capturing frame from webcam: {e}")

    async def cleanup(self) -> None:
        """Releases the webcam capture."""
        if self._capture:
            self._capture.release()
            logger.debug(f"Webcam (device_id={self.device_id}) released.")
