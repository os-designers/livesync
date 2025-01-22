# Core Concepts

LiveSync is a framework for building real-time media processing pipelines, inspired by Keras. Here's how data flows through the system:

## 1. Streams

Streams are the foundation of LiveSync - they represent flowing data that moves through processing steps:

```python
x = WebcamInput(...)  # Source of frames
y = some_layer(x)     # Processed frames
```

Key characteristics:

- **Asynchronous Flow**: Data moves independently through the pipeline
- **Type Safety**: Each stream carries specific data types (e.g., VideoFrame, AudioFrame)
- **Backpressure**: Automatically manages flow when downstream processing is slower

## 2. Input Streams

Input streams are the data sources that trigger the pipeline:

```python
# Common input streams
webcam = ls.WebcamInput(device_id=0, fps=30)      # Video frames
mic = ls.MicrophoneInput(sample_rate=44100)       # Audio samples
```

Key points:

- **Trigger Role**: Input streams initiate data flow
- **Asynchronous Generation**: Continuously produce new data
- **Built-in Controls**: Manage frame rates, buffering, etc.

## 3. Layers

Layers define operations on streams. When you call a layer with a stream as input, it returns a new stream containing the operation to be performed, but no actual processing happens until the pipeline is executed:

```python
# Processing chain example
x = ls.WebcamInput(device_id=0)
processed = layers.FpsControl(fps=15)(x)          # Control frame rate
merged = layers.Merge([processed, mic])           # Combine streams
recorded = layers.MediaRecorder("output.mp4")(merged)
```

## 4. Sync

Sync orchestrates the pipeline by managing connections and execution:

```python
# Create and run a pipeline
sync = ls.Sync(
    inputs=[webcam, mic],    # Data sources
    outputs=[recorded]       # Final destinations
)
with sync.compile() as runner:
    runner.run()
```

What Sync does:

- **Path Management**: Tracks routes from inputs to outputs
- **Validation**: Ensures proper pipeline connections
- **Execution**: Coordinates data flow
- **Resource Management**: Handles cleanup and shutdown

## Complete Example

Here's how everything works together:

```python
import livesync as ls
from livesync import layers

# Create input streams
x1 = ls.WebcamInput(device_id=0, fps=30)
x2 = ls.MicrophoneInput(sample_rate=44100)

# Build processing pipeline
h = layers.FpsControl(fps=15)(x1)
u = layers.Merge([x1, x2], how="any")
y = layers.MediaRecorder("output.mp4")(u)

# Run pipeline
sync = ls.Sync(inputs=[webcam, mic], outputs=[y])
with sync.compile() as runner:
    runner.run()
```

This creates a pipeline where:

- Webcam generates frames (Input Stream)
- Frames flow through FPS control (Layer)
- Processed frames are recorded (Layer)
- Sync manages the entire flow

This creates a pipeline that:

1. Captures webcam frames and audio (Input Streams)
2. Controls frame rate (Layer)
3. Merges the streams (Layer)
4. Records to an MP4 file (Layer)

## Next Steps

- See complete [Examples](./basic.md)
