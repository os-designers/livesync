import livesync as ls
from livesync import layers

if __name__ == "__main__":
    # Example: Media Recording
    #
    # ●  (f): Records processed frames to MP4 file
    # │
    # ○  (u): Merges webcam and microphone streams
    # │
    # ○──●  (wait for all streams)
    # │  │
    # │  ●  (x2): Captures audio frames from microphone
    # │
    # ◇  (x1): Captures frames from webcam
    #

    x1 = ls.WebcamInput(device_id=0, fps=30)
    x2 = ls.MicrophoneInput(sample_rate=44100, chunk_size=1024)

    u = layers.Merge([x1, x2], how="outer")
    f = layers.MediaRecorderLayer(filename="./examples/output.mp4")

    y = f(u)

    sync = ls.Sync(inputs=[x1, x2], outputs=[u])
    with sync.compile() as runner:
        runner.run(callback=None)  # ls.StreamMonitoringCallback())
