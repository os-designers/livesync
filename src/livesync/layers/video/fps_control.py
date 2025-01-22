from ...frames.video_frame import VideoFrame
from ..core.callable_layer import CallableLayer


class FpsControlLayer(CallableLayer[VideoFrame, VideoFrame | None]):
    """A layer that drops frames to achieve a target FPS."""

    def __init__(self, fps: int = 30, name: str | None = None) -> None:
        super().__init__(name=name)
        self.fps = fps
        self._last_pts = -1
        self._frame_interval_pts = 0  # Will be calculated on first frame

    async def call(self, x: VideoFrame) -> VideoFrame | None:
        """Drops frames if they're too close in time."""
        if x.pts < 0:
            raise ValueError("Frame PTS must be non-negative")

        if x.time_base is None:
            raise ValueError("Frame must have a time_base")

        # Calculate frame interval in PTS units on first frame
        if self._frame_interval_pts == 0:
            target_interval = 1.0 / self.fps
            self._frame_interval_pts = int(target_interval / float(x.time_base))

        if self._last_pts >= 0:
            elapsed_pts = x.pts - self._last_pts
            if elapsed_pts < self._frame_interval_pts:
                return None

        self._last_pts = x.pts
        return x
