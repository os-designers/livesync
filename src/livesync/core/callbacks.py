from __future__ import annotations

from typing import Any, Literal, TypeVar, Protocol
from datetime import datetime
from dataclasses import field, dataclass

T = TypeVar("T")


@dataclass(kw_only=True)
class CallbackEvent:
    """Base class for all callback events"""

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class NodeEvent(CallbackEvent):
    """Event data for node-related callbacks (bootstrap, step_start, step_end, shutdown, error)."""

    event_type: Literal["bootstrap", "step_start", "step_end", "shutdown", "error", "cancelled"]
    node_name: str
    step_index: int | None = None
    output: Any = None
    error: Exception | None = None


@dataclass
class GraphEvent(CallbackEvent):
    """Event data for graph-related callbacks"""

    event_type: Literal["start", "end", "error"]
    node_count: int
    error: Exception | None = None


class CallbackProtocol(Protocol):
    """Protocol defining the callback interface"""

    def on_graph_start(self, event: GraphEvent) -> None: ...
    def on_graph_end(self, event: GraphEvent) -> None: ...
    def on_node_bootstrap(self, event: NodeEvent) -> None: ...
    def on_node_shutdown(self, event: NodeEvent) -> None: ...
    def on_node_step_start(self, event: NodeEvent) -> None: ...
    def on_node_step_end(self, event: NodeEvent) -> None: ...
    def on_node_error(self, event: NodeEvent) -> None: ...
    def on_graph_error(self, event: GraphEvent) -> None: ...
