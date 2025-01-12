import asyncio
from typing_extensions import override

import pytest

from tests.conftest import MockFrame, MockCallbackHandler
from livesync.nodes.base_node import BaseNode
from livesync.frames.base_frame import BaseFrame


class MockNode(BaseNode):
    """Mock node implementation for testing base functionality."""

    @override
    def __post_init__(self):
        super().__post_init__()
        self.type = "mock"

    @override
    async def _before_run(self):
        pass

    @override
    async def _before_cleanup(self):
        pass

    @override
    async def process_frame(self, frame: BaseFrame) -> BaseFrame | None:
        return frame


class TestBaseNode:
    @pytest.mark.asyncio
    async def test_node_initialization(self):
        """Test basic node initialization."""
        node = MockNode()
        assert node.id is not None
        assert not node.concurrent
        assert node.callback_handler is None
        assert node.type == "mock"

    @pytest.mark.asyncio
    async def test_frame_processing_with_callbacks(self, mock_frame: MockFrame, callback_handler: MockCallbackHandler):
        """Test frame processing with callback handlers."""
        node = MockNode(callback_handler=callback_handler)
        await node.start()

        await node._input_queue.put(("test_source", mock_frame))
        await asyncio.sleep(0.1)  # Allow processing to complete

        callback_handler.on_received.assert_called_once()
        callback_handler.on_processed.assert_called_once()

        await node.stop()

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, mock_frame: MockFrame):
        """Test concurrent frame processing."""
        node = MockNode(concurrent=True)
        await node.start()

        # Send multiple frames
        for _ in range(3):
            await node._input_queue.put(("test_source", mock_frame))

        await asyncio.sleep(0.1)  # Allow processing to complete
        assert len(node._tasks) > 0

        await node.stop()
        assert len(node._tasks) == 0

    @pytest.mark.asyncio
    async def test_node_cleanup(self, mock_frame: MockFrame):
        """Test proper cleanup of node resources."""
        node = MockNode()
        await node.start()

        # Add some frames to the queue
        await node._input_queue.put(("test_source", mock_frame))
        await node._input_queue.put(("test_source", mock_frame))

        await node.stop()
        assert not node._is_running
        assert node._tasks == []
        assert node._input_queue.empty()
