# Frames

LiveSync provides specialized frame classes for handling different types of media data. The frame system is built around two main classes: `AudioFrame` and `VideoFrame`, both inheriting from `BaseFrame`.

## Frame Types

### Audio Frames

```python
from livesync import AudioFrame
import numpy as np

# Create an audio frame
audio_frame = AudioFrame(
    data=np.zeros((1024, 2)),          # (samples, channels)
    timestamp_us=1234567,              # microseconds
    sample_rate=44100,                 # Hz
    num_channels=2,                    # 1 (mono) or 2 (stereo)
    sample_format="float32",           # float32, int16, int32, uint8
    channel_layout="stereo"            # mono or stereo
)
```

### Video Frames

```python
from livesync import VideoFrame
import numpy as np

# Create a video frame
video_frame = VideoFrame(
    data=np.zeros((1080, 1920, 3)),   # (height, width, channels)
    timestamp_us=1234567,              # microseconds
    width=1920,
    height=1080,
    buffer_type="rgb24"               # rgba, rgb24, i420, etc.
)
```

## Supported Formats

### Video Buffer Types

- 4-channel: `rgba`, `abgr`, `argb`, `bgra`
- 3-channel: `rgb24`
- YUV formats: `i420`, `i420a`, `i422`, `i444`

### Audio Sample Formats

- `float32`
- `int16`
- `int32`
- `uint8`

## Serialization

Both frame types support serialization for network transmission or storage:

```python
# Serialize
frame_bytes = video_frame.tobytes()

# Deserialize
restored_frame = VideoFrame.frombytes(frame_bytes)
```

## Frame Validation

Frames automatically validate their data on creation:

- Correct dimensionality (2D for audio, 3D for video)
- Valid format types
- Positive timestamps
- Matching channel counts
- Correct buffer types

## Example Usage in Node

```python
from livesync import Node, VideoFrame
import numpy as np

class VideoProcessingNode(Node):
    async def step(self) -> VideoFrame:
        # Get input frame
        input_frame: VideoFrame = await self.get_input("camera")

        # Process frame data
        processed_data = np.array(input_frame.data) * 1.5

        # Create new frame
        return VideoFrame(
            data=processed_data,
            timestamp_us=input_frame.timestamp_us,
            width=input_frame.width,
            height=input_frame.height,
            buffer_type=input_frame.buffer_type
        )
```

---

**Next Steps:** Learn about [Pre-built Nodes](../reference/prebuilt-nodes.md) for media processing.
