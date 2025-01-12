from time import time
from logging import getLogger
from typing_extensions import override

from livesync.nodes import BaseNode, NodeCallbackHandler
from livesync.frames import BaseFrame, VideoFrame

from .metrics import NodeMetrics
from ..gui.main_window import MainWindow

logger = getLogger(__name__)


class NodeMonitor(NodeCallbackHandler):
    """Monitors node performance metrics by implementing NodeCallbackHandler."""

    def __init__(self, window: MainWindow):
        self._window = window
        self._metrics: dict[str, NodeMetrics] = {}

    def _get_or_create_metrics(self, node: BaseNode) -> NodeMetrics:
        """Get or create metrics object for a node"""
        if node.id not in self._metrics:
            self._metrics[node.id] = NodeMetrics()
        return self._metrics[node.id]

    @override
    async def on_frame_received(self, node: BaseNode, frame: BaseFrame):
        """Called when a frame is received by a node"""
        metrics = self._get_or_create_metrics(node)
        metrics.total_received_frames += 1

        # Record frame reception time
        current_time = time()
        metrics.processing_start_times[frame.timestamp_us] = current_time

    @override
    async def on_frame_processed(self, node: BaseNode, frame: BaseFrame):
        """Called when a frame has been processed by a node"""
        metrics = self._get_or_create_metrics(node)
        current_time = time()

        # Record frame completion
        metrics.total_processed_frames += 1
        metrics.recent_frame_times.append(current_time)

        # Calculate processing latency
        if frame.timestamp_us in metrics.processing_start_times:
            latency = current_time - metrics.processing_start_times[frame.timestamp_us]
            metrics.total_latency += latency
            metrics.max_latency = max(metrics.max_latency, latency)
            metrics.min_latency = min(metrics.min_latency, latency)
            del metrics.processing_start_times[frame.timestamp_us]

        # Calculate dropped frames
        metrics.total_dropped_frames = metrics.total_received_frames - metrics.total_processed_frames

        # Calculate queue size
        metrics.queue_size = self.get_queue_size(node)

        # Update the window
        if isinstance(frame, VideoFrame):
            self._window.on_frame_processed(node.id, frame, metrics)

    def get_queue_size(self, node: BaseNode) -> int:
        """Get current input queue size of the node"""
        return node._input_queue.qsize()

    def get_metrics(self, node: BaseNode) -> NodeMetrics:
        """Get metrics for a specific node"""
        return self._get_or_create_metrics(node)
