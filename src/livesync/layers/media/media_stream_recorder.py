import asyncio
from fractions import Fraction

import av
import av.container

from ...types import MediaFrameType
from ..._utils.logs import logger
from ...frames.video_frame import VideoFrame
from ..core.callable_layer import CallableLayer


class MediaStreamRecorderLayer(CallableLayer[MediaFrameType | dict[str, MediaFrameType], None]):
    """A layer that records both video and audio frames to a single media file using PyAV.

    Parameters
    ----------
    filename : str
        Path to the output media file (e.g., 'output.mp4').
    """

    def __init__(self, filename: str, audio_format: str = "flt", name: str | None = None) -> None:
        super().__init__(name=name)
        self.filename = filename
        self.audio_format = audio_format

        self._lock = asyncio.Lock()
        self._container: av.container.OutputContainer | None = None
        self._video_stream: av.VideoStream | None = None
        self._audio_stream: av.AudioStream | None = None

        logger.warning(
            "This layer can record either video or audio streams, but not both simultaneously. "
            "You must choose to record either video frames or audio frames - attempting to record "
            "both types at the same time is not supported."
        )

    async def _init_container(self) -> None:
        """Initializes the PyAV container if not already initialized."""
        if self._container is not None:
            return

        try:
            self._container = av.open(self.filename, mode="w")
        except Exception as e:
            logger.error(f"Failed to open container for writing: {e}")
            raise

    async def _init_video_stream(self, width: int, height: int, time_base: Fraction) -> None:
        """Initializes the video stream once the first video frame is received."""
        await self._init_container()
        if self._video_stream is not None:
            return

        # Define a video stream using H.264 codec
        fps = int(1 / float(time_base))
        self._video_stream = self._container.add_stream("libx264", rate=fps)  # type: ignore
        self._video_stream.width = width  # type: ignore
        self._video_stream.height = height  # type: ignore
        self._video_stream.pix_fmt = "yuv420p"  # type: ignore
        self._video_stream.time_base = time_base  # type: ignore

        logger.info(f"Initialized video stream: {width}x{height} at {fps} FPS")

    async def _init_audio_stream(self, sample_rate: int, num_channels: int, time_base: Fraction) -> None:
        """Initializes the audio stream once the first audio frame is received."""
        await self._init_container()
        if self._audio_stream is not None:
            return

        self._audio_stream = self._container.add_stream("aac", rate=sample_rate)  # type: ignore
        self._audio_stream.bit_rate = 128_000
        self._audio_stream.layout = "stereo" if num_channels == 2 else "mono"
        self._audio_stream.format = self.audio_format
        self._audio_stream.time_base = time_base

        logger.info(f"Initialized audio stream: {sample_rate} Hz, {num_channels} channels")

    async def call(self, x: MediaFrameType | dict[str, MediaFrameType]) -> None:
        """Processes incoming video/audio frames and writes them to the output file."""
        async with self._lock:
            # If input is a dictionary, extract the single frame inside
            if isinstance(x, dict):
                if len(x) != 1:
                    raise ValueError("Expected exactly one stream in the dictionary")
                frame = next(iter(x.values()))
            else:
                frame = x

            # 1) Process Video Frame
            if isinstance(frame, VideoFrame):
                # Initialize the video stream when the first frame arrives
                if not self._video_stream and frame.time_base:
                    await self._init_video_stream(frame.width, frame.height, frame.time_base)

                if not self._video_stream or not self._container:
                    logger.error("Video stream not initialized properly.")
                    return

                # Create a PyAV VideoFrame from the numpy array
                av_frame = av.VideoFrame.from_ndarray(frame.data, format=frame.buffer_type)  # type: ignore
                av_frame.pts = frame.pts  # type: ignore

                for packet in self._video_stream.encode(av_frame):
                    self._container.mux(packet)

            # 2) Process Audio Frame
            else:
                sample_rate = frame.sample_rate
                num_channels = frame.num_channels

                # Initialize the audio stream when the first audio frame arrives
                if not self._audio_stream and frame.time_base:
                    await self._init_audio_stream(sample_rate, num_channels, frame.time_base)

                if not self._audio_stream or not self._container:
                    logger.error("Audio stream not initialized properly.")
                    return

                # Convert numpy array to PyAV AudioFrame
                av_audio_frame = av.AudioFrame.from_ndarray(
                    frame.data.T,  # type: ignore
                    format=self.audio_format,
                    layout=frame.channel_layout,  # type: ignore
                )
                av_audio_frame.sample_rate = sample_rate
                av_audio_frame.pts = frame.pts  # type: ignore

                for packet in self._audio_stream.encode(av_audio_frame):
                    self._container.mux(packet)

    async def cleanup(self) -> None:
        """Finalizes the recording and closes the container properly."""
        async with self._lock:
            # Flush remaining video frames
            if self._video_stream and self._container:
                for packet in self._video_stream.encode(None):
                    self._container.mux(packet)

            # Flush remaining audio frames
            if self._audio_stream and self._container:
                for packet in self._audio_stream.encode(None):
                    self._container.mux(packet)

            # Close the output container
            if self._container:
                self._container.close()
                self._container = None

            logger.info(f"Recording finalized: {self.filename}")
