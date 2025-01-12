from unittest.mock import Mock

import numpy as np
import pytest
from livekit import rtc  # type: ignore
from numpy.typing import NDArray

from livesync.frames.video_frame import VideoFrame
from livesync.nodes.presets.livekit import LiveKitVideoPublisherNode
from livesync.nodes.presets.livekit.livekit_video_publisher_node import BUFFER_TYPE_MAP


class TestLiveKitVideoPublisherNode:
    @pytest.fixture
    def mock_livekit_source(self):
        """Create a mock LiveKit video source."""
        source = Mock(spec=rtc.VideoSource)
        source.capture_frame = Mock()
        return source

    @pytest.fixture
    def sample_video_frame(self) -> VideoFrame:
        """Create a sample video frame for testing."""
        video_data: NDArray[np.uint8] = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

        return VideoFrame(width=1280, height=720, buffer_type="rgb24", data=video_data, timestamp_us=1000000)

    @pytest.mark.asyncio
    async def test_process_frame(self, mock_livekit_source: Mock, sample_video_frame: VideoFrame):
        """Test that video frames are correctly processed and sent to LiveKit."""
        node = LiveKitVideoPublisherNode(livekit_source=mock_livekit_source)

        # Process the frame
        await node.process_frame(sample_video_frame)

        # Verify that capture_frame was called
        mock_livekit_source.capture_frame.assert_called_once()

        # Verify the LiveKit frame properties
        called_frame = mock_livekit_source.capture_frame.call_args[0][0]
        assert isinstance(called_frame, rtc.VideoFrame)
        assert called_frame.width == sample_video_frame.width
        assert called_frame.height == sample_video_frame.height
        assert called_frame.type == BUFFER_TYPE_MAP[sample_video_frame.buffer_type]
        assert bytes(called_frame.data) == sample_video_frame.data.tobytes()

    @pytest.mark.asyncio
    async def test_multiple_frames(self, mock_livekit_source: Mock):
        """Test processing multiple video frames."""
        node = LiveKitVideoPublisherNode(livekit_source=mock_livekit_source)

        # Create multiple frames with different data
        frames: list[VideoFrame] = []
        for i in range(3):
            video_data: NDArray[np.uint8] = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
            frame = VideoFrame(
                width=1280, height=720, buffer_type="rgb24", data=video_data, timestamp_us=1000000 + i * 1000
            )
            frames.append(frame)

        # Process all frames
        for frame in frames:
            await node.process_frame(frame)

        # Verify number of calls
        assert mock_livekit_source.capture_frame.call_count == len(frames)

        # Verify each frame was processed correctly
        for i, call_args in enumerate(mock_livekit_source.capture_frame.call_args_list):
            lk_frame = call_args[0][0]
            assert isinstance(lk_frame, rtc.VideoFrame)
            assert lk_frame.width == frames[i].width
            assert lk_frame.height == frames[i].height
            assert lk_frame.type == BUFFER_TYPE_MAP[frames[i].buffer_type]
            assert bytes(lk_frame.data) == frames[i].data.tobytes()

    @pytest.mark.asyncio
    async def test_different_buffer_types(self, mock_livekit_source: Mock):
        """Test processing frames with different buffer types."""
        node = LiveKitVideoPublisherNode(livekit_source=mock_livekit_source)

        # Create RGBA test data
        video_data: NDArray[np.uint8] = np.random.randint(0, 255, (720, 1280, 4), dtype=np.uint8)

        frame = VideoFrame(width=1280, height=720, buffer_type="rgba", data=video_data, timestamp_us=1000000)

        # Process the frame
        await node.process_frame(frame)

        # Verify the frame properties
        called_frame = mock_livekit_source.capture_frame.call_args[0][0]
        assert isinstance(called_frame, rtc.VideoFrame)
        assert called_frame.width == frame.width
        assert called_frame.height == frame.height
        assert called_frame.type == BUFFER_TYPE_MAP[frame.buffer_type]
        assert bytes(called_frame.data) == frame.data.tobytes()

    @pytest.mark.asyncio
    async def test_different_resolutions(self, mock_livekit_source: Mock):
        """Test processing frames with different resolutions."""
        node = LiveKitVideoPublisherNode(livekit_source=mock_livekit_source)

        resolutions = [(1920, 1080), (1280, 720), (854, 480)]
        for width, height in resolutions:
            video_data: NDArray[np.uint8] = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

            frame = VideoFrame(width=width, height=height, buffer_type="rgb24", data=video_data, timestamp_us=1000000)

            # Process the frame
            await node.process_frame(frame)

            # Verify the frame properties
            called_frame = mock_livekit_source.capture_frame.call_args[0][0]
            assert isinstance(called_frame, rtc.VideoFrame)
            assert called_frame.width == width
            assert called_frame.height == height
            assert called_frame.type == BUFFER_TYPE_MAP[frame.buffer_type]
            assert bytes(called_frame.data) == frame.data.tobytes()
