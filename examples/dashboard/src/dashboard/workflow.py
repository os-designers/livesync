from typing import Literal
from dataclasses import dataclass

from PyQt6.QtGui import QImage, QPixmap

import livesync as ls
from livesync import layers

from .ui import MainWindow


@dataclass
class WorkflowSession:
    runner: ls.Runner
    run: ls.Run


class WorkflowManager:
    def __init__(self):
        self.current_session: WorkflowSession | None = None

    async def start_workflow(
        self,
        window: MainWindow,
        webcam_device_id: int = 0,
        max_quality: Literal["4K", "2K", "1080p", "720p", "480p", "360p", "240p", "144p"] = "720p",
        max_fps: int = 20,
    ) -> ls.Run:
        global _window
        _window = window
        # Cancel existing run if any
        if self.current_session:
            self.current_session.run.cancel()
            self.current_session = None

        # Create new workflow
        x = layers.WebcamInput(device_id=webcam_device_id)

        # Option 1. Use local frame rate node
        f1 = layers.FpsControlLayer(fps=max_fps)

        # Option 2. Use remote frame rate node for testing
        # f1 = RemoteNode(
        #     name="frame_rate",
        #     settings={"frame_rate_node": {"fps": max_fps}},
        #     endpoints=["localhost:50051"],
        # )

        f2 = layers.VideoQualityControlLayer(quality=max_quality)

        async def update_frame(x: ls.VideoFrame) -> None:
            global workflow_manager
            height, width = x.data.shape[:2]

            # Determine the number of channels.
            channels = x.data.shape[2] if len(x.data.shape) > 2 else 1

            if channels == 3:
                # 3-channel image: use Format_RGB888.
                bytes_per_line = 3 * width
                qimage = QImage(x.data.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
            elif channels == 4:
                # 4-channel image: use Format_RGBA8888.
                bytes_per_line = 4 * width
                qimage = QImage(x.data.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGBA8888)
            elif channels == 1:
                # 1-channel (grayscale) image: use Format_Grayscale8.
                bytes_per_line = width
                qimage = QImage(x.data.tobytes(), width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
            else:
                raise ValueError(f"Unsupported number of channels: {channels}")

            pixmap = QPixmap.fromImage(qimage)
            _window.update_frame(pixmap)  # type: ignore

        f3 = layers.Lambda(function=update_frame)

        y = f3(f2(f1(x)))

        runner = ls.Sync(inputs=[x], outputs=[y]).compile()
        run = await runner.async_run(callback=ls.LoggingCallback())

        # Store the session
        self.current_session = WorkflowSession(runner=runner, run=run)

        return run

    def cleanup(self):
        if self.current_session:
            self.current_session.run.cancel()
            self.current_session = None


# Global workflow manager instance
workflow_manager = WorkflowManager()
