import numpy as np
import pytest
from numpy.typing import NDArray

from livesync import VideoFrame
from livesync.nodes.presets import ResolutionNode


class TestResolutionNode:
    @pytest.fixture
    def sample_frame(self) -> VideoFrame:
        """Create a sample video frame for testing."""
        # Create a test frame (800x600 red image)
        test_data: NDArray[np.uint8] = np.full((600, 800, 3), [255, 0, 0], dtype=np.uint8)
        return VideoFrame(data=test_data, timestamp_us=1000000, width=800, height=600, buffer_type="rgb24")

    @pytest.mark.asyncio
    async def test_resolution_node_downscale(self, sample_frame: VideoFrame):
        """Test downscaling a frame while maintaining aspect ratio."""
        node = ResolutionNode(target_height=480)
        result = await node.process_frame(sample_frame)

        # Verify dimensions and aspect ratio
        assert result.height == 480
        assert result.width == 640  # 800 * (480/600) = 640
        assert abs(result.width / result.height - sample_frame.width / sample_frame.height) < 0.01
        assert result.buffer_type == "rgb24"
        assert result.timestamp_us == sample_frame.timestamp_us

    @pytest.mark.asyncio
    async def test_resolution_node_upscale(self, sample_frame: VideoFrame):
        """Test upscaling a frame while maintaining aspect ratio."""
        node = ResolutionNode(target_height=720)
        result = await node.process_frame(sample_frame)

        # Verify dimensions and aspect ratio
        assert result.height == 720
        assert result.width == 960  # 800 * (720/600) = 960
        assert abs(result.width / result.height - sample_frame.width / sample_frame.height) < 0.01
        assert result.buffer_type == "rgb24"
        assert result.timestamp_us == sample_frame.timestamp_us

    @pytest.mark.asyncio
    async def test_resolution_node_same_size(self, sample_frame: VideoFrame):
        """Test when target height equals input height."""
        node = ResolutionNode(target_height=600)
        result = await node.process_frame(sample_frame)

        # Verify dimensions remain the same
        assert result.height == sample_frame.height
        assert result.width == sample_frame.width
        assert result.buffer_type == "rgb24"
        assert result.timestamp_us == sample_frame.timestamp_us

    @pytest.mark.asyncio
    async def test_resolution_node_preserves_data(self, sample_frame: VideoFrame):
        """Test that the frame data is properly preserved after resizing."""
        node = ResolutionNode(target_height=480)
        result = await node.process_frame(sample_frame)

        # Verify the resized frame still contains valid image data
        assert isinstance(result.data, np.ndarray)
        assert result.data.shape == (480, 640, 3)
        assert result.data.dtype == np.uint8
