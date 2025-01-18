import os
import wave
import asyncio
import tempfile
import subprocess
from logging import getLogger

import cv2
import pyaudio  # type: ignore

from ...core.nodes import Node
from ...core.fields import Field
from ...core.frames import AudioFrame, VideoFrame
from ...utils.codec import get_video_codec

logger = getLogger(__name__)


class MediaRecorderNode(Node):
    """A node that records both video and audio frames to a single media file."""

    filename: str = Field(default=..., description="Path to the final output media file (e.g., output.mp4)")
    fps: float = Field(default=30.0, description="Frames per second for the output video")
    video_node: str = Field(default=..., description="Name of the video parent node")
    audio_node: str = Field(default=..., description="Name of the audio parent node")

    def bootstrap(self) -> None:
        """Initializes the video and audio writers."""
        if len(self.parents) != 2:
            raise ValueError("MediaRecorderNode must have exactly two parents (video and audio)")

        # Create temporary files
        self._temp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        self._temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self._codec = get_video_codec(self.filename)
        self._video_writer = None
        self._audio_writer = None
        self._lock = asyncio.Lock()

    async def step(self):
        """Receives and writes both video and audio frames."""
        video_frame: VideoFrame = await self.get_input(self.video_node)
        audio_frame: AudioFrame = await self.get_input(self.audio_node)

        async with self._lock:
            if self._video_writer is None:
                self._video_writer = cv2.VideoWriter(
                    self._temp_video.name, self._codec, self.fps, (video_frame.width, video_frame.height)
                )

            bgr_frame_data = cv2.cvtColor(video_frame.data, cv2.COLOR_RGB2BGR)  # type: ignore
            self._video_writer.write(bgr_frame_data)  # type: ignore

            # Handle audio
            if self._audio_writer is None:
                self._audio_writer = wave.open(self._temp_audio.name, "wb")
                self._audio_writer.setnchannels(audio_frame.num_channels)
                self._audio_writer.setsampwidth(pyaudio.get_sample_size(pyaudio.paFloat32))
                self._audio_writer.setframerate(audio_frame.sample_rate)

            self._audio_writer.writeframes(audio_frame.data.tobytes())

    async def shutdown(self):
        """Finalizes the recording and merges video and audio."""
        async with self._lock:
            # Close video writer
            if self._video_writer is not None:
                self._video_writer.release()
                self._video_writer = None

            # Close audio writer
            if self._audio_writer is not None:
                self._audio_writer.close()
                self._audio_writer = None

            # Merge video and audio using FFmpeg
            try:
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    self._temp_video.name,
                    "-i",
                    self._temp_audio.name,
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    self.filename,
                ]
                subprocess.run(cmd, check=True)
                logger.info(f"Successfully merged video and audio to {self.filename}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to merge video and audio: {e}")
            finally:
                # Cleanup temporary files
                for temp_file in [self._temp_video.name, self._temp_audio.name]:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except OSError as e:
                        logger.error(f"Failed to remove temporary file {temp_file}: {e}")
