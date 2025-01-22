from __future__ import annotations

import struct
from typing import Any
from fractions import Fraction

import numpy as np
from numpy.typing import NDArray

from .base_frame import BaseFrame

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


class VideoFrame(BaseFrame):
    """Video frame representation supporting various color formats.

    Parameters
    ----------
    width : int
        Frame width in pixels.
    height : int
        Frame height in pixels.
    buffer_type : str
        Color format of the frame data (e.g., 'rgba', 'rgb24', 'i420').
    data : NDArray[np.number[Any]]
        Video frame data as a 3D numpy array (height, width, channels).
    pts : int
        Presentation timestamp in seconds.
    time_base : Fraction | None
        Time base of the video stream.

    Raises
    ------
    ValueError
        If frame dimensions, buffer type, or channel count are invalid.
    """

    def __init__(
        self,
        width: int,
        height: int,
        buffer_type: str,
        data: NDArray[np.number[Any]],
        pts: int,
        time_base: Fraction | None = None,
    ) -> None:
        super().__init__(frame_type="video", data=data, pts=pts, time_base=time_base)

        self.width = width
        self.height = height
        self.buffer_type = buffer_type

        if self.data.ndim != 3:
            raise ValueError("Video data must be 3-dimensional (height, width, channels)")
        if (
            self.buffer_type not in BUFFER_FORMAT_CHANNELS
            or BUFFER_FORMAT_CHANNELS[self.buffer_type] != self.data.shape[2]
        ):
            raise ValueError(f"Invalid buffer type or channel count: {self.buffer_type}")

    def tobytes(self) -> bytes:
        """Serialize the video frame to bytes for network transmission.

        Returns
        -------
        bytes
            Serialized video frame data containing metadata and pixel data.

        Raises
        ------
        ValueError
            If serialization fails.
        """
        try:
            # Pack time_base if it exists
            time_base_bytes = (
                b"\x01" + struct.pack(">II", self.time_base.numerator, self.time_base.denominator)
                if self.time_base
                else b"\x00"
            )

            # Pack metadata into bytes
            metadata = (
                self.width.to_bytes(4, "big")
                + self.height.to_bytes(4, "big")
                + self.buffer_type.encode()
                + b"\x00"  # null-terminated string
                + struct.pack(">d", self.pts)
                + time_base_bytes
            )

            # Convert frame data to bytes efficiently
            frame_bytes = self.data.tobytes()

            return metadata + frame_bytes
        except Exception as e:
            raise ValueError(f"Failed to serialize video frame: {e}") from e

    @classmethod
    def frombytes(cls, buffer: bytes) -> VideoFrame:
        """Create a VideoFrame instance from bytes.

        Parameters
        ----------
        buffer : bytes
            Serialized video frame data.

        Returns
        -------
        VideoFrame
            New instance created from the byte data.

        Raises
        ------
        ValueError
            If deserialization fails.
        """
        try:
            # Extract metadata
            width = int.from_bytes(buffer[0:4], "big")
            height = int.from_bytes(buffer[4:8], "big")

            # Extract buffer type string
            buffer_type_end = buffer.index(b"\x00", 8)
            buffer_type = buffer[8:buffer_type_end].decode()  # type: ignore

            # Extract timestamp
            pts_start = buffer_type_end + 1
            pts = struct.unpack(">d", buffer[pts_start : pts_start + 8])[0]

            # Extract time_base if present
            time_base_start = pts_start + 8
            has_time_base = buffer[time_base_start] == 1
            if has_time_base:
                num, den = struct.unpack(">II", buffer[time_base_start + 1 : time_base_start + 9])
                time_base = Fraction(num, den)
                frame_data_start = time_base_start + 9
            else:
                time_base = None
                frame_data_start = time_base_start + 1

            # Extract and reshape frame data
            frame_data = np.frombuffer(buffer[frame_data_start:], dtype=np.uint8)
            channels = BUFFER_FORMAT_CHANNELS[buffer_type]
            frame_data = frame_data.reshape(height, width, channels)

            return cls(
                data=frame_data,
                pts=pts,
                width=width,
                height=height,
                buffer_type=buffer_type,
                time_base=time_base,
            )
        except Exception as e:
            raise ValueError(f"Failed to deserialize video frame: {e}") from e

    def __repr__(self) -> str:
        return (
            f"VideoFrame(width={self.width}, "
            f"height={self.height}, "
            f"buffer_type={self.buffer_type}, "
            f"pts={self.pts}, "
            f"time_base={self.time_base}, "
            f"data_shape={self.data.shape})"
        )
