import time
from dataclasses import field, dataclass
from typing_extensions import override

from ...core.callbacks import NodeEvent, GraphEvent, CallbackProtocol


@dataclass
class NodeMetrics:
    """Metrics data for node monitoring"""

    node_name: str
    total_frames: int = 0
    dropped_frames: int = 0
    queue_size: int = 0

    # Latency tracking (in milliseconds)
    total_latency: float = 0
    min_latency: float = float("inf")
    max_latency: float = 0

    # Time window tracking
    window_start_time: float = field(default_factory=time.monotonic)
    window_frame_count: int = 0

    @property
    def avg_latency(self) -> float:
        return self.total_latency / self.total_frames if self.total_frames > 0 else 0

    @property
    def fps(self) -> float:
        current_time = time.monotonic()
        window_duration = current_time - self.window_start_time
        if window_duration > 0:
            return self.window_frame_count / window_duration
        return 0

    def reset_window(self) -> None:
        """Reset the time window metrics"""
        self.window_start_time = time.monotonic()
        self.window_frame_count = 0


class NodeMonitoringCallback(CallbackProtocol):
    """
    Callback for monitoring node performance metrics.

    Parameters
    ----------
    window_size : float
        Time window size in seconds for FPS calculation
    """

    def __init__(self, window_size: float = 60.0):
        self.window_size = window_size
        self.metrics: dict[str, NodeMetrics] = {}
        self._last_window_check = time.monotonic()
        self._step_start_times: dict[str, float] = {}
        self._last_display_time: float = 0
        self._display_interval = 0.5
        # Clear screen and hide cursor
        print("\033[2J\033[?25l", end="")
        # Store log messages
        self._log_messages: list[str] = []

    def _display_dashboard(self) -> None:
        current_time = time.monotonic()
        if current_time - self._last_display_time < self._display_interval:
            return

        # Move cursor to home position and clear screen
        print("\033[H\033[2J", end="")

        # Dashboard header
        print("\033[1m=== LiveSync Performance Monitor ===\033[0m")
        print(f"Window Size: {self.window_size}s | Active Nodes: {len(self.metrics)}")
        print("─" * 80)

        # Node metrics table
        print("\033[1mNode Name            FPS    Latency(ms)   Queue   Drop Rate\033[0m")
        for name, metrics in self.metrics.items():
            fps = metrics.fps
            avg_latency = metrics.avg_latency
            drop_rate = metrics.dropped_frames / metrics.total_frames * 100 if metrics.total_frames > 0 else 0

            fps_color = "\033[32m" if fps > 25 else "\033[33m" if fps > 15 else "\033[31m"
            latency_color = "\033[32m" if avg_latency < 50 else "\033[33m" if avg_latency < 100 else "\033[31m"

            print(
                f"{name:<20} {fps_color}{fps:5.1f}\033[0m  {latency_color}{avg_latency:8.1f}\033[0m    {metrics.queue_size:3d}    {drop_rate:5.1f}%"
            )

        print("─" * 80)
        print("\033[2m• Green: Good | Yellow: Warning | Red: Critical\033[0m")

        # Display last few log messages if any
        if self._log_messages:
            print("\nRecent Events:")
            for msg in self._log_messages[-3:]:  # Show last 3 messages
                print(msg)

        self._last_display_time = current_time

    def _add_log(self, message: str) -> None:
        self._log_messages.append(message)
        if len(self._log_messages) > 10:  # Keep only last 10 messages
            self._log_messages.pop(0)
        self._display_dashboard()

    @override
    def on_graph_start(self, event: GraphEvent) -> None:
        self._add_log(f"Graph execution started - {event.node_count} nodes")

    @override
    def on_graph_end(self, event: GraphEvent) -> None:
        self._add_log(f"Graph execution completed")

    @override
    def on_node_bootstrap(self, event: NodeEvent) -> None:
        self._add_log(f"Node '{event.node_name}' bootstrap started")

    @override
    def on_node_shutdown(self, event: NodeEvent) -> None:
        self._add_log(f"Node '{event.node_name}' shutdown started")

    @override
    def on_node_step_start(self, event: NodeEvent) -> None:
        if event.node_name not in self.metrics:
            self.metrics[event.node_name] = NodeMetrics(node_name=event.node_name)

        # Record start time for latency calculation
        self._step_start_times[event.node_name] = time.monotonic()

        metrics = self.metrics[event.node_name]

        # Update queue size
        # TODO: This is a hack to get the queue size. We need to find a better way to get the queue size.
        metrics.queue_size += 1

        # Check if we need to reset the window
        current_time = time.monotonic()
        if current_time - metrics.window_start_time >= self.window_size:
            metrics.reset_window()

    @override
    def on_node_step_end(self, event: NodeEvent) -> None:
        if event.node_name not in self.metrics:
            return

        metrics = self.metrics[event.node_name]
        metrics.total_frames += 1
        metrics.queue_size -= 1

        # Only count frames that actually produced output
        if event.output is not None:
            metrics.window_frame_count += 1

        # Calculate latency
        if event.node_name in self._step_start_times:
            start_time = self._step_start_times.pop(event.node_name)
            latency = (time.monotonic() - start_time) * 1000  # convert to ms
            metrics.total_latency += latency
            metrics.min_latency = min(metrics.min_latency, latency)
            metrics.max_latency = max(metrics.max_latency, latency)

        self._display_dashboard()
        self._add_log(
            f"Node '{event.node_name}' step {event.step_index} completed (Output is None: {event.output is None})"
        )

    @override
    def on_node_error(self, event: NodeEvent) -> None:
        if event.node_name not in self.metrics:
            return

        metrics = self.metrics[event.node_name]
        metrics.dropped_frames += 1
        self._step_start_times.pop(event.node_name, None)

    @override
    def on_graph_error(self, event: GraphEvent) -> None:
        self._add_log(f"Graph execution failed: {event.error}")

    def get_metrics(self, node_name: str) -> NodeMetrics:
        """Get current metrics for a node"""
        if node_name not in self.metrics:
            raise KeyError(f"Node {node_name} is not being monitored")
        return self.metrics[node_name]

    def __del__(self):
        # Show cursor when done
        print("\033[?25h", end="")
