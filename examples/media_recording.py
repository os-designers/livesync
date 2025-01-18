from __future__ import annotations

from livesync import Graph
from livesync.prebuilt.nodes import WebcamNode, MicrophoneNode, MediaRecorderNode
from livesync.prebuilt.callbacks import LoggingCallback

if __name__ == "__main__":
    # Example: Media Recording
    #
    #   (X) ---\
    #           => (Z)
    #   (Y) ---/
    #
    # Node X captures video frames from the webcam
    # Node Y captures audio frames from the microphone
    # Node Z records the video and audio frames to a file

    workflow = Graph()

    node_x = WebcamNode(name="webcam", fps=30)
    node_y = MicrophoneNode(name="microphone", sample_rate=44100, chunk_size=1024)
    node_z = MediaRecorderNode(
        name="media_recorder",
        filename="./output.mp4",
        video_node=node_x.name,
        audio_node=node_y.name,
        fps=30,
    )

    workflow.add_node(node_x)
    workflow.add_node(node_y)
    workflow.add_node(node_z)

    workflow.add_edge(node_x, node_z)
    workflow.add_edge(node_y, node_z)

    with workflow.compile() as runner:
        try:
            run = runner.run(callback=LoggingCallback())
            print(run)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt: Stopping runner.")
