from livesync.graphs import Graph
from livesync.nodes.presets import WebcamNode, FrameRateNode, ResolutionNode

# from livesync.nodes.presets.livesync import LivesyncRemoteNode, ProcessorConfig
from .monitor import NodeMonitor
from ..gui.main_window import MainWindow

_WEBCAM_DEVICE_ID = 0
_WEBCAM_FPS = 30
_TARGET_RESOLUTION = 480  # 480p
_TARGET_FRAME_RATE = 5


async def create_graph(window: MainWindow):
    # Create the graph
    monitor = NodeMonitor(window=window)
    graph = Graph()

    # Add nodes
    video_input = WebcamNode(device_id=_WEBCAM_DEVICE_ID, fps=_WEBCAM_FPS, id="webcam", callback_handler=monitor)
    resolution = ResolutionNode(target_height=_TARGET_RESOLUTION, id="resolution", callback_handler=monitor)

    # Option 1. Local frame rate node
    frame_rate = FrameRateNode(target_fps=_TARGET_FRAME_RATE, id="frame_rate", callback_handler=monitor)

    # Option 2. Remote frame rate node
    # frame_rate = LivesyncRemoteNode(
    #     endpoints=["localhost:50051"],
    #     configs=[ProcessorConfig(name="frame_rate", settings={"target_fps": "5"})],
    #     id="frame_rate_remote_node",
    #     callback_handler=monitor,
    # )

    # Add nodes
    graph.add_node(video_input)
    graph.add_node(frame_rate)
    graph.add_node(resolution)

    # Add edges
    graph.add_edge(video_input, frame_rate)
    graph.add_edge(frame_rate, resolution)

    # Update the window
    window.update_graph(graph)
    return graph
