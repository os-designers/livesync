from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from .nodes import Node

if TYPE_CHECKING:
    from .runner import Runner


class Graph:
    """
    A unified graph implementation that can be used in both DAG and streaming pipelines.

    Attributes
    ----------
    nodes : list[Node]
        List of nodes in the graph
    """

    def __init__(self) -> None:
        self.nodes: list[Node] = []

    def add_node(self, node: Node) -> Node:
        """
        Add a node to the graph.
        """
        self.nodes.append(node)
        return node

    def add_edge(self, parent: Node, child: Node) -> None:
        """
        Add a directed edge from parent node to child node.

        Parameters
        ----------
        parent : Node
            Source node of the edge
        child : Node
            Target node of the edge
        """
        parent.children.append(child)
        child.parents.append(parent)

        q = asyncio.Queue[Any]()
        parent.output_queues[child.name] = q
        child.input_queues[parent.name] = q

    def compile(self) -> Runner:
        """
        Return a runner associated with this graph.
        Each graph type should return its corresponding runner.
        """
        from .runner import Runner

        return Runner(self)
