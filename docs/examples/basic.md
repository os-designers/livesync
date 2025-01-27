# Quick Start

This guide walks you through creating your first LiveSync pipeline for media processing.

## Creating a Simple Video Pipeline

LiveSync uses a graph-based architecture where nodes represent different processing steps. Let's create a simple video processing pipeline.

### Example: Webcam Recording Pipeline

```python
import livesync as ls
from livesync import layers

# Create input stream
x = ls.WebcamInput(name="webcam", device_id=0, fps=30)

# Create processing layers
f1 = layers.FpsControl(name="frame_rate", fps=10)
f2 = layers.VideoRecorder(
    name="video_recorder",
    filename="./output.mp4"
)

y = f2(f1(x))

# Create and run pipeline
sync = ls.Sync(inputs=[x], outputs=[y])
with sync.compile() as runner:
    run = runner.run(callback=ls.LoggingCallback())
```

This pipeline:

1. Captures video from your webcam at 30 FPS
2. Processes it through a frame rate controller to achieve 10 FPS
3. Records the output to a video file

```
  ●  (f2): Records processed frames to MP4 file
  │
  ●  (f1): Controls frame rate of the stream
  │
  ◇  (x): Captures frames from webcam
```

## Running the Example

Save the script as `webcam_fps_control.py` and run:

```bash
rye run examples/04_webcam_fps_control.py
```

The pipeline will start capturing from your webcam and save the processed video to `output.mp4`.

---

**Next Steps**

- Learn about more complex pipelines in the [User Guide](../user-guide/core-concepts.md)
- See more examples in the [Examples](../examples/advanced.md) section
