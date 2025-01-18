from ...core.nodes import Node
from ...core.fields import Field
from ...core.frames import VideoFrame


class FrameRateNode(Node):
    """A node that drops frames to achieve a target FPS."""

    fps: int = Field(default=30, description="The target FPS")

    def bootstrap(self) -> None:
        """Calculates the delay between consecutive frames."""
        if len(self.parents) != 1:
            raise ValueError("FrameRateNode must have a single parent")
        self._parent_node = self.parents[0]
        self._frame_interval_us = int(1_000_000 / self.fps)
        self._last_frame_time_us = 0

    async def step(self) -> VideoFrame | None:
        """Drops frames if they're too close in time."""
        frame: VideoFrame = await self.get_input(self._parent_node.name)

        current_time_us = frame.timestamp_us
        if current_time_us <= 0:
            raise ValueError("Frame timestamp must be positive")

        if self._last_frame_time_us > 0:
            elapsed = current_time_us - self._last_frame_time_us
            if elapsed < self._frame_interval_us:
                return None

        self._last_frame_time_us = current_time_us
        return frame
