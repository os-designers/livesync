from dataclasses import field, dataclass
from typing_extensions import override

import cv2

from ..base_node import BaseNode
from ...frames.video_frame import VideoFrame


@dataclass
class ResolutionNode(BaseNode):
    """Resizes frames to the specified height while maintaining aspect ratio."""

    target_height: int = field(default=720)

    @override
    async def process_frame(self, frame: VideoFrame) -> VideoFrame:  # type: ignore[override]
        """Resizes the frame while preserving its aspect ratio."""
        aspect_ratio = frame.width / frame.height
        new_width = int(self.target_height * aspect_ratio)
        new_height = self.target_height
        resized = cv2.resize(frame.data, (new_width, new_height), interpolation=cv2.INTER_NEAREST)  # type: ignore
        return VideoFrame(
            data=resized,  # type: ignore
            timestamp_us=frame.timestamp_us,
            width=new_width,
            height=new_height,
            buffer_type=frame.buffer_type,
        )
