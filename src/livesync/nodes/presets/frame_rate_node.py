from dataclasses import field, dataclass
from typing_extensions import override

from ..base_node import BaseNode
from ...frames.base_frame import BaseFrame


@dataclass
class FrameRateNode(BaseNode):
    """Drops frames to achieve a target FPS."""

    target_fps: float = field(default=30)
    _frame_delay_us: int = field(init=False)
    _last_frame_time_us: int = field(init=False)
    _last_frame: BaseFrame | None = field(init=False)

    @override
    def __post_init__(self):
        """Calculates the delay between consecutive frames."""
        super().__post_init__()
        self._frame_delay_us = int(1_000_000 / self.target_fps)
        self._last_frame_time_us = 0
        self._last_frame = None

    @override
    async def process_frame(self, frame: BaseFrame) -> BaseFrame | None:
        """Drops frames if they're too close in time."""
        current_time_us = frame.timestamp_us
        if self._last_frame_time_us > 0:
            elapsed = current_time_us - self._last_frame_time_us
            if elapsed < self._frame_delay_us:
                return None

        self._last_frame_time_us = current_time_us
        self._last_frame = frame
        return frame
