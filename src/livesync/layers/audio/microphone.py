import time
import asyncio
from typing import AsyncIterator
from logging import getLogger
from fractions import Fraction

import numpy as np
import pyaudio  # type: ignore

from ..._utils.logs import logger
from ..core.input_layer import InputLayer
from ...frames.audio_frame import AudioFrame

logger = getLogger(__name__)


class MicrophoneInput(InputLayer[AudioFrame]):
    """A layer that captures audio from a microphone device.

    Parameters
    ----------
    device_id : int, default=None
        The device ID of the microphone
    sample_rate : int, default=44100
        The sample rate of the microphone
    channels : int, default=None
        The number of channels of the microphone. If None, uses maximum available channels
    chunk_size : int, default=1024
        The size of the audio chunks to capture
    """

    def __init__(
        self,
        device_id: int | None = None,
        sample_rate: int = 44100,
        channels: int | None = None,
        chunk_size: int = 1024,
        sample_format: str = "int16",
        name: str | None = None,
    ):
        """Initializes the audio capture."""
        super().__init__(dtype=AudioFrame, name=name)
        self.device_id = device_id
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.sample_format = sample_format

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

        format_map = {
            "float32": pyaudio.paFloat32,
            "int16": pyaudio.paInt16,
            "int32": pyaudio.paInt32,
            "uint8": pyaudio.paUInt8,
        }

        self._stream = self._audio.open(
            format=format_map[self.sample_format],
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index=self.device_id,
        )
        self._time_base = Fraction(1, self.sample_rate)

    async def aiter(self) -> AsyncIterator[AudioFrame]:
        """Captures audio from the microphone.

        Yields
        ------
        AudioFrame
            Audio frames captured from the microphone

        Raises
        ------
        RuntimeError
            If audio stream is not initialized
        """
        start_time = time.time()

        while True:
            try:
                if not self._stream or not self.channels:
                    raise RuntimeError("Audio stream is not initialized")

                try:
                    data = self._stream.read(self.chunk_size)
                except IOError as e:
                    logger.error(f"Error reading from audio stream: {e}")
                    raise

                current_time = time.time()

                pts = int((current_time - start_time) / self._time_base)

                dtype_map = {
                    "float32": np.float32,
                    "int16": np.int16,
                    "int32": np.int32,
                    "uint8": np.uint8,
                }

                audio_data = np.frombuffer(data, dtype=dtype_map[self.sample_format]).reshape(-1, self.channels)
                audio_frame = AudioFrame(
                    data=audio_data,
                    sample_rate=self.sample_rate,
                    num_channels=self.channels,
                    sample_format=self.sample_format,
                    channel_layout=self._channel_layout,
                    pts=pts,
                    time_base=self._time_base,
                )
                yield audio_frame
                await asyncio.sleep(0)
            except Exception as e:
                logger.error(f"Error capturing audio frame: {e}")
                raise

    async def cleanup(self) -> None:
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
