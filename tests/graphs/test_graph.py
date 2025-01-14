from __future__ import annotations

import asyncio
from unittest.mock import Mock, AsyncMock

import pytest

from livesync.graphs import Graph
from livesync.nodes.base_node import BaseNode


@pytest.fixture
def mock_node() -> Mock:
    """Create a mock node for testing."""
    node = Mock(spec=BaseNode)
    node.id = "test_node"
    node.start = AsyncMock()
    node.stop = AsyncMock()
    return node


class TestBaseGraph:
    def test_graph_initialization(self) -> None:
        graph = Graph()
        assert not graph.is_running
        assert len(graph.nodes) == 0

    def test_add_node(self, mock_node: Mock) -> None:
        graph = Graph()
        graph.add_node(mock_node)
        assert mock_node in graph.nodes
        assert mock_node.id in graph._edges

    def test_add_duplicate_node(self, mock_node: Mock) -> None:
        graph = Graph()
        graph.add_node(mock_node)
        with pytest.raises(ValueError, match="already exists"):
            graph.add_node(mock_node)

    def test_add_edge(self, mock_node: Mock) -> None:
        graph = Graph()
        source = mock_node
        target = Mock(spec=BaseNode)
        target.id = "target_node"

        graph.add_node(source)
        graph.add_node(target)
        graph.add_edge(source, target)

        assert target in graph.get_successors(source)

    @pytest.mark.parametrize(
        "scenario,expected_error",
        [
            ("self_loop", "Self-loops are not allowed"),
            ("duplicate_edge", "Edge already exists"),
            ("missing_source", "Source node not found"),
            ("missing_target", "Target node not found"),
        ],
    )
    def test_add_edge_validation(self, mock_node: Mock, scenario: str, expected_error: str) -> None:
        graph = Graph()
        source = mock_node
        target = Mock(spec=BaseNode)
        target.id = "target_node"

        if scenario != "missing_source":
            graph.add_node(source)
        if scenario != "missing_target":
            graph.add_node(target)

        if scenario == "self_loop":
            with pytest.raises(ValueError, match=expected_error):
                graph.add_edge(source, source)
        elif scenario == "duplicate_edge":
            graph.add_edge(source, target)
            with pytest.raises(ValueError, match=expected_error):
                graph.add_edge(source, target)
        else:
            with pytest.raises(ValueError, match=expected_error):
                graph.add_edge(source, target)

    @pytest.mark.asyncio
    async def test_graph_start(self, mock_node: Mock) -> None:
        graph = Graph()
        graph.add_node(mock_node)

        await graph.start()
        await asyncio.sleep(0)

        assert graph.is_running
        mock_node.start.assert_called_once()

        await graph.stop()

    @pytest.mark.asyncio
    async def test_graph_start_error_handling(self, mock_node: Mock) -> None:
        graph = Graph()
        graph.add_node(mock_node)

        # Setup mock to raise an exception
        mock_node.start.side_effect = Exception("Test error")

        with pytest.raises(Exception, match="Test error"):
            await graph.start()

        assert not graph.is_running
        mock_node.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_graph_already_running(self, mock_node: Mock) -> None:
        graph = Graph()
        graph.add_node(mock_node)

        await graph.start()
        await asyncio.sleep(0)
        with pytest.raises(RuntimeError, match="Graph is already running"):
            await graph.start()

        await graph.stop()

    @pytest.mark.asyncio
    async def test_graph_cleanup_on_error(self, mock_node: Mock) -> None:
        graph = Graph()
        graph.add_node(mock_node)

        # Setup mock to raise an exception during stop
        mock_node.stop.side_effect = Exception("Stop error")

        await graph.start()
        await asyncio.sleep(0.1)
        await graph.stop()  # Should not raise exception

        assert not graph.is_running
        mock_node.stop.assert_called_once()

    def test_remove_node(self, mock_node: Mock) -> None:
        graph = Graph()
        target = Mock(spec=BaseNode)
        target.id = "target_node"

        # Add nodes and create an edge
        graph.add_node(mock_node)
        graph.add_node(target)
        graph.add_edge(mock_node, target)

        # Remove node and verify
        graph.remove_node(target)
        assert target not in graph.nodes
        assert target not in graph.get_successors(mock_node)

    def test_remove_nonexistent_node(self, mock_node: Mock) -> None:
        graph = Graph()
        with pytest.raises(ValueError, match="not found in graph"):
            graph.remove_node(mock_node)

    def test_get_node_by_id(self, mock_node: Mock) -> None:
        graph = Graph()
        graph.add_node(mock_node)

        # Test successful retrieval
        found_node = graph.get_node_by_id("test_node")
        assert found_node == mock_node

        # Test non-existent node
        not_found = graph.get_node_by_id("nonexistent")
        assert not_found is None


@pytest.mark.asyncio
class TestNodeReplacement:
    async def test_replace_node_when_not_running(self, mock_node: Mock) -> None:
        """Test node replacement when graph is not running."""
        graph = Graph()
        old_node = mock_node
        new_node = Mock(spec=BaseNode)
        new_node.id = "new_node"

        graph.add_node(old_node)
        await graph.replace_node(old_node, new_node)

        assert new_node in graph.nodes
        assert old_node not in graph.nodes
        # Verify old node was not stopped since graph wasn't running
        old_node.stop.assert_not_called()

    async def test_replace_node_preserves_connections(self, mock_node: Mock) -> None:
        """Test that node replacement preserves graph connections."""
        graph = Graph()

        # Setup nodes
        old_node = mock_node
        new_node = Mock(spec=BaseNode)
        new_node.id = "new_node"
        predecessor = Mock(spec=BaseNode)
        predecessor.id = "pred"
        successor = Mock(spec=BaseNode)
        successor.id = "succ"

        # Build graph
        graph.add_node(predecessor)
        graph.add_node(old_node)
        graph.add_node(successor)
        graph.add_edge(predecessor, old_node)
        graph.add_edge(old_node, successor)

        # Start graph and replace node
        await graph.start()
        await graph.replace_node(old_node, new_node)

        # Verify connections are preserved
        assert new_node in graph.get_successors(predecessor)
        assert successor in graph.get_successors(new_node)

        # Verify old node was properly stopped
        old_node.stop.assert_called_once()

        # Verify new node was started
        new_node.start.assert_called_once()

        await graph.stop()

    async def test_replace_nonexistent_node(self, mock_node: Mock) -> None:
        """Test replacing a node that doesn't exist in the graph."""
        graph = Graph()
        new_node = Mock(spec=BaseNode)
        new_node.id = "new_node"

        with pytest.raises(ValueError, match="Node not found in graph"):
            await graph.replace_node(mock_node, new_node)

    @pytest.mark.asyncio
    async def test_replace_node_handles_stop_error(self, mock_node: Mock) -> None:
        """Test node replacement when stopping the old node fails."""
        graph = Graph()
        old_node = mock_node
        new_node = Mock(spec=BaseNode)
        new_node.id = "new_node"

        # Setup mock to raise an exception during stop
        old_node.stop.side_effect = Exception("Stop error")

        graph.add_node(old_node)
        await graph.start()

        # Should raise the exception from stop
        with pytest.raises(Exception, match="Stop error"):
            await graph.replace_node(old_node, new_node)

        # Verify old node is still in graph
        assert old_node in graph.nodes
        assert new_node not in graph.nodes

        await graph.stop()
