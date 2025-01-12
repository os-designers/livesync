import time
import asyncio
from unittest.mock import patch

import cv2
import numpy as np
import pytest
from numpy.typing import NDArray

from livesync import VideoFrame
from livesync.nodes.presets import WebcamNode


class MockVideoCapture:
    """Mock implementation of cv2.VideoCapture."""

    def __init__(self, is_opened: bool = True):
        self.is_opened = is_opened
        self.released = False
        # Create a test frame (100x100 red image)
        self.test_frame: NDArray[np.uint8] = np.full((100, 100, 3), [255, 0, 0], dtype=np.uint8)
        self.fps = 30

    def isOpened(self) -> bool:
        return self.is_opened

    def read(self):
        if not self.is_opened:
            return False, None
        return True, self.test_frame.copy()

    def release(self):
        self.released = True

    def set(self, prop_id: int, value: int):
        if prop_id == cv2.CAP_PROP_FPS:
            self.fps = value


class TestWebcamNode:
    @pytest.mark.asyncio
    async def test_webcam_node_successful_start(self):
        """Test successful webcam initialization and frame capture."""
        with patch("cv2.VideoCapture", return_value=MockVideoCapture()) as _:
            node = WebcamNode(device_id=0, fps=30)

            # Start the node
            await node.start()
            await asyncio.sleep(1)  # Wait for frame capture

            # Verify
            assert node._is_running
            assert node._source_task is not None

            # Cleanup
            await node.stop()
            assert not node._is_running
            assert node._source_task is None

    @pytest.mark.asyncio
    async def test_webcam_node_failed_open(self):
        """Test scenario when webcam fails to open."""
        with patch("cv2.VideoCapture", return_value=MockVideoCapture(is_opened=False)):
            node = WebcamNode(device_id=0)

            # Start the node and wait for the error to propagate
            with pytest.raises(RuntimeError, match="Failed to open webcam"):
                await node.start()
                # Wait for the source task to actually start and fail
                while node._source_task is None:
                    await asyncio.sleep(0.1)
                await node._source_task

    @pytest.mark.asyncio
    async def test_webcam_node_cleanup(self):
        """Test proper cleanup of webcam node resources."""
        mock_capture = MockVideoCapture()
        with patch("cv2.VideoCapture", return_value=mock_capture):
            node = WebcamNode(device_id=0)

            await node.start()
            await asyncio.sleep(0.1)
            await node.stop()

            assert mock_capture.released
            assert not node._is_running
            assert node._source_task is None

    @pytest.mark.asyncio
    async def test_webcam_node_fps_setting(self):
        """Test FPS configuration of the webcam."""
        mock_capture = MockVideoCapture()
        with patch("cv2.VideoCapture", return_value=mock_capture):
            test_fps = 60
            node = WebcamNode(device_id=0, fps=test_fps)

            await node.start()
            await asyncio.sleep(0.1)

            assert mock_capture.fps == test_fps
            await node.stop()

    @pytest.mark.asyncio
    async def test_frame_format(self):
        """Verify the format of captured frames."""
        mock_capture = MockVideoCapture()
        with patch("cv2.VideoCapture", return_value=mock_capture):
            node = WebcamNode(device_id=0)

            await node.start()
            await asyncio.sleep(0.1)

            # Get frame from queue
            _, frame = await node._input_queue.get()

            # Verify frame properties
            assert isinstance(frame, VideoFrame)
            assert frame.width == 100
            assert frame.height == 100
            assert frame.buffer_type == "rgb24"
            assert isinstance(frame.timestamp_us, int)
            assert frame.timestamp_us <= int(time.time() * 1_000_000)

            await node.stop()
