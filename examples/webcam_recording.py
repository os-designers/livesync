from __future__ import annotations

from livesync import Graph
from livesync.prebuilt.nodes import WebcamNode, FrameRateNode, VideoRecorderNode
from livesync.prebuilt.callbacks import NodeMonitoringCallback

if __name__ == "__main__":
    # Example: WebcamNode Recording
    #
    #   (X) => (Y) => (Z)
    #
    # Node X captures video frames from the webcam
    # Node Y drops frames to achieve a target FPS
    # Node Z records the video frames to a file

    workflow = Graph()

    node_x = WebcamNode(name="webcam", device_id=0, fps=30)
    node_y = FrameRateNode(name="frame_rate", fps=10)
    node_z = VideoRecorderNode(name="video_recorder", filename="./output.mp4", fps=10)

    workflow.add_node(node_x)
    workflow.add_node(node_y)
    workflow.add_node(node_z)

    workflow.add_edge(node_x, node_y)
    workflow.add_edge(node_y, node_z)

    with workflow.compile() as runner:
        try:
            run = runner.run(callback=NodeMonitoringCallback())
            print(run)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt: Stopping runner.")
