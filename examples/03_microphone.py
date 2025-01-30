import livesync as ls
from livesync import layers

if __name__ == "__main__":
    # Example: MicrophoneNode Recording Pipeline
    #
    # ●  (f): Records audio frames to MP3 file
    # │
    # ◇  (x): Captures audio frames from microphone
    #

    x = ls.MicrophoneInput(name="microphone", sample_rate=44100, chunk_size=1024)
    f = layers.AudioRecorderLayer(
        name="audio_recorder",
        filename="./examples/output.wav",
    )

    y = f(x)
    sync = ls.Sync(inputs=[x], outputs=[y])

    with sync.compile() as runner:
        runner.run(callback=ls.LoggingCallback())
