# Advanced Examples

## Media Processing Pipeline

### Video Recording

```python
from livesync import Graph
from livesync.prebuilt.nodes import WebcamNode, FrameRateNode, VideoRecorderNode

workflow = Graph()

# Configure nodes
webcam = WebcamNode(name="webcam", device_id=0, fps=30)
frame_rate = FrameRateNode(name="frame_rate", fps=15)
recorder = VideoRecorderNode(name="recorder", filename="output.mp4", fps=15)

# Build pipeline
workflow.add_node(webcam)
workflow.add_node(frame_rate)
workflow.add_node(recorder)

workflow.add_edge(webcam, frame_rate)
workflow.add_edge(frame_rate, recorder)
```

### Audio/Video Synchronization

```python
from livesync import Graph
from livesync.prebuilt.nodes import WebcamNode, MicrophoneNode, MediaSyncNode

workflow = Graph()

# Create media sources
video = WebcamNode(name="webcam", fps=30)
audio = MicrophoneNode(name="mic", sample_rate=44100)

# Configure sync node
sync = MediaSyncNode(
    name="sync",
    buffer_size=30,
    max_sync_threshold_us=5000,
    audio_node="mic",
    video_node="webcam"
)

# Build pipeline
workflow.add_edge(video, sync)
workflow.add_edge(audio, sync)
```

### Remote Processing

```python
from livesync import Graph
from livesync.prebuilt import RemoteNode, WebcamNode

workflow = Graph()

# Configure nodes
webcam = WebcamNode(name="webcam", fps=30)
remote = RemoteNode(
    name="remote",
    endpoints=["localhost:50051"],
    settings={"resolution_node": {"target_height": "320"}}
)

workflow.add_edge(webcam, remote)
```
