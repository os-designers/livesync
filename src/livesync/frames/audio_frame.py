from typing import Literal
from dataclasses import field, dataclass
from typing_extensions import override

import numpy as np

from .base_frame import BaseFrame

SampleFormat = Literal["float32", "int16", "int32", "uint8"]
ChannelLayout = Literal["mono", "stereo"]


@dataclass
class AudioFrame(BaseFrame):
    """Audio frame representation supporting various sample formats and channel layouts."""

    sample_rate: int
    num_channels: Literal[1, 2]
    sample_format: SampleFormat
    channel_layout: ChannelLayout
    frame_type: str = field(init=False)

    @override
    def __post_init__(self) -> None:
        """Validate audio frame data after initialization."""
        super().__post_init__()

        if self.data.ndim != 2:
            raise ValueError("Audio data must be 2-dimensional (samples, channels)")
        if self.num_channels not in (1, 2):
            raise ValueError("Audio channels must be 1 (mono) or 2 (stereo)")
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be greater than 0")
        if self.sample_format not in ("float32", "int16", "int32", "uint8"):
            raise ValueError(f"Invalid sample format: {self.sample_format}")
        if self.channel_layout not in ("mono", "stereo"):
            raise ValueError(f"Invalid channel layout: {self.channel_layout}")

        self.frame_type = "audio"

    @override
    def tobytes(self) -> bytes:
        """Convert the audio frame to bytes for network transmission.

        Returns:
            bytes: Serialized audio frame data containing metadata and samples
        """
        # Pack metadata into bytes
        metadata = (
            self.sample_rate.to_bytes(4, "big")
            + self.num_channels.to_bytes(2, "big")
            + self.sample_format.encode()
            + b"\x00"  # null-terminated string
            + self.channel_layout.encode()
            + b"\x00"  # null-terminated string
            + self.timestamp_us.to_bytes(8, "big")
        )

        # Convert audio data to bytes efficiently
        audio_bytes = self.data.tobytes()

        return metadata + audio_bytes

    @override
    @classmethod
    def frombytes(cls, buffer: bytes) -> "AudioFrame":
        """Create an AudioFrame instance from bytes.

        Args:
            data: Serialized audio frame data

        Returns:
            AudioFrame: New instance created from the byte data
        """
        # Extract sample rate and num_channels
        sample_rate = int.from_bytes(buffer[0:4], "big")
        num_channels: Literal[1, 2] = int.from_bytes(buffer[4:6], "big")  # type: ignore

        # Extract sample format string
        format_end = buffer.index(b"\x00", 6)
        sample_format: SampleFormat = buffer[6:format_end].decode()  # type: ignore

        # Extract channel layout string
        layout_start = format_end + 1
        layout_end = buffer.index(b"\x00", layout_start)
        channel_layout: ChannelLayout = buffer[layout_start:layout_end].decode()  # type: ignore

        # Extract timestamp
        timestamp_start = layout_end + 1
        timestamp_us = int.from_bytes(buffer[timestamp_start : timestamp_start + 8], "big")

        # Map sample format to numpy dtype
        dtype_map = {
            "float32": np.float32,
            "int16": np.int16,
            "int32": np.int32,
            "uint8": np.uint8,
        }

        # Extract and reshape audio data
        audio_data = np.frombuffer(buffer[timestamp_start + 8 :], dtype=dtype_map[sample_format])
        if len(audio_data.shape) == 1 and num_channels > 1:
            audio_data = audio_data.reshape(-1, num_channels)

        return cls(
            sample_rate=sample_rate,
            num_channels=num_channels,
            sample_format=sample_format,
            data=audio_data,
            timestamp_us=timestamp_us,
            channel_layout=channel_layout,
        )

    @override
    def __repr__(self) -> str:
        return (
            f"AudioFrame(sample_rate={self.sample_rate}, "
            f"num_channels={self.num_channels}, "
            f"format={self.sample_format}, "
            f"layout={self.channel_layout}, "
            f"timestamp_us={self.timestamp_us}, "
            f"data_shape={self.data.shape})"
        )
