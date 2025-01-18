# Quick Start

This guide walks you through creating your first LiveSync pipeline for media processing.

## Creating a Simple Video Pipeline

LiveSync uses a graph-based architecture where nodes represent different processing steps. Let's create a simple video processing pipeline.

### Example: Webcam Recording Pipeline

```python
from livesync import Graph
from livesync.prebuilt.nodes import WebcamNode, FrameRateNode, VideoRecorderNode
from livesync.prebuilt.callbacks import NodeMonitoringCallback

# Create a new graph
workflow = Graph()

# Create nodes
node_x = WebcamNode(name="webcam", device_id=0, fps=30)    # Capture frames
node_y = FrameRateNode(name="frame_rate", fps=10)          # Control frame rate
node_z = VideoRecorderNode(filename="./output.mp4", fps=5) # Record video

# Add nodes to graph
workflow.add_node(node_x)
workflow.add_node(node_y)
workflow.add_node(node_z)

# Connect nodes
workflow.add_edge(node_x, node_y)
workflow.add_edge(node_y, node_z)

# Run the pipeline
with workflow.compile() as runner:
    try:
        run = runner.run(callback=NodeMonitoringCallback())
        print(run)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt: Stopping runner.")
```

This pipeline:

1. Captures video from your webcam at 30 FPS
2. Processes it through a frame rate controller to achieve 10 FPS
3. Records the output to a video file at 10 FPS

## Running the Example

Save the script as `webcam_recording.py` and run:

```bash
python webcam_recording.py
```

The pipeline will start capturing from your webcam and save the processed video to `output.mp4`.

## Pipeline Visualization

```
(Webcam) => (Frame Rate) => (Video Recorder)
   30fps        10fps           10fps
```

---

**Next Steps**

- Learn about more complex pipelines in the [User Guide](../user-guide/core-concepts.md)
- Explore pre-built nodes in the [Node Reference](../reference/nodes.md)
- See more examples in the [Examples](../examples/basic.md) section
