import cv2

from ...core.nodes import Node
from ...core.fields import Field
from ...core.frames import VideoFrame


class ResolutionNode(Node):
    """A node that resizes frames to the specified height while maintaining aspect ratio."""

    target_height: int = Field(default=720, description="The target height of the frames")

    def bootstrap(self) -> None:
        if len(self.parents) != 1:
            raise ValueError("ResolutionNode must have a single parent")
        self._parent_node = self.parents[0]

    async def step(self) -> VideoFrame:
        """Resizes the frame while preserving its aspect ratio."""
        frame: VideoFrame = await self.get_input(self._parent_node.name)

        aspect_ratio = frame.width / frame.height
        new_width = int(self.target_height * aspect_ratio)
        new_height = self.target_height
        resized = cv2.resize(frame.data, (new_width, new_height), interpolation=cv2.INTER_NEAREST)  # type: ignore

        video_frame = VideoFrame(
            data=resized,  # type: ignore
            timestamp_us=frame.timestamp_us,
            width=new_width,
            height=new_height,
            buffer_type=frame.buffer_type,
        )
        return video_frame
