from __future__ import annotations

import asyncio

from livesync import Node, Field, Graph
from livesync.prebuilt.callbacks import LoggingCallback


class NumberNode(Node):
    number: int = Field(default=..., description="The number to return")

    def step(self) -> int:
        """Return a constant number."""
        return self.number


class AsyncNumberNode(Node):
    sleep_time: float = Field(default=..., description="The time to sleep")
    number: int = Field(default=..., description="The number to return")

    async def step(self) -> int:
        """Return a constant number after sleeping."""
        await asyncio.sleep(self.sleep_time)  # simulate async work
        return self.number


class JoinNode(Node):
    source_a: str = Field(default=..., description="The source node to get the input from")
    source_b: str = Field(default=..., description="The source node to get the input from")

    async def step(self) -> int:
        """Sum the inputs from two nodes."""
        a = await self.get_input(self.source_a)
        b = await self.get_input(self.source_b)
        sum = a + b
        return sum


if __name__ == "__main__":
    # Simple branching and joining
    #
    #   (A) ---\
    #           => (C)
    #   (B) ---/
    #
    # Node X returns 10
    # Node Y returns 5
    # Node Z sums both => 15

    workflow = Graph()

    node_x = NumberNode(number=10)
    node_y = AsyncNumberNode(number=5, sleep_time=1.0)
    node_z = JoinNode(source_a=node_x.name, source_b=node_y.name)

    workflow.add_node(node_x)
    workflow.add_node(node_y)
    workflow.add_node(node_z)

    workflow.add_edge(node_x, node_z)
    workflow.add_edge(node_y, node_z)

    # Option 1: Using the runner with context manager for auto-cleanup
    with workflow.compile() as runner:
        run = runner.run(continuous=False, callback=LoggingCallback())
        print(run)  # Run(status=completed, runtime=1.002s)
