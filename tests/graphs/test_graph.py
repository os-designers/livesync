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
