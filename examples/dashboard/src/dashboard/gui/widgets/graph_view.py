from typing_extensions import override

from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QMouseEvent, QPaintEvent, QPainterPath, QLinearGradient
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtWidgets import QWidget

from livesync import Graph, BaseNode

from ...core.metrics import NodeMetrics


class NodeVisual:
    def __init__(self, node_id: str, x: float, y: float, width: float, height: float):
        self.node_id = node_id
        self.rect = QRectF(x, y, width, height)
        self.metrics: NodeMetrics | None = None
        self.color = QColor(230, 250, 230)
        self.border_color = QColor(70, 180, 70)

    def update_metrics(self, metrics: NodeMetrics):
        self.metrics = metrics
        if metrics.queue_size > 10:
            self.color = QColor(255, 250, 220)
            self.border_color = QColor(200, 180, 70)
        else:
            self.color = QColor(230, 250, 230)
            self.border_color = QColor(70, 180, 70)


class GraphView(QWidget):
    node_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.nodes: dict[str, NodeVisual] = {}
        self.connections: list[tuple[str, str]] = []
        self.selected_node: str | None = None
        self.dragging_node: str | None = None
        self.drag_start_pos: QPointF | None = None
        self.setMinimumSize(400, 300)
        self.setWindowTitle("Processing Pipeline")

    @override
    def mousePressEvent(self, a0: QMouseEvent | None = None):
        if a0 is None:
            return

        for node_id, node in self.nodes.items():
            if node.rect.contains(a0.position()):
                self.selected_node = node_id
                self.dragging_node = node_id
                self.drag_start_pos = a0.position() - node.rect.topLeft()
                self.node_selected.emit(node_id)
                self.update()
                break

    @override
    def mouseReleaseEvent(self, a0: QMouseEvent | None = None):
        if a0 is None:
            return

        self.dragging_node = None
        self.drag_start_pos = None

    @override
    def mouseMoveEvent(self, a0: QMouseEvent | None = None):
        if a0 is None:
            return

        if self.dragging_node is not None and self.drag_start_pos is not None:
            new_pos = a0.position() - self.drag_start_pos
            # Check screen boundaries
            new_pos.setX(max(0, min(new_pos.x(), self.width() - self.nodes[self.dragging_node].rect.width())))
            new_pos.setY(max(0, min(new_pos.y(), self.height() - self.nodes[self.dragging_node].rect.height())))
            self.nodes[self.dragging_node].rect.moveTopLeft(new_pos)
            self.update()

    @override
    def paintEvent(self, a0: QPaintEvent | None = None):
        if a0 is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw connections - add gradient effect
        gradient_pen = QPen()
        gradient_pen.setWidth(2)
        gradient_pen.setStyle(Qt.PenStyle.SolidLine)

        node_items = list(self.nodes.values())
        for i in range(len(node_items) - 1):
            current = node_items[i]
            next_node = node_items[i + 1]

            gradient = QLinearGradient(current.rect.center(), next_node.rect.center())
            gradient.setColorAt(0, current.border_color)
            gradient.setColorAt(1, next_node.border_color)
            gradient_pen.setBrush(gradient)
            painter.setPen(gradient_pen)

            # Draw curved connection
            path = QPainterPath()
            start = current.rect.center()
            end = next_node.rect.center()
            control1 = QPointF(start.x(), start.y() + (end.y() - start.y()) * 0.5)
            control2 = QPointF(end.x(), start.y() + (end.y() - start.y()) * 0.5)

            path.moveTo(start)
            path.cubicTo(control1, control2, end)
            painter.drawPath(path)

        # Draw nodes
        for node_id, node in self.nodes.items():
            # Add shadow effect
            shadow = QPainterPath()
            shadow.addEllipse(node.rect.translated(2, 2))
            painter.fillPath(shadow, QColor(0, 0, 0, 30))

            # Draw node background
            painter.setBrush(QBrush(node.color))
            if node_id == self.selected_node:
                painter.setPen(QPen(QColor(50, 120, 220), 3))
            else:
                painter.setPen(QPen(node.border_color, 2))
            painter.drawEllipse(node.rect)

            # Draw node ID
            font = painter.font()
            font.setBold(True)
            font.setPointSize(10)
            painter.setFont(font)
            painter.setPen(QPen(QColor(60, 60, 60)))

            # Display ID on two lines
            id_rect = QRectF(
                node.rect.x(),
                node.rect.y() + node.rect.height() * 0.15,  # Slightly adjust position
                node.rect.width(),
                node.rect.height() * 0.35,  # Expand area
            )

            # Wrap long ID appropriately
            wrapped_id = self._wrap_text(node_id, 7)  # Wrap at 10 characters
            painter.drawText(id_rect, Qt.AlignmentFlag.AlignCenter, wrapped_id)
            # Display metrics - bottom inside node
            font.setPointSize(8)
            font.setBold(False)
            painter.setFont(font)

            if node.metrics:
                fps_text = f"FPS: {node.metrics.fps:.1f}"
                queue_text = f"Q: {node.metrics.queue_size}"
            else:
                fps_text = "FPS: --"
                queue_text = "Q: --"

            metrics_rect = QRectF(
                node.rect.x(), node.rect.y() + node.rect.height() * 0.5, node.rect.width(), node.rect.height() * 0.4
            )
            painter.drawText(metrics_rect, Qt.AlignmentFlag.AlignCenter, f"{fps_text}\n{queue_text}")

    def _wrap_text(self, text: str, max_length: int) -> str:
        """Wrap long text to specified length"""
        if len(text) <= max_length:
            return text

        # Try wrapping at underscore or uppercase
        for i in range(max_length, 0, -1):
            if text[i] == "_" or (i < len(text) - 1 and text[i + 1].isupper()):
                return text[:i] + "\n" + text[i:]

        # If no suitable position is found, force line break
        return text[:max_length] + "\n" + text[max_length:]

    def update_graph(self, graph: Graph):
        """Update the graph view with the given graph"""
        # Reset existing nodes
        self.nodes.clear()
        self.selected_node = None

        # Find root node (node with no incoming edges)
        all_target_nodes: set[str] = set()
        for targets in graph._edges.values():
            all_target_nodes.update(targets)

        root_nodes = [node for node in graph.nodes if node.id not in all_target_nodes]
        if not root_nodes:
            return
        # Calculate positions starting from root
        width = self.width() / 2
        spacing = self.height() / (len(graph.nodes) + 1)
        current_y = spacing

        def add_node_recursive(node: BaseNode, visited: set[str]):
            nonlocal current_y
            if node.id in visited:
                return

            visited.add(node.id)
            x = width - 30
            y = current_y - 30
            self.nodes[node.id] = NodeVisual(node.id, x, y, 60, 60)
            current_y += spacing

            # Process successors
            for successor in graph.get_successors(node):
                add_node_recursive(successor, visited)

        # Start from root and traverse graph
        visited: set[str] = set()
        for root in root_nodes:
            add_node_recursive(root, visited)

        if graph.nodes:
            first_node_id = root_nodes[0].id
            self.selected_node = first_node_id
            self.node_selected.emit(first_node_id)
        self.update()

    def update_metrics(self, metrics: NodeMetrics):
        """Update the metrics for the selected node"""
        if self.selected_node:
            self.nodes[self.selected_node].update_metrics(metrics)
        self.update()
