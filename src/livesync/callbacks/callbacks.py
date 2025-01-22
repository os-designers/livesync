from __future__ import annotations

import time
import logging

from .events import RunEvent, StreamEvent
from .protocol import CallbackProtocol
from .._utils.logs import logger


class LoggingCallback(CallbackProtocol):
    """Enhanced implementation of callbacks with configurable logging

    Parameters
    ----------
    log_level : str, default="debug"
        Logging level to use (debug, info, warning, error)
    log_fields : dict, optional
        Dictionary specifying which fields to log for each event type.
        Format: {event_type: [field_names]}
        Example: {"stream": ["stream_name", "step", "queue_size"]}
    format_templates : dict, optional
        Custom message templates for each event type.
        Format: {event_type: "message_template"}
        Example: {"stream_start": "Stream {stream_name} started"}
    """

    DEFAULT_LOG_FIELDS = {"stream": ["stream_name", "step", "input", "output", "error"], "run": ["error"]}

    DEFAULT_TEMPLATES = {
        "run_start": "Run execution started",
        "run_end": "Run execution completed",
        "run_error": "Run execution failed: {error}",
        "stream_start": "Stream '{stream_name}' Step {step} started, input={input}",
        "stream_end": "Stream '{stream_name}' Step {step} completed, output={output}",
        "stream_error": "Stream '{stream_name}' Step {step} failed: {error}",
    }

    def __init__(
        self,
        log_level: str = "info",
        log_fields: dict[str, list[str]] | None = None,
        format_templates: dict[str, str] | None = None,
    ) -> None:
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_fields = {**self.DEFAULT_LOG_FIELDS, **(log_fields or {})}
        self.templates = {**self.DEFAULT_TEMPLATES, **(format_templates or {})}

    def _format_event(self, template: str, event: StreamEvent | RunEvent) -> str:
        """Format event data using template and configured fields"""
        event_type = "stream" if isinstance(event, StreamEvent) else "run"
        fields = self.log_fields.get(event_type, [])

        # Get available event attributes that are in configured fields
        event_data = {field: getattr(event, field) for field in fields if hasattr(event, field)}

        return template.format(**event_data)

    def on_run_start(self, event: RunEvent) -> None:
        logger.log(self.log_level, self._format_event(self.templates["run_start"], event))

    def on_run_end(self, event: RunEvent) -> None:
        logger.log(self.log_level, self._format_event(self.templates["run_end"], event))

    def on_run_error(self, event: RunEvent) -> None:
        logger.log(self.log_level, self._format_event(self.templates["run_error"], event))

    def on_stream_start(self, event: StreamEvent) -> None:
        logger.log(self.log_level, self._format_event(self.templates["stream_start"], event))

    def on_stream_end(self, event: StreamEvent) -> None:
        logger.log(self.log_level, self._format_event(self.templates["stream_end"], event))

    def on_stream_error(self, event: StreamEvent) -> None:
        logger.error(self._format_event(self.templates["stream_error"], event))


class StreamMetrics:
    """Performance metrics tracker for a single stream.

    Parameters
    ----------
    stream_name : str
        Name of the stream being monitored.

    Attributes
    ----------
    total_streams : int
        Total number of streams processed.
    dropped_streams : int
        Number of streams that were dropped due to errors.
    queue_size : int
        Current size of the processing queue.
    total_latency : float
        Total accumulated processing latency in milliseconds.
    min_latency : float
        Minimum observed latency in milliseconds.
    max_latency : float
        Maximum observed latency in milliseconds.

    # Input/Output FPS tracking
    input_window_start_time : float
        Start time of the current input window.
    output_window_start_time : float
        Start time of the current output window.
    input_count : int
        Number of input streams processed in the current window.
    output_count : int
        Number of output streams processed in the current window.
    """

    def __init__(self, stream_name: str) -> None:
        self.stream_name = stream_name
        self.total_streams = 0
        self.dropped_streams = 0
        self.queue_size = 0
        self.total_latency = 0.0
        self.min_latency = float("inf")
        self.max_latency = 0.0

        # Input/Output FPS tracking
        self.input_window_start_time = time.monotonic()
        self.output_window_start_time = time.monotonic()
        self.input_count = 0
        self.output_count = 0

    @property
    def input_fps(self) -> float:
        """Calculate current input streams per second."""
        current_time = time.monotonic()
        window_duration = current_time - self.input_window_start_time
        return self.input_count / window_duration if window_duration > 0 else 0

    @property
    def output_fps(self) -> float:
        """Calculate current output streams per second."""
        current_time = time.monotonic()
        window_duration = current_time - self.output_window_start_time
        return self.output_count / window_duration if window_duration > 0 else 0

    @property
    def avg_latency(self) -> float:
        """Calculate average latency in milliseconds."""
        return self.total_latency / self.total_streams if self.total_streams > 0 else 0

    def reset_window(self) -> None:
        """Reset the time window metrics."""
        current_time = time.monotonic()
        self.input_window_start_time = current_time
        self.output_window_start_time = current_time
        self.input_count = 0
        self.output_count = 0


class StreamMonitoringCallback(CallbackProtocol):
    """Callback for monitoring stream performance metrics.

    Parameters
    ----------
    window_size : float, optional
        Time window size in seconds for FPS calculation, by default 60.0

    Attributes
    ----------
    metrics : dict
        Dictionary mapping stream names to their metrics.
    """

    def __init__(self, window_size: float = 60.0):
        self.window_size = window_size
        self.metrics: dict[str, StreamMetrics] = {}
        self._last_window_check = time.monotonic()
        self._step_start_times: dict[str, float] = {}
        self._input_start_times: dict[str, float] = {}
        self._output_start_times: dict[str, float] = {}
        self._last_display_time: float = 0
        self._display_interval = 0.5
        self._log_messages: list[str] = []

        # Clear screen and hide cursor
        print("\033[2J\033[?25l", end="")

    def _display_dashboard(self) -> None:
        """Display the performance monitoring dashboard."""
        current_time = time.monotonic()
        if current_time - self._last_display_time < self._display_interval:
            return

        # Move cursor to home position and clear screen
        print("\033[H\033[2J", end="")

        # Dashboard header
        print("\033[1m=== LiveSync Performance Monitor ===\033[0m")
        print(f"Window Size: {self.window_size}s | Active Nodes: {len(self.metrics)}")
        print("─" * 110)  # Reduced line length

        # Updated table header with wider Stream Name column and slightly reduced spacing
        header = (
            "\033[1m"
            "Stream Name                      "  # Increased to 30 chars
            "   #In      #Out    #Queue    #Drop  "  # Slightly reduced spacing
            " In FPS    Out FPS    Latency(ms)\033[0m"  # Slightly reduced spacing
        )
        print(header)

        for name, metrics in self.metrics.items():
            in_count = metrics.input_count
            out_count = metrics.output_count
            dropped = in_count - out_count if in_count > out_count else 0
            in_fps = metrics.input_fps
            out_fps = metrics.output_fps
            latency = metrics.avg_latency

            # Color coding based on performance metrics
            in_fps_color = "\033[32m" if in_fps > 25 else "\033[33m" if in_fps > 15 else "\033[31m"
            out_fps_color = "\033[32m" if out_fps > 25 else "\033[33m" if out_fps > 15 else "\033[31m"
            latency_color = "\033[32m" if latency < 50 else "\033[33m" if latency < 100 else "\033[31m"
            queue_color = (
                "\033[32m" if metrics.queue_size < 10 else "\033[33m" if metrics.queue_size < 20 else "\033[31m"
            )
            drop_color = "\033[32m" if dropped == 0 else "\033[31m"

            print(
                f"{name:<30}  "  # Increased to 30 chars
                f"{in_count:>8}  "
                f"{out_count:>8}  "
                f"{queue_color}{metrics.queue_size:>8}\033[0m  "
                f"{drop_color}{dropped:>8}\033[0m  "
                f"{in_fps_color}{in_fps:>8.1f}\033[0m  "
                f"{out_fps_color}{out_fps:>8.1f}\033[0m  "
                f"{latency_color}{latency:>8.1f}\033[0m"
            )

        print("─" * 110)  # Reduced line length

        self._last_display_time = current_time

    def _add_log(self, message: str) -> None:
        """Add a log message to the dashboard."""
        self._log_messages.append(message)
        if len(self._log_messages) > 10:  # Keep only last 10 messages
            self._log_messages.pop(0)
        self._display_dashboard()

    def on_run_start(self, event: RunEvent) -> None:  # noqa: ARG002
        self._add_log(f"Run execution started")

    def on_run_end(self, event: RunEvent) -> None:  # noqa: ARG002
        self._add_log(f"Run execution completed")

    def on_run_error(self, event: RunEvent) -> None:
        self._add_log(f"Run execution failed: {event.error}")

    def on_stream_start(self, event: StreamEvent) -> None:
        if event.stream_name not in self.metrics:
            self.metrics[event.stream_name] = StreamMetrics(stream_name=event.stream_name)

        metrics = self.metrics[event.stream_name]

        # Record start time for latency calculation
        self._step_start_times[event.stream_name] = time.monotonic()

        # Update input metrics
        if event.input is not None:
            metrics.input_count += 1

        metrics.queue_size = event.queue_size or 0

        # Check if we need to reset the window
        current_time = time.monotonic()
        if current_time - metrics.input_window_start_time >= self.window_size:
            metrics.reset_window()

    def on_stream_end(self, event: StreamEvent) -> None:
        if event.stream_name not in self.metrics:
            return

        metrics = self.metrics[event.stream_name]
        current_time = time.monotonic()

        # Update total streams and latency
        if event.stream_name in self._step_start_times:
            start_time = self._step_start_times.pop(event.stream_name)
            latency = (current_time - start_time) * 1000  # convert to ms
            metrics.total_latency += latency
            metrics.min_latency = min(metrics.min_latency, latency)
            metrics.max_latency = max(metrics.max_latency, latency)

        # Update output metrics
        if event.output is not None:
            metrics.output_count += 1
            metrics.total_streams += 1

        metrics.queue_size = event.queue_size or 0

        self._display_dashboard()
        self._add_log(f"Stream '{event.stream_name}' completed, output={event.output}")

    def on_stream_error(self, event: StreamEvent) -> None:
        if event.stream_name not in self.metrics:
            return

        metrics = self.metrics[event.stream_name]
        metrics.dropped_streams += 1
        self._input_start_times.pop(event.stream_name, None)
        self._output_start_times.pop(event.stream_name, None)

    def get_metrics(self, stream_name: str) -> StreamMetrics:
        """Get current metrics for a stream"""
        if stream_name not in self.metrics:
            raise KeyError(f"Stream {stream_name} is not being monitored")
        return self.metrics[stream_name]

    def __del__(self) -> None:
        # Show cursor when done
        print("\033[?25h", end="")
