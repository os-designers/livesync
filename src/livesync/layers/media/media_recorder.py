import os
import wave
import asyncio
import tempfile
import subprocess
from logging import getLogger

import av
import numpy as np
import av.container

from ...types import MediaFrameType
from ..._utils.logs import logger
from ...frames.video_frame import VideoFrame
from ..core.callable_layer import CallableLayer

logger = getLogger(__name__)


class MediaRecorderLayer(CallableLayer[MediaFrameType | dict[str, MediaFrameType], None]):
    """A layer that records both video and audio frames to a single media file.

    Parameters
    ----------
    filename : str
        Path to the output media file
    codec : str, default="h264"
        Codec to use for the output video
    """

    def __init__(self, filename: str, codec: str = "h264", name: str | None = None) -> None:
        super().__init__(name=name)
        self.filename = filename
        self.codec = codec

        self._temp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        self._temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self._video_container: av.container.OutputContainer | None = None
        self._video_stream: av.VideoStream | None = None
        self._audio_writer: wave.Wave_write | None = None
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
                    if self._video_container is None:
                        self._video_container = av.open(self._temp_video.name, mode="w")
                        self._video_stream = self._video_container.add_stream(self.codec)  # type: ignore
                        self._video_stream.width = frame.width  # type: ignore
                        self._video_stream.height = frame.height  # type: ignore
                        self._video_stream.pix_fmt = "yuv420p"  # type: ignore

                    # Write video frame
                    av_frame = av.VideoFrame.from_ndarray(frame.data, format=frame.buffer_type)  # type: ignore
                    av_frame.pts = frame.pts
                    packet = self._video_stream.encode(av_frame)  # type: ignore
                    self._video_container.mux(packet)  # type: ignore

                else:
                    # Initialize audio writer if not already done
                    if self._audio_writer is None:
                        self._audio_writer = wave.open(self._temp_audio.name, "wb")  # type: ignore
                        self._audio_writer.setnchannels(frame.num_channels)
                        self._audio_writer.setsampwidth(frame.sample_width)
                        self._audio_writer.setframerate(frame.sample_rate)

                    # Convert data to appropriate format for WAV file
                    data = frame.data.astype(np.int16)

                    # Write audio frame
                    self._audio_writer.writeframes(data.tobytes())

        except Exception as e:
            logger.error(f"Error in MediaRecorderNode process: {e}")
            raise

    async def cleanup(self) -> None:
        """Finalizes the recording and merges video and audio."""
        async with self._lock:
            # Close video writer
            if self._video_container is not None and self._video_stream is not None:
                self._video_container.mux(self._video_stream.encode())
                self._video_container.close()
                self._video_container = None
                self._video_stream = None

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
