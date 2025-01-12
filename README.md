# Livesync

The graph-based video processing framework for building real-time video applications. It supports both synchronous and asynchronous processing pipelines and offers a flexible node system for video manipulation.

## Installation

We recommend using `rye` for installation:

```bash
rye add livesync-io
```

Alternatively, you can use pip:

```bash
# install from PyPI
pip install livesync-io
```

## Usage

The library is designed around a graph-based architecture where nodes represent different processing steps that can be connected together to form a processing pipeline.

Here's a basic example:

```python
import asyncio
from livesync import Graph
from livesync.nodes import WebcamNode, FrameRateNode


async def main():
    # Create a processing graph
    graph = Graph()

    # Add a webcam input node
    webcam_node = WebcamNode(device_id=0, fps=30)
    graph.add_node(webcam_node)

    # Add a frame rate processing node
    frame_rate_node = FrameRateNode(target_fps=10)
    graph.add_node(frame_rate_node)

    # Connect the nodes
    graph.add_edge(webcam_node, frame_rate_node)

    # Start processing
    await graph.start()

    # Keep the graph running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await graph.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

## Features

### Asynchronous Processing

Each node in the graph acts as an independent processing unit with its own queue, enabling asynchronous processing of frames. This architecture is specifically designed for real-time video processing, allowing high-throughput and low-latency operations.

### Remote Processing

LiveSync supports distributed processing through gRPC-based remote nodes. You can offload processing to remote servers:

```python
from livesync.nodes.presets.livesync import ProcessorConfig, LivesyncRemoteNode

# Create a remote processing node

remote_node = LivesyncRemoteNode(
    endpoints=["localhost:50051"],
    configs=[ProcessorConfig(name="frame_rate", settings={"target_fps": "5"})],
)
```

### LiveKit Integration

Built-in support for LiveKit enables real-time video streaming and WebRTC capabilities:

```python
from livesync.nodes import LiveKitVideoSinkNode, LiveKitVideoSourceNode

# Stream video to LiveKit
livekit_sink = LiveKitVideoSinkNode(livekit_stream=stream)
graph.add_node(livekit_sink)
```

## Requirements

- Python 3.10 or higher
- OpenCV Python
- LiveKit SDK
- gRPC tools for remote processing

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

LiveSync is developed and maintained by OS Designers, Inc. Special thanks to all contributors who have helped shape this framework.
For support, feature requests, or bug reports, please open an issue on our [GitHub repository](https://github.com/OS-Designers/livesync).
