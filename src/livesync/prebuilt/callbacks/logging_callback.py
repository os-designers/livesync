from __future__ import annotations

from typing_extensions import override

from ...utils.logs import logger
from ...core.callbacks import NodeEvent, GraphEvent, CallbackProtocol


class LoggingCallback(CallbackProtocol):
    """Default implementation of callbacks with logging"""

    @override
    def on_graph_start(self, event: GraphEvent) -> None:
        logger.info(f"[{event.timestamp}] Graph execution started - {event.node_count} nodes")

    @override
    def on_graph_end(self, event: GraphEvent) -> None:
        logger.info(f"[{event.timestamp}] Graph execution completed")

    @override
    def on_node_bootstrap(self, event: NodeEvent) -> None:
        logger.info(f"[{event.timestamp}] Node '{event.node_name}' bootstrap started")

    @override
    def on_node_shutdown(self, event: NodeEvent) -> None:
        logger.info(f"[{event.timestamp}] Node '{event.node_name}' shutdown started")

    @override
    def on_node_step_start(self, event: NodeEvent) -> None:
        logger.info(f"[{event.timestamp}] Node '{event.node_name}' step {event.step_index} started")

    @override
    def on_node_step_end(self, event: NodeEvent) -> None:
        logger.info(f"[{event.timestamp}] Node '{event.node_name}' step {event.step_index} completed: {event.output}")

    @override
    def on_node_error(self, event: NodeEvent) -> None:
        logger.error(f"[{event.timestamp}] Error in node '{event.node_name}': {event.error}")

    @override
    def on_graph_error(self, event: GraphEvent) -> None:
        logger.error(f"[{event.timestamp}] Graph execution failed: {event.error}")
