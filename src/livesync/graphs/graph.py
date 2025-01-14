import asyncio
from typing import Any
from logging import getLogger
from dataclasses import field, dataclass

from ..nodes.base_node import BaseNode

logger = getLogger(__name__)


@dataclass
class Graph:
    """Abstract base class for directed graph implementations using dataclass pattern.

    Provides core functionality for managing nodes and their connections in a directed graph,
    with support for asynchronous execution.
    """

    _nodes: list[BaseNode] = field(default_factory=list)
    _edges: dict[str, list[str]] = field(default_factory=dict)
    _tasks: list[asyncio.Task[Any]] = field(default_factory=list)
    _is_running: bool = field(default=False)
    _loop: asyncio.AbstractEventLoop | None = field(default=None)

    @property
    def is_running(self) -> bool:
        """Check if the graph is currently running."""
        return self._is_running

    @property
    def nodes(self) -> list[BaseNode]:
        """Get all nodes in the graph."""
        return self._nodes.copy()

    def add_node(self, node: BaseNode) -> None:
        """Add a node to the graph."""
        if node in self._nodes:
            raise ValueError(f"Node {node.id} already exists in the graph")
        self._nodes.append(node)
        self._edges[node.id] = []

    def add_edge(self, from_node: BaseNode, to_node: BaseNode) -> None:
        """Connect two nodes with directional edge."""
        self._validate_edge(from_node, to_node)
        self._edges[from_node.id].append(to_node.id)

    def _validate_edge(self, from_node: BaseNode, to_node: BaseNode) -> None:
        """Validate edge connection."""
        if not any(n.id == from_node.id for n in self._nodes):
            raise ValueError("Source node not found in graph")
        if not any(n.id == to_node.id for n in self._nodes):
            raise ValueError("Target node not found in graph")
        if from_node.id == to_node.id:
            raise ValueError("Self-loops are not allowed")
        if to_node.id in self._edges[from_node.id]:
            raise ValueError("Edge already exists")

    async def replace_node(self, old_node: BaseNode, new_node: BaseNode) -> None:
        """Replace an existing node with a new node while preserving connections."""
        if not any(n.id == old_node.id for n in self._nodes):
            raise ValueError("Old node not found in graph")

        # Store connection information of the old node
        predecessors = [n for n in self._nodes if old_node.id in self._edges[n.id]]
        successors = self.get_successors(old_node)

        is_running = self._is_running

        if is_running:
            await self.stop()

        # Replace the node
        self.remove_node(old_node)
        self.add_node(new_node)

        # Restore connections
        for pred in predecessors:
            self.add_edge(pred, new_node)
        for succ in successors:
            self.add_edge(new_node, succ)

        # Start the new node if graph is running
        if is_running:
            await self.start()

    def remove_node(self, node: BaseNode) -> None:
        """Remove a node from the graph."""
        node_id = node.id
        if not any(n.id == node_id for n in self._nodes):
            raise ValueError("Node not found in graph")

        self._nodes = [n for n in self._nodes if n.id != node_id]
        self._edges.pop(node_id, None)
        # Remove references from other nodes' edges
        for edges in self._edges.values():
            while node_id in edges:
                edges.remove(node_id)

    def get_node_by_id(self, node_id: str) -> BaseNode | None:
        """Retrieve a node by its identifier."""
        return next((node for node in self._nodes if node.id == node_id), None)

    def get_successors(self, node: BaseNode) -> list[BaseNode]:
        """Get all successor nodes."""
        successor_ids = self._edges.get(node.id, [])
        return [n for n in self._nodes if n.id in successor_ids]

    async def start(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        """Run all nodes in the graph asynchronously."""
        if self._is_running:
            raise RuntimeError("Graph is already running")

        try:
            self._is_running = True
            self._loop = loop or asyncio.get_running_loop()
            await self._run_nodes()

        except asyncio.CancelledError:
            logger.debug("Graph execution cancelled")
        except Exception as e:
            logger.error(f"Error during graph execution: {e}")
            raise

    async def _run_nodes(self) -> None:
        """Run all nodes in the graph asynchronously."""
        if not self._loop:
            raise RuntimeError("Loop is not set")

        try:
            for node in self._nodes:
                self._tasks.append(
                    self._loop.create_task(node.start(loop=self._loop, successors=self.get_successors(node)))
                )
            await asyncio.gather(*self._tasks)
        except Exception as e:
            logger.error(f"Error during graph execution: {e}")
            self._is_running = False
            raise

    async def stop(self) -> None:
        """Stop the graph."""
        if not self._is_running:
            return

        try:
            await self._stop_nodes()
        finally:
            await self._cancel_tasks()
            self._is_running = False
            self._tasks = []

    async def _stop_nodes(self) -> None:
        """Stop all nodes."""
        if not self._loop:
            raise RuntimeError("Loop is not set")

        stop_tasks: list[asyncio.Task[Any]] = []
        for node in self._nodes:
            try:
                stop_tasks.append(self._loop.create_task(node.stop()))
            except Exception as e:
                logger.error(f"Error stopping node {node.id}: {e}")

        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

    async def _cancel_tasks(self) -> None:
        """Cancel remaining tasks."""
        if not self._tasks:
            return

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task  # Wait for task to complete cancellation
                except (asyncio.CancelledError, Exception) as e:
                    logger.debug(f"Task cancellation: {e}")
