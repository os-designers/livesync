import wave
import asyncio
from logging import getLogger

import pyaudio  # type: ignore

from ...core.nodes import Node
from ...core.fields import Field
from ...core.frames import AudioFrame

logger = getLogger(__name__)


class AudioRecorderNode(Node):
    """A node that records audio frames to a file."""

    filename: str = Field(default=..., description="Path to the output audio file")

    def bootstrap(self) -> None:
        """Initializes the audio file writer."""
        if len(self.parents) != 1:
            raise ValueError("AudioRecorderNode must have a single parent")

        self._parent_node = self.parents[0]
        self._writer = None
        self._recording: bool = False
        self._lock = asyncio.Lock()

    async def step(self):
        """Receives audio frames and writes them to the file."""
        frame: AudioFrame = await self.get_input(self._parent_node.name)

        async with self._lock:
            if self._writer is None:
                self._writer = wave.open(self.filename, "wb")
                self._writer.setnchannels(frame.num_channels)
                self._writer.setsampwidth(pyaudio.get_sample_size(pyaudio.paFloat32))
                self._writer.setframerate(frame.sample_rate)

            self._writer.writeframes(frame.data.tobytes())

    async def shutdown(self):
        """Finalizes the file writing process."""
        self._recording = False
        async with self._lock:
            if self._writer is not None:
                self._writer.close()
                self._writer = None  # Reset writer
