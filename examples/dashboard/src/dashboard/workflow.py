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
        quality: str = "HD",
        target_fps: int = 20,
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
        f1 = layers.FpsControlLayer(fps=target_fps)

        # Option 2. Use remote frame rate node for testing
        # f1 = RemoteNode(
        #     name="frame_rate",
        #     settings={"frame_rate_node": {"fps": target_fps}},
        #     endpoints=["localhost:50051"],
        # )

        f2 = layers.VideoQualityControlLayer(quality=quality)

        async def update_frame(x: ls.VideoFrame) -> None:
            global workflow_manager
            height, width = x.data.shape[:2]
            bytes_per_line = 3 * width
            qimage = QImage(x.data.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
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
