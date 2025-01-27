# LiveSync

![Logo](logo.png)

A Keras-inspired asynchronous stream processing framework for building real-time media applications. LiveSync provides a flexible layer system for creating both synchronous and asynchronous media processing pipelines.

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

Here's a simple example of a webcam recording pipeline:

```python
import livesync as ls
from livesync import layers

x = ls.WebcamInput(device_id=0, fps=30)

f1 = layers.FpsControlLayer(fps=10)
f2 = layers.VideoRecorderLayer(filename="./examples/output.mp4")

h = f1(x)
y = f2(h)

sync = ls.Sync(inputs=[x], outputs=[y])
with sync.compile() as runner:
    runner.run(callback=ls.LoggingCallback())
```

You can visualize the pipeline by printing y.graph:

```
>>> print(y.graph)

● (f2): Records processed frames to MP4 file
│
● (f1): Controls frame rate of the stream
│
◇ (x): Captures frames from webcam (device 0)
```

## Features

- **Layer-Based Architecture**: Build complex processing pipelines using a Keras-inspired layer system
- **Async-First Design**: Built from the ground up for asynchronous stream processing
- **Media Processing**: Optimized for real-time audio and video processing
- **Flexible Stream System**: Support for both synchronous and asynchronous data flows
- **Remote Processing**: Built-in gRPC support for distributed processing

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
