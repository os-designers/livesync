from typing import Literal
from dataclasses import dataclass
from typing_extensions import override

import numpy as np

from .base_frame import BaseFrame

BufferType = Literal["rgba", "abgr", "argb", "bgra", "rgb24", "i420", "i420a", "i422", "i444", "i010", "nv12"]
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
    buffer_type: BufferType

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
            buffer_type: BufferType = buffer[8:buffer_type_end].decode()  # type: ignore

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
