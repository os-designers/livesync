from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal
from dataclasses import field, dataclass
from typing_extensions import override

import numpy as np
from numpy.typing import NDArray


@dataclass
class BaseFrame(ABC):
    """Abstract base class for frame representation.

    Provides common functionality and interface for all frame types.
    """

    frame_type: str = field(init=False)
    data: NDArray[np.number[Any]]
    timestamp_us: int

    def __post_init__(self) -> None:
        """Validate frame data after initialization."""
        if self.timestamp_us < 0:
            raise ValueError("Timestamp cannot be negative")

    @abstractmethod
    def tobytes(self) -> bytes:
        """Serialize the frame to bytes.

        Returns:
            bytes: The serialized frame data
        """
        pass

    @classmethod
    @abstractmethod
    def frombytes(cls, buffer: bytes) -> BaseFrame:
        """Deserialize bytes to a Frame.

        Args:
            buffer: Raw bytes to deserialize

        Returns:
            BaseFrame: A new frame instance
        """
        pass


@dataclass
class AudioFrame(BaseFrame):
    """Audio frame representation supporting various sample formats and channel layouts."""

    sample_rate: int
    num_channels: int
    sample_format: str
    channel_layout: str  # "mono" or "stereo"
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
        sample_format = buffer[6:format_end].decode()  # type: ignore

        # Extract channel layout string
        layout_start = format_end + 1
        layout_end = buffer.index(b"\x00", layout_start)
        channel_layout = buffer[layout_start:layout_end].decode()  # type: ignore

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


BUFFER_FORMAT_CHANNELS = {
    "rgba": 4,
    "abgr": 4,
    "argb": 4,
    "bgra": 4,  # 4-channel formats
    "rgb24": 3,  # 3-channel formats
    "i420": 1,
    "i420a": 1,
    "i422": 1,
    "i444": 1,  # YUV formats
}


@dataclass
class VideoFrame(BaseFrame):
    """Video frame representation supporting various color formats."""

    width: int
    height: int
    buffer_type: str

    @override
    def __post_init__(self) -> None:
        """Validate video frame data after initialization."""
        super().__post_init__()

        if self.data.ndim != 3:
            raise ValueError("Video data must be 3-dimensional (height, width, channels)")
        if (
            self.buffer_type not in BUFFER_FORMAT_CHANNELS
            or BUFFER_FORMAT_CHANNELS[self.buffer_type] != self.data.shape[2]
        ):
            raise ValueError(f"Invalid buffer type or channel count: {self.buffer_type}")

        self.frame_type = "video"

    @override
    def tobytes(self) -> bytes:
        """Serialize the video frame to bytes for network transmission."""
        try:
            # Pack metadata into bytes
            metadata = (
                self.width.to_bytes(4, "big")
                + self.height.to_bytes(4, "big")
                + self.buffer_type.encode()
                + b"\x00"  # null-terminated string
                + self.timestamp_us.to_bytes(8, "big")
            )

            # Convert frame data to bytes efficiently
            frame_bytes = self.data.tobytes()

            return metadata + frame_bytes
        except Exception as e:
            raise ValueError(f"Failed to serialize video frame: {e}") from e

    @override
    @classmethod
    def frombytes(cls, buffer: bytes) -> "VideoFrame":
        """Deserialize bytes to create a new VideoFrame instance."""
        try:
            # Extract metadata
            width = int.from_bytes(buffer[0:4], "big")
            height = int.from_bytes(buffer[4:8], "big")

            # Extract buffer type string
            buffer_type_end = buffer.index(b"\x00", 8)
            buffer_type = buffer[8:buffer_type_end].decode()  # type: ignore

            # Extract timestamp
            timestamp_start = buffer_type_end + 1
            timestamp_us = int.from_bytes(buffer[timestamp_start : timestamp_start + 8], "big")

            # Extract and reshape frame data
            frame_data = np.frombuffer(buffer[timestamp_start + 8 :], dtype=np.uint8)
            channels = 4 if buffer_type in ["rgba", "abgr", "argb", "bgra"] else 3
            frame_data = frame_data.reshape(height, width, channels)

            return cls(
                data=frame_data,
                timestamp_us=timestamp_us,
                width=width,
                height=height,
                buffer_type=buffer_type,
            )
        except Exception as e:
            raise ValueError(f"Failed to deserialize video frame: {e}") from e

    @override
    def __repr__(self) -> str:
        return (
            f"VideoFrame(width={self.width}, "
            f"height={self.height}, "
            f"buffer_type={self.buffer_type}, "
            f"timestamp_us={self.timestamp_us}, "
            f"data_shape={self.data.shape})"
        )
