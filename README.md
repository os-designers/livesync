# LiveSync

The graph-based video processing framework for building real-time video applications. LiveSync provides a flexible node system for creating both synchronous and asynchronous media processing pipelines.

## Installation

We recommend using `rye` for installation:

```bash
rye add livesync-io
```

Alternatively, you can use pip:

```bash
pip install livesync-io
```

## Quick Start

Here's a simple example of a video recording pipeline:

```python
from livesync import Graph
from livesync.prebuilt.nodes import WebcamNode, FrameRateNode, VideoRecorderNode
from livesync.prebuilt.callbacks import NodeMonitoringCallback

# Create a processing graph
workflow = Graph()

# Configure nodes
webcam = WebcamNode(name="webcam", device_id=0, fps=30)
frame_rate = FrameRateNode(name="frame_rate", fps=10)
recorder = VideoRecorderNode(name="video_recorder", filename="output.mp4", fps=10)

# Build pipeline
workflow.add_node(webcam)
workflow.add_node(frame_rate)
workflow.add_node(recorder)

workflow.add_edge(webcam, frame_rate)
workflow.add_edge(frame_rate, recorder)

# Execute pipeline
with workflow.compile() as runner:
    try:
        run = runner.run(callback=NodeMonitoringCallback())
        print(run)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt: Stopping runner.")
```

## Features

- **Graph-Based Architecture**: Build complex processing pipelines using a simple, intuitive DAG structure
- **Real-Time Processing**: Optimized for handling continuous data streams with minimal latency
- **Flexible Node System**: Create custom processing nodes or use pre-built ones for common media operations
- **Async-First Design**: Leverages Python's asyncio for efficient concurrent processing

## Requirements

- Python 3.10 or higher
- OpenCV Python
- FFmpeg
- gRPC tools (for remote processing)

## Documentation

For detailed documentation and examples, visit our [documentation site](https://os-designers.github.io/livesync/).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

LiveSync is developed and maintained by OS Designers, Inc. For support, feature requests, or bug reports, please open an issue on our [GitHub repository](https://github.com/OS-Designers/livesync).
