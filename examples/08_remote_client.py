import livesync as ls
from livesync import layers

if __name__ == "__main__":
    # Example: Remote Layer for Frame Processing (Part 2 of 2) - Client
    #
    # ●  (f2): Records processed frames to MP4 file
    # │
    # ●  (f1): Processes frames on remote server (grayscale conversion)
    # │
    # ◇  (x): Captures frames from webcam (device 0)
    #

    x = layers.WebcamInput(fps=30, device_id=1)

    f1 = layers.RemoteLayer(endpoint="localhost:50051")
    f2 = layers.VideoRecorderLayer(filename="./examples/output.mp4")

    y = f2(f1(x))

    sync = ls.Sync(inputs=[x], outputs=[y])
    with sync.compile() as runner:
        runner.run(continuous=True, callback=ls.StreamMonitoringCallback())
