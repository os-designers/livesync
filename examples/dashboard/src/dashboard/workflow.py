from dataclasses import dataclass

from PyQt6.QtGui import QImage, QPixmap

from livesync import Run, Node, Field, Graph, Runner, VideoFrame
from livesync.prebuilt.nodes import WebcamNode, FrameRateNode, ResolutionNode
from livesync.prebuilt.callbacks import NodeMonitoringCallback

from .main_window import MainWindow

_WEBCAM_FPS = 30


class OutputNode(Node):
    window: MainWindow = Field(default=..., description="The main window of the application")

    def bootstrap(self) -> None:
        if len(self.parents) != 1:
            raise ValueError("OutputNode must have a single parent")
        self._parent_node = self.parents[0]

    async def step(self) -> None:
        frame: VideoFrame = await self.get_input(self._parent_node.name)
        height, width = frame.data.shape[:2]
        bytes_per_line = 3 * width
        qimage = QImage(frame.data.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.window.update_frame(pixmap)


@dataclass
class WorkflowSession:
    runner: Runner
    run: Run


class WorkflowManager:
    def __init__(self):
        self.current_session: WorkflowSession | None = None

    async def start_workflow(
        self,
        window: MainWindow,
        webcam_device_id: int = 0,
        target_resolution: int = 360,
        target_fps: int = 20,
    ) -> Run:
        # Cancel existing run if any
        if self.current_session:
            self.current_session.run.cancel()
            self.current_session = None

        # Create new workflow
        workflow = Graph()

        video_input = WebcamNode(device_id=webcam_device_id, fps=_WEBCAM_FPS, name="webcam")
        resolution = ResolutionNode(target_height=target_resolution, name="resolution")
        frame_rate = FrameRateNode(fps=target_fps, name="frame_rate_default")
        output = OutputNode(window=window, name="output")

        workflow.add_node(video_input)
        workflow.add_node(frame_rate)
        workflow.add_node(resolution)
        workflow.add_node(output)

        workflow.add_edge(video_input, frame_rate)
        workflow.add_edge(frame_rate, resolution)
        workflow.add_edge(resolution, output)
        # Compile and run
        runner = workflow.compile()
        run = await runner.async_run(callback=NodeMonitoringCallback())

        # Store the session
        self.current_session = WorkflowSession(runner=runner, run=run)

        return run

    def cleanup(self):
        if self.current_session:
            self.current_session.run.cancel()
            self.current_session = None


# Global workflow manager instance
workflow_manager = WorkflowManager()
