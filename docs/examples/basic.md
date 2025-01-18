# Basic Examples

## Linear Chain Processing

LiveSync supports both class-based and functional approaches for creating nodes. Here are two equivalent implementations:

### Class-based Approach

```python
from livesync import Node, Field, Graph

class NumberNode(Node):
    number: int = Field(default=..., description="Number to output")

    def step(self) -> int:
        return self.number

class MultiplierNode(Node):
    source: str = Field(default=..., description="Source node name")
    factor: int = Field(default=..., description="Multiplication factor")

    async def step(self) -> int:
        input_value = await self.get_input(self.source)
        return input_value * self.factor

# Build pipeline
workflow = Graph()
node_x = NumberNode(number=2)
node_y = MultiplierNode(factor=3, source=node_x.name)
```

### Functional Approach

```python
from livesync import Node, Graph

# Define processing functions
def return_two(self: Node) -> int:
    return 2

async def multiply_by_three(self: Node) -> int:
    input_value = await self.get_input("x")
    return input_value * 3

# Build pipeline
workflow = Graph()
node_x = Node(name="x", step_func=return_two)
node_y = Node(name="y", step_func=multiply_by_three)
```
