import time
import asyncio
from typing import AsyncIterator
from typing_extensions import override

import numpy as np
import pytest
from numpy.typing import NDArray

from livesync.nodes.source_node import SourceNode
from livesync.frames.video_frame import VideoFrame


class MockSourceNode(SourceNode):
    """Mock source node for testing."""

    def __init__(self, sample_video_data: NDArray[np.uint8]):
        super().__init__()
        self.stop_capture_called = False
        self.frames_captured = 0
        self.sample_video_data = sample_video_data

    @override
    async def _source_frames(self) -> AsyncIterator[VideoFrame]:  # type: ignore[override]
        video_frame = VideoFrame(
            width=1920,
            height=1080,
            buffer_type="rgb24",
            data=self.sample_video_data,
            timestamp_us=int(time.time() * 1_000_000),
        )
        while self._is_running:
            self.frames_captured += 1
            yield video_frame
            await asyncio.sleep(0.1)

    @override
    async def _stop_source(self):
        self.stop_capture_called = True


class TestSourceNode:
    @pytest.mark.asyncio
    async def test_source_node_lifecycle(self, sample_video_data: NDArray[np.uint8]):
        """Test the complete lifecycle of a source node."""
        node = MockSourceNode(sample_video_data=sample_video_data)

        # Test startup
        await node.start()
        await asyncio.sleep(0.2)

        assert node._source_task is not None
        assert node._is_running
        assert node.frames_captured > 0

        # Test shutdown
        await node.stop()
        assert node.stop_capture_called
        assert not node._is_running
        assert node._source_task is None

    @pytest.mark.asyncio
    async def test_source_node_cleanup(self, sample_video_data: NDArray[np.uint8]):
        """Test proper cleanup of source node resources."""
        node = MockSourceNode(sample_video_data=sample_video_data)
        await node.start()
        await asyncio.sleep(0.1)

        # Force cancel the capture task
        if node._source_task:
            node._source_task.cancel()

        await node.stop()
        assert node.stop_capture_called
        assert not node._is_running
        assert node._source_task is None
