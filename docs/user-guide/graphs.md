# Graphs

Graphs in LiveSync represent the processing pipeline structure. They manage node connections and data flow between nodes.

## Creating a Graph

```python
from livesync import Graph, Node

# Create a new graph
graph = Graph()

# Add nodes and connections
node_a = Node(name="a", step_func=lambda self: 42)
node_b = Node(name="b", step_func=lambda self: self.get_input("a") * 2)

graph.add_node(node_a)
graph.add_node(node_b)
graph.add_edge(node_a, node_b)
```

## Running a Graph

LiveSync supports both synchronous and asynchronous execution:

### Synchronous Execution

```python
# Using context manager (recommended)
with graph.compile() as runner:
    runner.run(continuous=False)
```

### Asynchronous Execution

```python
async def main():
    async with graph.compile() as runner:
        run = await runner.async_run(continuous=False)
        await run.wait()
```

## Execution Modes

### One-shot Execution

```python
runner.run(continuous=False)  # Run once and stop
```

### Continuous Processing

```python
runner.run(continuous=True)  # Run continuously until stopped
```

## Monitoring Execution

Use callbacks to monitor graph execution:

```python
from livesync.prebuilt.callbacks import LoggingCallback

with graph.compile() as runner:
    run = runner.run(
        continuous=True,
        callback=LoggingCallback()
    )
```

## Example: Linear Chain

```python
from livesync import Graph, Node

# Create a processing chain
workflow = Graph()

# Define nodes
node_x = Node(name="x", step_func=lambda self: 2)
node_y = Node(name="y", step_func=lambda self: self.get_input("x") * 3)
node_z = Node(name="z", step_func=lambda self: self.get_input("y") * 2)

# Build graph
workflow.add_node(node_x)
workflow.add_node(node_y)
workflow.add_node(node_z)

workflow.add_edge(node_x, node_y)
workflow.add_edge(node_y, node_z)

# Execute
with workflow.compile() as runner:
    runner.run(continuous=False)
```

## Graph Visualization

```
Linear Chain:
(X) -> (Y) -> (Z)

Parallel Processing:
    -> (B) ->
(A)         (D)
    -> (C) ->
```

---

**Next Steps:** Explore [Pre-built Nodes](../reference/prebuilt-nodes.md) for common processing tasks.
