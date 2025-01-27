# Advanced Examples

Building on the basic concepts, let's explore more complex pipelines with media synchronization and stream merging.

## Media Synchronization Pipeline

This example demonstrates how to build a pipeline that synchronizes video and audio streams with precise timing control.

### Example: Synchronized Recording Pipeline

```python
import livesync as ls
from livesync import layers

# Create input streams
x1 = ls.WebcamInput(device_id=1, fps=30)
x2 = ls.MicrophoneInput(sample_rate=44100, chunk_size=1024)

# Create processing layers
f1 = layers.DelayLayer(interval=1.0)              # Add 1s delay to audio
f2 = layers.MediaSynchronizerLayer(
    buffer_size=1024,
    max_threshold=0.005                           # 5ms sync threshold
)
f3 = layers.MediaRecorderLayer(filename="./output.mp4")

# Build pipeline
h = f1(x2)                                        # Delayed audio
u = layers.Merge([x1, h], how="outer")           # Merge streams
y = f3(f2(u))                                     # Sync and record

# Create and run pipeline
sync = ls.Sync(inputs=[x1, x2], outputs=[y])
with sync.compile() as runner:
    runner.run(callback=ls.LoggingCallback())
```

This pipeline:

1. Captures video from webcam and audio from microphone
2. Adds a 1-second delay to the audio stream
3. Merges streams with "outer" mode (processes when either stream has data)
4. Synchronizes video and audio within 5ms precision
5. Records the synchronized output to MP4

```
  ●  (f3): Records synchronized media to MP4 file
  │
  ●  (f2): Synchronizes streams within 5ms threshold
  │
  ○  (u): Merges streams (processes on any input)
  │
  ○──●  (waits for either stream)
  │  │
  │  ●  (f1): Delays audio by 1 second
  │  │
  │  ◇  (x2): Microphone input
  │
  ◇  (x1): Webcam input
```

### Key Concepts

- **Stream Merging**: The `how="outer"` parameter in `Merge` means the layer processes whenever either input stream has data
- **Media Sync**: `MediaSynchronizerLayer` ensures audio and video stay synchronized within the specified threshold
- **Delay Control**: `DelayLayer` can adjust timing relationships between streams

## Running the Example

Save the script as `media_sync_recording.py` and run:

```bash
rye run examples/06_media_sync_recording.py
```

The pipeline will start capturing synchronized audio and video, saving the result to `output.mp4`.
