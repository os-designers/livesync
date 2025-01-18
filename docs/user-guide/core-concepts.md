# Core Concepts

LiveSync is built around a graph-based processing model that enables flexible media processing pipelines. Here are the key concepts you need to understand:

## Core Components

### 1. Graphs

The main container that manages the processing pipeline:

```python
from livesync import Graph

graph = Graph()
```

### 2. Nodes

Processing units that can be connected to form a pipeline. Nodes can be created in two ways:

```python
# Class-based approach
class ProcessingNode(Node):
    def step(self):
        return 42

# Functional approach
node = Node(name="processor", step_func=lambda self: 42)
```

### 3. Frames

Specialized containers for media data:

```python
from livesync import VideoFrame, AudioFrame

video_frame = VideoFrame(
    data=frame_data,
    timestamp_us=1234567,
    width=1920,
    height=1080,
    buffer_type="rgb24"
)
```

## Example Pipeline

Here's a complete example of a basic processing pipeline:

```python
from livesync import Graph, Node

# Create processing pipeline
graph = Graph()

# Define nodes
source = Node(name="source", step_func=lambda self: 2)
processor = Node(
    name="processor",
    step_func=lambda self: self.get_input("source") * 3
)

# Build graph
graph.add_node(source)
graph.add_node(processor)
graph.add_edge(source, processor)

# Execute
with graph.compile() as runner:
    runner.run(continuous=False)
```

## Pipeline Execution

```python
# Synchronous execution
with graph.compile() as runner:
    runner.run(continuous=True)

# Asynchronous execution
async with graph.compile() as runner:
    run = await runner.async_run()
    await run.wait()
```

---

**Next Steps:** Dive deeper into [Nodes](nodes.md) and [Graphs](graphs.md).
