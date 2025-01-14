from livesync.graphs import Graph
from livesync.nodes.presets import WebcamNode, FrameRateNode, ResolutionNode
from livesync.nodes.presets.livesync import ProcessorConfig, LivesyncRemoteNode

from .monitor import NodeMonitor
from ..gui.main_window import MainWindow

_WEBCAM_DEVICE_ID = 0
_WEBCAM_FPS = 30
_TARGET_RESOLUTION = 360  # 360p
_LOCAL_TARGET_FPS = 20
_REMOTE_TARGET_FPS = 5
_REMOTE_ENDPOINT = "localhost:50051"


async def init_graph(window: MainWindow) -> Graph:
    # Create the graph
    monitor = NodeMonitor(window=window)
    graph = Graph()

    # Add nodes
    video_input = WebcamNode(device_id=_WEBCAM_DEVICE_ID, fps=_WEBCAM_FPS, id="webcam", callback_handler=monitor)
    resolution = ResolutionNode(target_height=_TARGET_RESOLUTION, id="resolution", callback_handler=monitor)
    frame_rate = FrameRateNode(target_fps=_LOCAL_TARGET_FPS, id="frame_rate_local", callback_handler=monitor)

    # Add nodes
    graph.add_node(video_input)
    graph.add_node(frame_rate)
    graph.add_node(resolution)

    # Add edges
    graph.add_edge(video_input, frame_rate)
    graph.add_edge(frame_rate, resolution)
    return graph


async def on_node_replace_requested(graph: Graph, window: MainWindow):
    monitor = NodeMonitor(window=window)

    # Try to find local node first
    old_node = graph.get_node_by_id("frame_rate_local")
    is_local_to_remote = bool(old_node)

    if not old_node:
        # If local node not found, try to find remote node
        old_node = graph.get_node_by_id("frame_rate_remote")
        if not old_node:
            raise ValueError("Neither local nor remote frame rate node found in graph")

    # Create appropriate new node based on the transition type
    new_node: LivesyncRemoteNode | FrameRateNode
    if is_local_to_remote:
        # new_node = FrameRateNode(target_fps=3, id="frame_rate_remote", callback_handler=monitor)
        new_node = LivesyncRemoteNode(
            endpoints=[_REMOTE_ENDPOINT],
            configs=[ProcessorConfig(name="frame_rate", settings={"target_fps": str(_REMOTE_TARGET_FPS)})],
            id="frame_rate_remote",
            callback_handler=monitor,
        )
    else:
        new_node = FrameRateNode(target_fps=_LOCAL_TARGET_FPS, id="frame_rate_local", callback_handler=monitor)

    await graph.replace_node(old_node, new_node)
    window.update_graph(graph)
