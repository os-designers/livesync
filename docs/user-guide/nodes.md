# Nodes

Nodes in LiveSync are flexible processing units that can be created either through inheritance or direct function assignment. This flexibility allows you to choose the most convenient approach for your use case.

## Creating Nodes

### 1. Class-based Approach

Inherit from `Node` and define lifecycle methods:

```python
from livesync import Node, Field

class NumberNode(Node):
    number: int = Field(default=..., description="Number to output")

    async def bootstrap(self):
        """Optional initialization"""
        print("Starting up...")

    def step(self) -> int:
        """Main processing logic"""
        return self.number

    async def shutdown(self):
        """Optional cleanup"""
        print("Shutting down...")
```

### 2. Functional Approach

Directly assign processing functions to `Node`:

```python
from livesync import Node

# Sync function
def process_data(self: Node):
    return 42

# Async function
async def process_data_async(self: Node):
    input_value = await self.get_input("source")
    return input_value * 2

node_a = Node(name="sync_node", step_func=process_data)
node_b = Node(name="async_node", step_func=process_data_async)
```

## Node Lifecycle Methods

Nodes support three optional lifecycle methods:

1. **bootstrap**: Initialization (sync/async)
2. **step**: Main processing (sync/async/generator/async generator)
3. **shutdown**: Cleanup (sync/async)

## Input/Output Handling

Nodes can receive inputs from parent nodes and send outputs to child nodes:

```python
async def process(self: Node):
    # Get input from a specific parent
    data = await self.get_input("parent_name")

    # Get all inputs as a dictionary
    inputs = await self.get_inputs()

    # Process and return (automatically sent to children)
    return processed_data
```

## Example: Complete Pipeline

```python
from livesync import Graph, Node

# Create nodes
node_x = Node(name="x", step_func=lambda self: 2)
node_y = Node(name="y", step_func=lambda self: self.get_input("x") * 3)

# Build pipeline
graph = Graph()
graph.add_node(node_x)
graph.add_node(node_y)
graph.add_edge(node_x, node_y)

# Execute
with graph.compile() as runner:
    runner.run(continuous=False)
```

---

**Next Steps:** Learn about [Graphs](graphs.md) to understand pipeline construction.
