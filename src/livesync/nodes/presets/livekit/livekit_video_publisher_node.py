from dataclasses import dataclass
from typing_extensions import override

from livekit import rtc  # type: ignore

from ...base_node import BaseNode
from ....frames.video_frame import VideoFrame

BUFFER_TYPE_MAP = {
    "rgba": rtc.VideoBufferType.RGBA,
    "abgr": rtc.VideoBufferType.ABGR,
    "argb": rtc.VideoBufferType.ARGB,
    "bgra": rtc.VideoBufferType.BGRA,
    "rgb24": rtc.VideoBufferType.RGB24,
    "i420": rtc.VideoBufferType.I420,
    "i420a": rtc.VideoBufferType.I420A,
    "i422": rtc.VideoBufferType.I422,
    "i444": rtc.VideoBufferType.I444,
    "i010": rtc.VideoBufferType.I010,
    "nv12": rtc.VideoBufferType.NV12,
}


@dataclass
class LiveKitVideoPublisherNode(BaseNode):
    """Sends video frames to a LiveKit video source."""

    livekit_source: rtc.VideoSource

    @override
    async def process_frame(self, frame: VideoFrame):  # type: ignore[override]
        livekit_frame = rtc.VideoFrame(
            width=frame.width,
            height=frame.height,
            type=BUFFER_TYPE_MAP[frame.buffer_type],
            data=frame.data.tobytes(),
        )
        self.livekit_source.capture_frame(livekit_frame)
