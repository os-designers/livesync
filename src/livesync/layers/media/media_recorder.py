import os
import wave
import asyncio
import tempfile
import subprocess
from logging import getLogger

import cv2
import pyaudio  # type: ignore

from ...types import MediaFrameType
from ..._utils.logs import logger
from ..._utils.codec import get_video_codec
from ...frames.video_frame import VideoFrame
from ..core.callable_layer import CallableLayer

logger = getLogger(__name__)


class MediaRecorderLayer(CallableLayer[MediaFrameType | dict[str, MediaFrameType], None]):
    """A layer that records both video and audio frames to a single media file.

    Parameters
    ----------
    filename : str
        Path to the output media file
    fps : float
        Frames per second for the output video
    """

    def __init__(self, filename: str, fps: float, name: str | None = None) -> None:
        super().__init__(name=name)
        self.filename = filename
        self.fps = fps

        self._temp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        self._temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self._codec = get_video_codec(self.filename)
        self._video_writer = None
        self._audio_writer = None
        self._lock = asyncio.Lock()

    async def call(self, x: MediaFrameType | dict[str, MediaFrameType]) -> None:
        """Receives and writes both video and audio frames."""
        try:
            async with self._lock:
                if isinstance(x, dict):
                    if len(x.values()) != 1:
                        raise ValueError("Expected exactly one stream")
                    frame = next(iter(x.values()))
                else:
                    frame = x

                if isinstance(frame, VideoFrame):
                    # Initialize video writer if not already done
                    if self._video_writer is None:
                        self._video_writer = cv2.VideoWriter(  # type: ignore
                            self._temp_video.name, self._codec, self.fps, (frame.width, frame.height)
                        )

                    # Write video frame
                    bgr_frame_data = cv2.cvtColor(frame.data, cv2.COLOR_RGB2BGR)  # type: ignore
                    self._video_writer.write(bgr_frame_data)  # type: ignore
                else:
                    # Initialize audio writer if not already done
                    if self._audio_writer is None:
                        self._audio_writer = wave.open(self._temp_audio.name, "wb")  # type: ignore
                        self._audio_writer.setnchannels(frame.num_channels)  # type: ignore[attr-defined]
                        self._audio_writer.setsampwidth(pyaudio.get_sample_size(pyaudio.paFloat32))  # type: ignore[attr-defined]
                        self._audio_writer.setframerate(frame.sample_rate)  # type: ignore[attr-defined]

                    # Write audio frame
                    self._audio_writer.writeframes(frame.data.tobytes())  # type: ignore

        except Exception as e:
            logger.error(f"Error in MediaRecorderNode process: {e}")
            raise

    async def cleanup(self) -> None:
        """Finalizes the recording and merges video and audio."""
        async with self._lock:
            # Close video writer
            if self._video_writer is not None:
                self._video_writer.release()  # type: ignore[unreachable]
                self._video_writer = None

            # Close audio writer
            if self._audio_writer is not None:
                self._audio_writer.close()  # type: ignore[unreachable]
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
