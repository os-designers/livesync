import os
import wave
import asyncio

import numpy as np

from ..._utils.logs import logger
from ...frames.audio_frame import AudioFrame
from ..core.callable_layer import CallableLayer

EXT_TO_FORMAT = {
    "wav": "int16",
    "flac": "int16",
    "ogg": "float32",
    "pcm": "int16",
}


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
        self._lock = asyncio.Lock()
        ext = os.path.splitext(filename)[-1][1:].lower()
        self.sample_format = EXT_TO_FORMAT.get(ext, "int16")

    async def call(self, x: AudioFrame) -> None:
        """Receives audio frames and writes them to the file."""
        try:
            async with self._lock:
                if self._writer is None:
                    self._writer = wave.open(self.filename, "wb")
                    self._writer.setnchannels(x.num_channels)
                    self._writer.setsampwidth(x.sample_width)
                    self._writer.setframerate(x.sample_rate)

                # Convert data to appropriate format for WAV file
                data = x.data
                if self.sample_format == "float32":
                    data = (x.data * 32767).astype(np.int16)  # Normalize float32 to int16
                else:
                    data = x.data.astype(np.int16)

                self._writer.writeframes(data.tobytes())
        except Exception as e:
            logger.error(f"Error writing audio frame to file: {e}")

    async def cleanup(self) -> None:
        """Finalizes the file writing process."""
        async with self._lock:
            if self._writer is not None:
                self._writer.close()
                self._writer = None  # Reset writer
