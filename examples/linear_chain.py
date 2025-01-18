from __future__ import annotations

from livesync import Node, Field, Graph
from livesync.prebuilt.callbacks import LoggingCallback


class NumberNode(Node):
    number: int = Field(default=..., description="The number to return")

    def step(self) -> int:
        """Return a constant number."""
        return self.number


class MultiplierNode(Node):
    source: str = Field(default=..., description="The source node to get the input from")
    factor: int = Field(default=..., description="The factor to multiply by")

    async def step(self) -> int:
        """Multiply input by a constant factor."""
        input_value = await self.get_input(self.source)
        return input_value * self.factor


if __name__ == "__main__":
    # Linear chain with multiplication
    #
    #   (X) -> (Y) -> (Z)
    #
    # Node X returns 2
    # Node Y multiplies that by 3 => 6
    # Node Z doubles that => 12

    workflow = Graph()

    node_x = NumberNode(number=2)
    node_y = MultiplierNode(factor=3, source=node_x.name)
    node_z = MultiplierNode(factor=2, source=node_y.name)

    workflow.add_node(node_x)
    workflow.add_node(node_y)
    workflow.add_node(node_z)

    workflow.add_edge(node_x, node_y)
    workflow.add_edge(node_y, node_z)

    # Option 1: Run synchronously
    with workflow.compile() as runner:
        runner.run(continuous=False, callback=LoggingCallback())

    # Option 2: Run asynchronously
    async def main():
        async with workflow.compile() as runner:
            run = await runner.async_run(continuous=False, callback=LoggingCallback())
            print(run)  # Run(status=running, runtime=N/A)

            await run.wait()
            print(run)  # Run(status=completed, runtime=1.001s)
