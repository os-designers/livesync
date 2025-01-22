import cv2

from ..._utils.logs import logger
from ...frames.video_frame import VideoFrame
from ..core.callable_layer import CallableLayer


class ResolutionControlLayer(CallableLayer[VideoFrame, VideoFrame | None]):
    """A layer that resizes frames to the specified height while maintaining aspect ratio."""

    def __init__(self, target_height: int = 720, name: str | None = None) -> None:
        super().__init__(name=name)
        self.target_height = target_height

    async def call(self, x: VideoFrame) -> VideoFrame | None:
        """Resizes the frame while preserving its aspect ratio."""
        try:
            aspect_ratio = x.width / x.height
            new_width = int(self.target_height * aspect_ratio)
            new_height = self.target_height
            resized = cv2.resize(x.data, (new_width, new_height), interpolation=cv2.INTER_NEAREST)  # type: ignore

            video_frame = VideoFrame(
                data=resized,  # type: ignore
                pts=x.pts,
                width=new_width,
                height=new_height,
                buffer_type=x.buffer_type,
            )
            return video_frame
        except Exception as e:
            logger.error(f"Error during resolution control: {e}")
            return None
