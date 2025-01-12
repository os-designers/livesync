from typing import AsyncIterator
from dataclasses import dataclass
from typing_extensions import override

import numpy as np
from livekit import rtc  # type: ignore

from ...source_node import SourceNode
from ....frames.video_frame import VideoFrame

BUFFER_TYPE_MAP = {
    rtc.VideoBufferType.RGBA: "rgba",
    rtc.VideoBufferType.ABGR: "abgr",
    rtc.VideoBufferType.ARGB: "argb",
    rtc.VideoBufferType.BGRA: "bgra",
    rtc.VideoBufferType.RGB24: "rgb24",
    rtc.VideoBufferType.I420: "i420",
    rtc.VideoBufferType.I420A: "i420a",
    rtc.VideoBufferType.I422: "i422",
    rtc.VideoBufferType.I444: "i444",
    rtc.VideoBufferType.I010: "i010",
    rtc.VideoBufferType.NV12: "nv12",
}


@dataclass
class LiveKitVideoSourceNode(SourceNode):
    """Captures video from a LiveKit stream."""

    livekit_stream: rtc.VideoStream

    @override
    async def _source_frames(self) -> AsyncIterator[VideoFrame]:  # type: ignore[override]
        """Captures video frames from the LiveKit stream."""
        async for frame_event in self.livekit_stream:
            lk_frame = frame_event.frame
            frame_data = np.frombuffer(lk_frame.data, dtype=np.uint8).reshape((lk_frame.height, lk_frame.width, 3))
            video_frame = VideoFrame(
                width=lk_frame.width,
                height=lk_frame.height,
                buffer_type=BUFFER_TYPE_MAP[lk_frame.type],  # type: ignore
                data=frame_data,
                timestamp_us=frame_event.timestamp_us,
            )
            yield video_frame

    @override
    async def _stop_source(self):
        """Stops the node and closes the LiveKit stream."""
        await self.livekit_stream.aclose()
