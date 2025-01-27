from dataclasses import dataclass

import cv2
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QWidget,
    QSpinBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)


@dataclass
class StreamSettings:
    webcam_device_id: int
    quality: str
    target_fps: int


class MainWindow(QMainWindow):
    settings_changed = pyqtSignal(StreamSettings)

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._init_ui()
        self._load_devices()

    def _setup_window(self):
        self.setWindowTitle("Dashboard")
        self.setGeometry(100, 100, 1024, 768)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel for video display
        video_container = QWidget()
        video_layout = QVBoxLayout(video_container)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        video_layout.addWidget(self.video_label)
        main_layout.addWidget(video_container, stretch=2)

        # Right panel for settings
        settings_panel = self._create_settings_panel()
        main_layout.addWidget(settings_panel, stretch=1)

        self.show_black_screen()

    def _create_settings_panel(self):
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)

        # Device selection group
        device_group = QGroupBox("Device Settings")
        device_layout = QVBoxLayout(device_group)

        # Camera selection
        camera_layout = QHBoxLayout()
        camera_label = QLabel("Camera:")
        self.camera_combo = QComboBox()
        camera_layout.addWidget(camera_label)
        camera_layout.addWidget(self.camera_combo)
        device_layout.addLayout(camera_layout)

        # Quality settings
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Quality:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["144p", "240p", "360p", "480p", "SD", "HD", "FHD", "2K", "4K"])  # type: ignore
        self.quality_combo.setCurrentText("HD")
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        device_layout.addLayout(quality_layout)

        # Target FPS settings
        target_fps_layout = QHBoxLayout()
        target_fps_label = QLabel("Target FPS:")
        self.target_fps_spin = QSpinBox()
        self.target_fps_spin.setRange(1, 60)
        self.target_fps_spin.setValue(20)
        target_fps_layout.addWidget(target_fps_label)
        target_fps_layout.addWidget(self.target_fps_spin)
        device_layout.addLayout(target_fps_layout)

        # Apply button
        self.apply_button = QPushButton("Apply Settings")
        self.apply_button.clicked.connect(self._on_settings_changed)  # type: ignore
        device_layout.addWidget(self.apply_button)

        settings_layout.addWidget(device_group)
        settings_layout.addStretch()

        return settings_container

    def _load_devices(self):
        self.camera_combo.clear()
        # Enumerate available cameras
        camera_list: list[str] = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                camera_list.append(f"Camera {i}")
                cap.release()
        self.camera_combo.addItems(camera_list)  # type: ignore

    def _on_settings_changed(self):
        settings = StreamSettings(
            webcam_device_id=self.camera_combo.currentIndex(),
            quality=self.quality_combo.currentText(),
            target_fps=self.target_fps_spin.value(),
        )
        self.settings_changed.emit(settings)

    def show_black_screen(self, width: int = 640, height: int = 360):
        black_pixmap = QPixmap(width, height)
        black_pixmap.fill(Qt.GlobalColor.black)
        self._display_frame(black_pixmap)

    def update_frame(self, frame_pixmap: QPixmap):
        self._display_frame(frame_pixmap)

    def _display_frame(self, pixmap: QPixmap):
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)
