from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QMainWindow, QSizePolicy, QVBoxLayout

from livesync import Graph, AudioFrame, VideoFrame

from ..core.metrics import NodeMetrics
from .widgets.graph_view import GraphView
from .widgets.metrics_tree import MetricsTree


class MainWindow(QMainWindow):
    WINDOW_X = 100
    WINDOW_Y = 100
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 600

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LiveSync")
        self.setGeometry(self.WINDOW_X, self.WINDOW_Y, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        # Set up the main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create top section (video and pipeline view)
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
        video_layout.addWidget(video_label_title)

        # Video label
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.video_label.setMinimumSize(320, 180)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        video_layout.addWidget(self.video_label)

        # Graph view (right side)
        self.graph_view = GraphView()
        graph_layout = QVBoxLayout()
        graph_label = QLabel("Processing Pipeline")
        graph_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        graph_layout.addWidget(graph_label)
        graph_layout.addWidget(self.graph_view)

        # Add to top layout
        top_layout.addWidget(self.video_container, stretch=6)
        top_layout.addLayout(graph_layout, stretch=4)

        # Create bottom section (metrics trees)
        bottom_container = QWidget()
        bottom_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)  # 수직 방향으로 고정
        bottom_layout = QHBoxLayout(bottom_container)

        # Create metrics trees with labels
        node_metrics_container = QWidget()
        node_metrics_layout = QVBoxLayout(node_metrics_container)
        node_metrics_label = QLabel("Selected Node Statistics")
        node_metrics_label.setStyleSheet("font-weight: bold; font-size: 14px;")
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
        node_metrics_layout.addWidget(node_metrics_label)
        node_metrics_layout.addWidget(self.node_metrics_tree)

        pipeline_metrics_container = QWidget()
        pipeline_metrics_layout = QVBoxLayout(pipeline_metrics_container)
        pipeline_metrics_label = QLabel("Overall Pipeline Statistics")
        pipeline_metrics_label.setStyleSheet("font-weight: bold; font-size: 14px;")
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
        pipeline_metrics_layout.addWidget(pipeline_metrics_label)
        pipeline_metrics_layout.addWidget(self.pipeline_metrics_tree)

        # Add metrics to bottom layout
        bottom_layout.addWidget(node_metrics_container)
        bottom_layout.addWidget(pipeline_metrics_container)

        # Add top and bottom sections to main layout
        self.main_layout.addWidget(top_container)
        self.main_layout.addWidget(bottom_container)

        # Display black screen initially
        self.show_black_screen()

        # Store node frames
        self._current_node_id: str | None = None
        self._node_metrics: dict[str, NodeMetrics] = {}
        self._audio_frames: dict[str, AudioFrame] = {}
        self._video_frames: dict[str, VideoFrame] = {}

        # Connect pipeline view node selection to metrics update
        self.graph_view.node_selected.connect(self.on_node_selected)  # type: ignore

    def on_node_selected(self, node_id: str):
        """Node selected, update metrics and frame"""
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
        """Show the frame of the selected node"""
        video_frame = self._video_frames.get(node_id)
        if video_frame:
            self._render_video_frame(video_frame)

    def show_black_screen(self):
        width = 640
        height = 360

        black_pixmap = QPixmap(width, height)
        black_pixmap.fill(Qt.GlobalColor.black)
        self.video_label.setPixmap(black_pixmap)
        self.video_label.setMinimumSize(width, height)

    def _render_video_frame(self, frame: VideoFrame) -> None:
        """Render the video frame to the video label"""
        h, w, ch = frame.data.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)  # type: ignore
        pixmap = QPixmap.fromImage(qt_image)

        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(scaled_pixmap)

    def update_graph(self, graph: Graph):
        """Update the graph view with the given graph"""
        self.graph_view.update_graph(graph)

    def on_frame_processed(self, node_id: str, frame: VideoFrame, metrics: NodeMetrics):
        """Handle frame processed for the pipeline"""
        self._video_frames[node_id] = frame
        self._node_metrics[node_id] = metrics

        # Current selected node's frame, update the screen
        if self._current_node_id == node_id:
            self._show_node_frame(node_id)
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
            self.graph_view.update_metrics(metrics)
