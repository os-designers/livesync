import asyncio
from unittest.mock import AsyncMock

import numpy as np
import pytest
from livekit import rtc  # type: ignore
from numpy.typing import NDArray

from livesync.frames.video_frame import VideoFrame
from livesync.nodes.presets.livekit import LiveKitVideoSourceNode
from livesync.nodes.presets.livekit.livekit_video_source_node import BUFFER_TYPE_MAP


class MockVideoFrame:
    """Mock for LiveKit VideoFrame."""

    def __init__(self, width: int, height: int, data: bytes):
        self.width = width
        self.height = height
        self.data = data
        self.type = rtc.VideoBufferType.RGB24


class MockFrameEvent:
    """Mock for LiveKit FrameEvent."""

    def __init__(self, frame: MockVideoFrame, timestamp_us: int):
        self.frame = frame
        self.timestamp_us = timestamp_us


class MockVideoStream:
    """Mock for LiveKit VideoStream."""

    def __init__(self, frame_events: list[MockFrameEvent]):
        self.frame_events = frame_events
        self.aclose = AsyncMock()
        self._iterator = self._create_iterator()

    async def _create_iterator(self):
        for event in self.frame_events:
            yield event

    def __aiter__(self):
        return self._iterator


class TestLiveKitVideoSourceNode:
    @pytest.fixture
    def sample_video_data(self) -> NDArray[np.uint8]:
        """Create sample video data for testing."""
        return np.full((720, 1280, 3), [255, 0, 0], dtype=np.uint8)

    @pytest.fixture
    def mock_video_stream(self, sample_video_data: NDArray[np.uint8]):
        """Create a mock video stream with predefined frame events."""
        frame_events: list[MockFrameEvent] = []
        base_time = 1000000

        # Create 3 frame events
        for i in range(3):
            frame = MockVideoFrame(width=1280, height=720, data=sample_video_data.tobytes())
            event = MockFrameEvent(frame=frame, timestamp_us=base_time + (i * 33333))  # ~30fps
            frame_events.append(event)

        return MockVideoStream(frame_events)

    @pytest.mark.asyncio
    async def test_source_frames_output(self, mock_video_stream: MockVideoStream, sample_video_data: NDArray[np.uint8]):
        """Test that source frames are correctly converted and yielded."""
        node = LiveKitVideoSourceNode(livekit_stream=mock_video_stream)  # type: ignore

        frames_received: list[VideoFrame] = []
        async for frame in node._source_frames():
            frames_received.append(frame)
            if len(frames_received) >= 3:  # Collect 3 frames
                break

        assert len(frames_received) == 3

        # Verify first frame properties
        first_frame = frames_received[0]
        assert isinstance(first_frame, VideoFrame)
        assert first_frame.width == 1280
        assert first_frame.height == 720
        assert first_frame.buffer_type == "rgb24"
        assert np.array_equal(first_frame.data, sample_video_data)
        assert first_frame.timestamp_us == 1000000

    @pytest.mark.asyncio
    async def test_stop_source(self, mock_video_stream: MockVideoStream):
        """Test that stop_source properly closes the LiveKit stream."""
        node = LiveKitVideoSourceNode(livekit_stream=mock_video_stream)  # type: ignore

        await node._stop_source()
        mock_video_stream.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_source_node_lifecycle(self, mock_video_stream: MockVideoStream):
        """Test the complete lifecycle of the LiveKit source node."""
        node = LiveKitVideoSourceNode(livekit_stream=mock_video_stream)  # type: ignore

        # Test startup
        await node.start()
        await asyncio.sleep(0.1)  # Give some time for processing

        assert node._source_task is not None
        assert node._is_running

        # Test shutdown
        await node.stop()
        assert not node._is_running
        assert node._source_task is None
        mock_video_stream.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_buffer_type_mapping(self):
        """Test that different LiveKit buffer types are correctly mapped."""
        for lk_type, expected_type in [
            (rtc.VideoBufferType.RGB24, "rgb24"),
            (rtc.VideoBufferType.RGBA, "rgba"),
            (rtc.VideoBufferType.I420, "i420"),
            # Add more buffer type tests as needed
        ]:
            assert expected_type == BUFFER_TYPE_MAP[lk_type]
