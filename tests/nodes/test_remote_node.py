# # TODO: Add tests for RemoteNode

# import asyncio
# from dataclasses import dataclass
# from typing_extensions import override

# import pytest
# import numpy as np
# from numpy.typing import NDArray

# from livesync.nodes import RemoteNode, NodeCallbackHandler
# from livesync.frames import BaseFrame, AudioFrame


# @dataclass
# class MockRemoteNode(RemoteNode):
#     """Mock implementation of RemoteNode for testing."""

#     is_connected: bool = False
#     connect_called: bool = False
#     disconnect_called: bool = False

#     @override
#     async def _connect(self):
#         """Mock connection implementation."""
#         self.connect_called = True
#         self.is_connected = True

#     @override
#     async def _disconnect(self):
#         """Mock disconnection implementation."""
#         self.disconnect_called = True
#         self.is_connected = False

#     @override
#     async def process_frame(self, frame: BaseFrame) -> BaseFrame:
#         """Simple pass-through frame processing."""
#         return frame


# class TestRemoteNode:
#     @pytest.fixture
#     def remote_endpoints(self) -> list[str]:
#         """Provide test endpoints."""
#         return ["ws://localhost:8080", "ws://localhost:8081"]

#     @pytest.fixture
#     def remote_node(self, remote_endpoints: list[str]) -> MockRemoteNode:
#         """Create a MockRemoteNode instance."""
#         return MockRemoteNode(endpoints=remote_endpoints)

#     @pytest.fixture
#     def remote_node_with_callback(
#         self, remote_endpoints: list[str], callback_handler: NodeCallbackHandler
#     ) -> MockRemoteNode:
#         """Create a MockRemoteNode instance with callback handler."""
#         return MockRemoteNode(endpoints=remote_endpoints, callback_handler=callback_handler)

#     @pytest.fixture
#     def audio_frame(self, sample_audio_data: NDArray[np.float32]) -> AudioFrame:
#         """Create a sample audio frame for testing."""
#         return AudioFrame(
#             data=sample_audio_data,
#             timestamp_us=1000000,
#             sample_rate=44100,
#             num_channels=2,
#             sample_format="float32",
#             channel_layout="stereo",
#         )

#     @pytest.mark.asyncio
#     async def test_remote_node_initialization(self, remote_endpoints: list[str]):
#         """Test proper initialization of RemoteNode."""
#         node = MockRemoteNode(endpoints=remote_endpoints)
#         assert node.endpoints == remote_endpoints
#         assert not node.is_connected
#         assert not node.connect_called
#         assert not node.disconnect_called

#     @pytest.mark.asyncio
#     async def test_remote_node_connect_on_start(self, remote_node: MockRemoteNode):
#         """Test that connection is established when node starts."""
#         await remote_node.start()
#         assert remote_node.connect_called
#         assert remote_node.is_connected
#         await remote_node.stop()

#     @pytest.mark.asyncio
#     async def test_remote_node_disconnect_on_stop(self, remote_node: MockRemoteNode):
#         """Test that disconnection occurs when node stops."""
#         await remote_node.start()
#         await remote_node.stop()
#         assert remote_node.disconnect_called
#         assert not remote_node.is_connected

#     @pytest.mark.asyncio
#     async def test_remote_node_frame_processing(
#         self, remote_node_with_callback: MockRemoteNode, audio_frame: AudioFrame
#     ):
#         """Test frame processing through the remote node."""
#         await remote_node_with_callback.start()

#         # Send frame through the node
#         await remote_node_with_callback._input_queue.put(("test_source", audio_frame))

#         # Wait a bit for processing
#         await asyncio.sleep(0.1)

#         # Verify callback handler was called
#         # assert remote_node_with_callback.callback_handler.on_frame_received.called
#         # assert remote_node_with_callback.callback_handler.on_frame_processed.called

#         await remote_node_with_callback.stop()

#     @pytest.mark.asyncio
#     async def test_remote_node_cleanup_on_error(self, remote_node: MockRemoteNode):
#         """Test proper cleanup when an error occurs."""
#         await remote_node.start()

#         # Simulate an error by cancelling the node's tasks
#         for task in remote_node._tasks:
#             task.cancel()

#         await remote_node.stop()

#         assert remote_node.disconnect_called
#         assert not remote_node.is_connected
#         assert not remote_node._is_running
#         assert len(remote_node._tasks) == 0

#     @pytest.mark.asyncio
#     async def test_remote_node_multiple_endpoints(self):
#         """Test RemoteNode with multiple endpoints."""
#         endpoints = ["ws://localhost:8080", "ws://localhost:8081", "ws://localhost:8082"]
#         node = MockRemoteNode(endpoints=endpoints)

#         await node.start()
#         assert node.connect_called
#         assert node.is_connected
#         assert len(node.endpoints) == 3

#         await node.stop()
#         assert node.disconnect_called
#         assert not node.is_connected

#     @pytest.mark.asyncio
#     async def test_remote_node_empty_endpoints(self):
#         """Test RemoteNode behavior with empty endpoints list."""
#         node = MockRemoteNode(endpoints=[])

#         await node.start()
#         assert node.connect_called
#         assert node.is_connected
#         assert len(node.endpoints) == 0

#         await node.stop()
#         assert node.disconnect_called
#         assert not node.is_connected
