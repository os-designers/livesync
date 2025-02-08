from __future__ import annotations

import struct
from typing import Any, Literal
from fractions import Fraction

import numpy as np
from numpy.typing import NDArray

from .base_frame import BaseFrame

SAMPLE_WIDTH_MAP = {
    "float32": 4,
    "int16": 2,
    "int32": 4,
    "uint8": 1,
}


class AudioFrame(BaseFrame):
    """Audio frame representation supporting various sample formats and channel layouts.

    Parameters
    ----------
    sample_rate : int
        The sampling rate in Hz.
    num_channels : int
        Number of audio channels (1 for mono, 2 for stereo).
    sample_format : str
        Audio sample format ('float32', 'int16', 'int32', or 'uint8').
    channel_layout : str
        Channel configuration ('mono' or 'stereo').
    data : NDArray[np.number[Any]]
        Audio samples as a 2D numpy array (samples x channels).
    pts : int | None
        Presentation timestamp. If None, `timestamp_ms` or automatic timestamp generation is used.
    time_base : Fraction | None
        Time base of the audio stream. Must be provided together with pts unless timestamp_ms is provided.
    timestamp_ms : int | None
        Timestamp in milliseconds. If provided, it is used (with time_base) to compute pts.
        If both pts and time_base are provided but timestamp_ms is also given, pts is recomputed
        from the given timestamp_ms and time_base.
        In the absence of both, the timestamp is auto-generated using current system time.
    Raises
    ------
    ValueError
        If audio data dimensions, channels, sample rate, format, or layout are invalid.
    """

    def __init__(
        self,
        sample_rate: int,
        num_channels: int,
        sample_format: str,
        channel_layout: str,
        data: NDArray[np.number[Any]],
        pts: int | None = None,
        time_base: Fraction | None = None,
        timestamp_ms: int | None = None,
    ) -> None:
        super().__init__(
            frame_type="audio",
            data=data,
            pts=pts,
            time_base=time_base,
            timestamp_ms=timestamp_ms,
        )

        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.sample_format = sample_format
        self.channel_layout = channel_layout

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

    def tobytes(self) -> bytes:
        """Convert the audio frame to bytes for network transmission.

        Returns
        -------
        bytes
            Serialized audio frame data containing metadata and samples.
        """
        # Pack time_base if it exists
        time_base_bytes = (
            b"\x01" + struct.pack(">II", self.time_base.numerator, self.time_base.denominator)
            if self.time_base
            else b"\x00"
        )

        # Pack metadata into bytes
        metadata = (
            self.sample_rate.to_bytes(4, "big")
            + self.num_channels.to_bytes(2, "big")
            + self.sample_format.encode()
            + b"\x00"  # null-terminated string
            + self.channel_layout.encode()
            + b"\x00"  # null-terminated string
            + struct.pack(">d", self.pts)
            + time_base_bytes
        )

        # Convert audio data to bytes efficiently
        audio_bytes = self.data.tobytes()

        return metadata + audio_bytes

    @classmethod
    def frombytes(cls, buffer: bytes) -> "AudioFrame":
        """Create an AudioFrame instance from bytes.

        Parameters
        ----------
        buffer : bytes
            Serialized audio frame data.

        Returns
        -------
        AudioFrame
            New instance created from the byte data.
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

        # Extract timestamp (pts)
        pts_start = layout_end + 1
        pts = struct.unpack(">d", buffer[pts_start : pts_start + 8])[0]

        # Extract time_base if present
        time_base_start = pts_start + 8
        has_time_base = buffer[time_base_start] == 1
        if has_time_base:
            num, den = struct.unpack(">II", buffer[time_base_start + 1 : time_base_start + 9])
            time_base = Fraction(num, den)
            audio_data_start = time_base_start + 9
        else:
            time_base = None
            audio_data_start = time_base_start + 1

        # Map sample format to numpy dtype
        dtype_map = {
            "float32": np.float32,
            "int16": np.int16,
            "int32": np.int32,
            "uint8": np.uint8,
        }

        # Extract and reshape audio data
        audio_data = np.frombuffer(buffer[audio_data_start:], dtype=dtype_map[sample_format])
        if audio_data.ndim == 1 and num_channels > 1:
            audio_data = audio_data.reshape(-1, num_channels)

        # Note: Here we pass pts and time_base as extracted from the metadata.
        return cls(
            sample_rate=sample_rate,
            num_channels=num_channels,
            sample_format=sample_format,
            data=audio_data,
            pts=int(pts),
            time_base=time_base,
            channel_layout=channel_layout,
        )

    @property
    def sample_width(self) -> int:
        return SAMPLE_WIDTH_MAP[self.sample_format]

    def __repr__(self) -> str:
        time_val = self.pts * float(self.time_base) if self.time_base else self.pts
        return f"AudioFrame(time={time_val})"
