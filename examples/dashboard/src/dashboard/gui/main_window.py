from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QWidget,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from livesync import Graph, AudioFrame, VideoFrame

from .utils import create_black_pixmap, convert_cv_frame_to_qpixmap
from ..core.metrics import NodeMetrics
from .widgets.graph_view import GraphView
from .widgets.metrics_tree import MetricsTree


class MainWindow(QMainWindow):
    """
    The Main Window that displays:
      - Live video
      - Pipeline graph
      - Node and pipeline metrics
    """

    WINDOW_X = 100
    WINDOW_Y = 100
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 600

    node_replace_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LiveSync")
        self.setGeometry(self.WINDOW_X, self.WINDOW_Y, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        self._current_node_id: str | None = None
        self._node_metrics: dict[str, NodeMetrics] = {}
        self._audio_frames: dict[str, AudioFrame] = {}
        self._video_frames: dict[str, VideoFrame] = {}

        self._init_ui()

    def _init_ui(self):
        """Initialize all UI components and layout."""
        # Set up the main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create top section (video and pipeline view)
        top_container = self._create_top_section()

        # Create bottom section (metrics trees)
        bottom_container = self._create_bottom_section()

        # Add sections to main layout
        self.main_layout.addWidget(top_container)
        self.main_layout.addWidget(bottom_container)

        # Display black screen initially
        self.show_black_screen()

    def _create_top_section(self) -> QWidget:
        """
        Create the top container holding the video view pipeline view.
        """
        top_container = QWidget()
        top_container.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )
        top_layout = QHBoxLayout(top_container)

        # Video container (left side)
        self.video_container = QWidget()
        video_layout = QVBoxLayout(self.video_container)

        # Video section label
        video_label_title = QLabel("Input Video Stream")
        video_label_title.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Video label
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        # Arrange video items
        video_layout.addWidget(video_label_title)
        video_layout.addWidget(self.video_label)

        # Graph view (right side)
        self.graph_view = GraphView()
        graph_layout = QVBoxLayout()
        graph_label = QLabel("Processing Pipeline")
        graph_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        graph_layout.addWidget(graph_label)
        graph_layout.addWidget(self.graph_view)

        # Add video and graph to top layout
        top_layout.addWidget(self.video_container, stretch=6)
        top_layout.addLayout(graph_layout, stretch=4)

        # Add replace button
        # Add toggle button
        self.toggle_button = QPushButton("Toggle Frame Rate Node")
        self.toggle_button.clicked.connect(self._on_toggle_button_clicked)
        graph_layout.addWidget(self.toggle_button)

        # Connect node selection signal
        self.graph_view.node_selected.connect(self.on_node_selected)

        return top_container

    def _on_toggle_button_clicked(self):
        """Emit signal when toggle button is clicked"""
        # self._previous_node_id = self._current_node_id
        self._current_node_id = None
        self.node_replace_requested.emit()

    def _create_bottom_section(self) -> QWidget:
        """
        Create the bottom container holding the node metrics and pipeline metrics.
        """
        bottom_container = QWidget()
        bottom_container.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )
        bottom_layout = QHBoxLayout(bottom_container)

        # Node metrics
        self.node_metrics_tree = MetricsTree(
            metrics_list=[
                "total_received_frames",
                "total_processed_frames",
                "total_dropped_frames",
                "queue_size",
                "max_latency",
                "min_latency",
                "total_latency",
            ]
        )
        node_metrics_container = self._create_metrics_container(
            title="Selected Node Statistics",
            tree_widget=self.node_metrics_tree,
        )

        # Pipeline metrics (example usage if you have pipeline-wide metrics)
        self.pipeline_metrics_tree = MetricsTree(
            metrics_list=[
                "total_received_frames",
                "total_processed_frames",
                "total_dropped_frames",
                "queue_size",
                "max_latency",
                "min_latency",
                "total_latency",
            ]
        )
        pipeline_metrics_container = self._create_metrics_container(
            title="Overall Pipeline Statistics",
            tree_widget=self.pipeline_metrics_tree,
        )

        # Add to bottom layout
        bottom_layout.addWidget(node_metrics_container)
        bottom_layout.addWidget(pipeline_metrics_container)

        return bottom_container

    @staticmethod
    def _create_metrics_container(title: str, tree_widget: MetricsTree) -> QWidget:
        """
        Helper to create a labeled container that holds a metrics tree.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        label = QLabel(title)
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(label)
        layout.addWidget(tree_widget)
        return container

    def on_node_selected(self, node_id: str):
        """
        Node selected, update metrics and frame on the UI.
        """
        self._current_node_id = node_id
        if node_id in self._node_metrics:
            metrics_dict = {
                "total_received_frames": self._node_metrics[node_id].total_received_frames,
                "total_processed_frames": self._node_metrics[node_id].total_processed_frames,
                "total_dropped_frames": self._node_metrics[node_id].total_dropped_frames,
                "queue_size": self._node_metrics[node_id].queue_size,
                "max_latency": self._node_metrics[node_id].max_latency,
                "min_latency": self._node_metrics[node_id].min_latency,
                "total_latency": self._node_metrics[node_id].total_latency,
            }
            self.node_metrics_tree.update_data(metrics_dict)
        self._show_node_frame(node_id)

    def _show_node_frame(self, node_id: str):
        """
        Show the frame of the selected node (if available).
        """
        video_frame = self._video_frames.get(node_id)
        if video_frame:
            pixmap = convert_cv_frame_to_qpixmap(video_frame)
            self._render_pixmap(pixmap)

    def show_black_screen(self, width: int = 640, height: int = 360):
        """
        Display a black rectangle initially or when no video is present.
        """
        black_pixmap = create_black_pixmap(width, height)
        self.video_label.setPixmap(black_pixmap)
        self.video_label.setMinimumSize(width, height)

    def _render_pixmap(self, pixmap: QPixmap):
        """
        Render a QPixmap to the video label, keeping aspect ratio.
        """
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(scaled_pixmap)

    def update_graph(self, graph: Graph):
        """
        Update the graph view with the given graph.
        """
        self.graph_view.update_graph(graph)

    def on_frame_processed(self, node_id: str, frame: VideoFrame, metrics: NodeMetrics):
        """
        Handle frame processed from a pipeline node, updating metrics and video display
        if it is the currently selected node.
        """
        self._video_frames[node_id] = frame
        self._node_metrics[node_id] = metrics

        # If this is the selected node, refresh display
        if self._current_node_id == node_id:
            pixmap = convert_cv_frame_to_qpixmap(frame)
            self._render_pixmap(pixmap)

            metrics_dict = {
                "total_received_frames": metrics.total_received_frames,
                "total_processed_frames": metrics.total_processed_frames,
                "total_dropped_frames": metrics.total_dropped_frames,
                "queue_size": metrics.queue_size,
                "max_latency": metrics.max_latency,
                "min_latency": metrics.min_latency,
                "total_latency": metrics.total_latency,
            }
            self.node_metrics_tree.update_data(metrics_dict)

            # Also update the node's visual metrics in the graph view
            self.graph_view.update_metrics(metrics)
