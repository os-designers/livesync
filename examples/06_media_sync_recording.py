import livesync as ls
from livesync import layers

if __name__ == "__main__":
    # Example: Media Synchronization Recording Pipeline
    #
    # ●  (f2): Records processed frames to MP4 file
    # │
    # ○  (f1): Synchronizes video and audio frames
    # │
    # ○  (u): Merges webcam and microphone streams
    # │
    # ○──●  (wait for any stream)
    # │  │
    # │  ●  (f1): Delays audio frames by 2 second
    # │  │
    # │  ◇  (x2): Captures audio frames from microphone
    # │
    # ◇  (x1): Captures frames from webcam
    #

    # x1 = ls.WebcamInput(device_id=0, fps=30)
    # x2 = ls.MicrophoneInput(sample_rate=44100, chunk_size=1024)

    # f1 = layers.DelayLayer(interval=3)
    # f2 = layers.MediaSynchronizerLayer(buffer_size=1024, max_threshold=0.005)  # 5ms
    # # f3 = layers.MediaRecorderLayer(filename="./examples/output.mp4")

    # h = f1(x2)
    # u = layers.Merge([x1, h], how="outer")

    # y = f2(u)

    # sync = ls.Sync(inputs=[x1, x2], outputs=[y])
    # with sync.compile() as runner:
    #     runner.run(callback=ls.LoggingCallback())

    x1 = ls.WebcamInput(device_id=0, fps=30)
    x2 = ls.MicrophoneInput(sample_rate=44100, chunk_size=1024)

    f1 = layers.DelayLayer(interval=3)
    f2 = layers.MediaSynchronizerLayer(buffer_size=1024, max_delay=0.1, sync_tolerance=0.05)  # 5ms
    f3 = layers.VideoRecorderLayer(filename="./examples/output.mp4")
    f4 = layers.AudioRecorderLayer(filename="./examples/output.wav")

    h1 = f2(f1(x1))
    h2 = f2(x2)

    y1 = f3(h1)
    y2 = f4(h2)

    sync = ls.Sync(inputs=[x1, x2], outputs=[y1, y2])
    with sync.compile() as runner:
        runner.run(callback=ls.StreamMonitoringCallback())
