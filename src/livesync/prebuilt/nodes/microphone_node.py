import time
import asyncio
from logging import getLogger

import numpy as np
import pyaudio  # type: ignore

from ...core.nodes import Node
from ...core.fields import Field
from ...core.frames import AudioFrame

logger = getLogger(__name__)


class MicrophoneNode(Node):
    """A node that captures audio from a microphone device."""

    device_id: int | None = Field(default=None, description="The device ID of the microphone")
    sample_rate: int = Field(default=44100, description="The sample rate of the microphone")
    channels: int | None = Field(
        default=None, description="The number of channels of the microphone. If None, uses maximum available channels"
    )
    chunk_size: int = Field(default=1024, description="The size of the audio chunks to capture")
    sample_format: str = Field(default="int16", description="The sample format of the microphone")

    def bootstrap(self) -> None:
        """Initializes the audio capture."""
        self._audio = pyaudio.PyAudio()
        self._stream: pyaudio.Stream | None = None
        self._loop = asyncio.get_event_loop()

        # Get device info
        if self.device_id is None:
            info = self._audio.get_default_input_device_info()
            self.device_id = int(info["index"])
        else:
            info = self._audio.get_device_info_by_index(self.device_id)

        # Set sample rate based on device capabilities if not specified
        supported_sample_rate = int(info["defaultSampleRate"])
        self.sample_rate = self.sample_rate or supported_sample_rate

        # Set channels based on device capabilities if not specified
        supported_channels = int(info["maxInputChannels"])
        self.channels = self.channels or supported_channels

        # Set channel layout based on number of channels
        self._channel_layout = "mono" if self.channels == 1 else "stereo"

        self._stream = self._audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index=self.device_id,
        )

    def step(self) -> AudioFrame:  # type: ignore[override]
        """Captures audio from the microphone and puts it into the queue."""
        if not self._stream or not self.channels:
            raise RuntimeError("Audio stream is not initialized")

        try:
            data = self._stream.read(self.chunk_size)
        except IOError as e:
            logger.error(f"Error reading from audio stream: {e}")
            raise

        current_time = time.time()

        audio_data = np.frombuffer(data, dtype=np.int16).reshape(-1, self.channels)
        audio_frame = AudioFrame(
            data=audio_data,
            sample_rate=self.sample_rate,
            num_channels=self.channels,
            sample_format=self.sample_format,
            channel_layout=self._channel_layout,
            timestamp_us=int(current_time * 1_000_000),
        )
        return audio_frame

    def shutdown(self) -> None:
        """Stops the audio stream and releases resources."""
        try:
            if self._stream and self._stream.is_active():
                self._stream.stop_stream()
                self._stream.close()
        except Exception as e:
            logger.error(f"Error during stream shutdown: {e}")
        finally:
            if self._audio:
                self._audio.terminate()
