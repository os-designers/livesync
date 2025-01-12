import time
from typing import Callable

import numpy as np
import pytest
from numpy.typing import NDArray

from livesync.nodes.presets import FrameRateNode
from livesync.frames.video_frame import VideoFrame


class TestFrameRateNode:
    @pytest.fixture
    def sample_video_data(self) -> NDArray[np.uint8]:
        """Create sample video data for testing."""
        return np.full((1080, 1920, 3), [255, 0, 0], dtype=np.uint8)

    @pytest.fixture
    def create_frame(self, sample_video_data: NDArray[np.uint8]):
        """Helper function to create VideoFrame with specific timestamp."""

        def _create(timestamp_us: int) -> VideoFrame:
            return VideoFrame(
                width=1920, height=1080, buffer_type="rgb24", data=sample_video_data, timestamp_us=timestamp_us
            )

        return _create

    @pytest.mark.asyncio
    async def test_frame_rate_node_initialization(self):
        """Test proper initialization of FrameRateNode."""
        node = FrameRateNode(target_fps=30)
        assert node.target_fps == 30
        assert node._frame_delay_us == 33333  # ~33.33ms in microseconds
        assert node._last_frame_time_us == 0
        assert node._last_frame is None

    @pytest.mark.asyncio
    async def test_first_frame_always_passes(self, create_frame: Callable[[int], VideoFrame]):
        """Test that the first frame always passes through."""
        node = FrameRateNode(target_fps=30)
        frame = create_frame(int(time.time() * 1_000_000))
        result = await node.process_frame(frame)

        assert result == frame
        assert node._last_frame_time_us == frame.timestamp_us
        assert node._last_frame == frame

    @pytest.mark.asyncio
    async def test_frame_drop_when_too_close(self, create_frame: Callable[[int], VideoFrame]):
        """Test that frames are dropped when they arrive too quickly."""
        node = FrameRateNode(target_fps=30)

        # First frame
        base_time = int(time.time() * 1_000_000)
        frame1 = create_frame(base_time)
        await node.process_frame(frame1)

        # Second frame arrives too soon (15000 microseconds later, < 33333)
        frame2 = create_frame(base_time + 15000)
        result = await node.process_frame(frame2)

        assert result is None
        assert node._last_frame_time_us == base_time
        assert node._last_frame == frame1

    @pytest.mark.asyncio
    async def test_frame_passes_after_delay(self, create_frame: Callable[[int], VideoFrame]):
        """Test that frames pass through after sufficient delay."""
        node = FrameRateNode(target_fps=30)

        # First frame
        base_time = int(time.time() * 1_000_000)
        frame1 = create_frame(base_time)
        await node.process_frame(frame1)

        # Second frame arrives after sufficient delay (40000 microseconds > 33333)
        frame2 = create_frame(base_time + 40000)
        result = await node.process_frame(frame2)

        assert result == frame2
        assert node._last_frame_time_us == base_time + 40000
        assert node._last_frame == frame2

    @pytest.mark.asyncio
    async def test_different_target_fps(self, create_frame: Callable[[int], VideoFrame]):
        """Test behavior with different target FPS."""
        node = FrameRateNode(target_fps=60)
        assert node._frame_delay_us == 16666  # ~16.67ms in microseconds

        base_time = int(time.time() * 1_000_000)
        frame1 = create_frame(base_time)
        await node.process_frame(frame1)

        # Frame arriving after 20ms should pass at 60 FPS
        frame2 = create_frame(base_time + 20000)
        result = await node.process_frame(frame2)

        assert result == frame2

    @pytest.mark.asyncio
    async def test_sequence_of_frames(self, create_frame: Callable[[int], VideoFrame]):
        """Test processing a sequence of frames."""
        node = FrameRateNode(target_fps=30)
        base_time = int(time.time() * 1_000_000)

        time_offsets = [0, 20000, 40000, 50000, 80000]
        expected_passes = [True, False, True, False, True]

        for offset, should_pass in zip(time_offsets, expected_passes):
            frame = create_frame(base_time + offset)
            result = await node.process_frame(frame)

            if should_pass:
                assert result == frame
            else:
                assert result is None
