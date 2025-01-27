import livesync as ls
from livesync import layers

if __name__ == "__main__":
    # Example: Webcam Recording Pipeline
    #
    # ●  (f2): Records processed frames to MP4 file
    # │
    # ●  (f1): Controls frame rate of the stream
    # │
    # ◇  (x): Captures frames from webcam (device 0)
    #

    x = ls.WebcamInput(device_id=0, fps=30)

    f1 = layers.FpsControlLayer(fps=10)
    f2 = layers.VideoRecorderLayer(filename="./examples/output.mp4")

    h = f1(x)
    y = f2(h)

    sync = ls.Sync(inputs=[x], outputs=[y])
    with sync.compile() as runner:
        runner.run(callback=ls.LoggingCallback())
