from __future__ import annotations

from livesync import Graph
from livesync.prebuilt.nodes import MicrophoneNode, AudioRecorderNode
from livesync.prebuilt.callbacks import LoggingCallback

if __name__ == "__main__":
    # Example: MicrophoneNode Recording
    #
    #   (X) => (Y) => (Z)
    #
    # Node X captures audio frames from the microphone
    # Node Y records the audio frames to a file

    workflow = Graph()

    node_x = MicrophoneNode(name="microphone", sample_rate=44100, chunk_size=1024)
    node_y = AudioRecorderNode(name="audio_recorder", filename="./output.mp3")

    workflow.add_node(node_x)
    workflow.add_node(node_y)

    workflow.add_edge(node_x, node_y)

    with workflow.compile() as runner:
        try:
            run = runner.run(callback=LoggingCallback())
            print(run)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt: Stopping runner.")
