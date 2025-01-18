from __future__ import annotations

from livesync import Node, Graph
from livesync.prebuilt.callbacks import LoggingCallback

if __name__ == "__main__":
    # Linear chain with multiplication
    #
    #   (X) -> (Y) -> (Z)
    #
    # Node X returns 2
    # Node Y multiplies that by 3 => 6
    # Node Z doubles that => 12

    workflow = Graph()

    def return_two(_: Node):
        """Return a constant number."""
        return 2

    async def multiply_by_three(self: Node):
        """Multiply input by a constant factor."""
        input_value = await self.get_input("x")
        return input_value * 3

    async def multiply_by_two(self: Node):
        """Multiply input by a constant factor."""
        input_value = await self.get_input("y")
        return input_value * 2

    node_x = Node(name="x", step_func=return_two)
    node_y = Node(name="y", step_func=multiply_by_three)
    node_z = Node(name="z", step_func=multiply_by_two)

    workflow.add_node(node_x)
    workflow.add_node(node_y)
    workflow.add_node(node_z)

    workflow.add_edge(node_x, node_y)
    workflow.add_edge(node_y, node_z)

    with workflow.compile() as runner:
        runner.run(continuous=False, callback=LoggingCallback())
