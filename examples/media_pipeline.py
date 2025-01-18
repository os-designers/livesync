from __future__ import annotations

from livesync import Graph
from livesync.prebuilt.nodes import WebcamNode, MediaSyncNode, MicrophoneNode
from livesync.prebuilt.callbacks import LoggingCallback

if __name__ == "__main__":
    # Example: Media pipeline
    #
    #   (X) ---\
    #           => (Z)
    #   (Y) ---/
    #
    # Node X captures video frames
    # Node Y captures audio frames
    # Node Z syncs them

    workflow = Graph()

    node_x = WebcamNode(name="webcam", fps=5)
    node_y = MicrophoneNode(name="microphone", sample_rate=44100, chunk_size=1024)
    node_z = MediaSyncNode(
        name="sync",
        buffer_size=30,
        max_sync_threshold_us=5000,
        audio_node=node_y.name,
        video_node=node_x.name,
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
            print("\nKeyboardInterrupt: Stopping cycle runner.")
