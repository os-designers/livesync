import wave
import asyncio

import pyaudio  # type: ignore

from ..._utils.logs import logger
from ...frames.audio_frame import AudioFrame
from ..core.callable_layer import CallableLayer


class AudioRecorderLayer(CallableLayer[AudioFrame, None]):
    """A node that records audio frames to a file.

    Parameters
    ----------
    filename : str
        Path to the output audio file
    """

    def __init__(self, filename: str, name: str | None = None) -> None:
        super().__init__(name=name)
        self.filename = filename

        self._writer: wave.Wave_write | None = None
        self._recording: bool = False
        self._lock = asyncio.Lock()

    async def call(self, x: AudioFrame) -> None:
        """Receives audio frames and writes them to the file."""
        try:
            async with self._lock:
                if self._writer is None:
                    self._writer = wave.open(self.filename, "wb")
                    self._writer.setnchannels(x.num_channels)
                    self._writer.setsampwidth(pyaudio.get_sample_size(pyaudio.paFloat32))
                    self._writer.setframerate(x.sample_rate)

                self._writer.writeframes(x.data.tobytes())
        except Exception as e:
            logger.error(f"Error writing audio frame to file: {e}")

    async def cleanup(self) -> None:
        """Finalizes the file writing process."""
        self._recording = False
        async with self._lock:
            if self._writer is not None:
                self._writer.close()
                self._writer = None  # Reset writer
