from time import time
from logging import getLogger
from collections import deque
from dataclasses import field, dataclass

logger = getLogger(__name__)


@dataclass
class NodeMetrics:
    """Stores performance metrics for a node."""

    total_received_frames: int = 0
    total_processed_frames: int = 0
    total_dropped_frames: int = 0
    total_latency: float = 0.0
    max_latency: float = 0.0
    min_latency: float = float("inf")

    queue_size: int = 0
    error_count: int = 0

    # Store frame processing timestamps for the last minute
    recent_frame_times: deque[float] = field(default_factory=lambda: deque(maxlen=60))
    # Store processing start time for each frame
    processing_start_times: dict[int, float] = field(default_factory=dict)

    @property
    def avg_latency(self) -> float:
        """Calculate average processing latency"""
        if self.total_received_frames == 0:
            return 0.0
        return self.total_latency / self.total_received_frames

    @property
    def fps(self) -> float:
        """Calculate FPS over the last minute"""
        now = time()
        # Remove entries older than 60 seconds
        while self.recent_frame_times and now - self.recent_frame_times[0] > 60:
            self.recent_frame_times.popleft()

        if not self.recent_frame_times:
            return 0.0

        # Calculate FPS based on the time difference between oldest frame and now
        time_diff = now - self.recent_frame_times[0]
        if time_diff <= 0:
            return 0.0
        return len(self.recent_frame_times) / time_diff

    @property
    def total_fps(self) -> float:
        """Calculate total FPS since start"""
        if not self.recent_frame_times:
            return 0.0
        total_time = time() - self.recent_frame_times[0]
        if total_time <= 0:
            return 0.0
        return self.total_processed_frames / total_time
