from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any
from fractions import Fraction

import numpy as np
from numpy.typing import NDArray


class BaseFrame(ABC):
    """Abstract base class for frame representation.

    Provides common functionality and interface for all frame types.

    The frame's timestamp can be provided in two or three ways:

    1. By providing a (pts, time_base) pair. In this case, if no timestamp_ms is supplied,
       the millisecond timestamp will be computed as
           int(round(pts * float(time_base) * 1000)).
    2. By providing a `timestamp_ms` value. When timestamp_ms is provided:
         - If time_base is omitted, it defaults to Fraction(1, 1000).
         - The presentation timestamp (`pts`) is computed as
             int(round( (timestamp_ms / 1000) / float(time_base) ))
         - Any provided value for `pts` will be overridden.
    3. If neither are provided, the timestamp is automatically generated using the current
       system time in microseconds. In that case, pts is set to the microsecond value
       (with time_base Fraction(1, 1000000)) and timestamp_ms is computed accordingly.
    """

    def __init__(
        self,
        frame_type: str,
        data: NDArray[np.number[Any]],
        pts: int | None = None,
        time_base: Fraction | None = None,
        timestamp_ms: int | None = None,
    ):
        self.frame_type = frame_type
        self.data = data

        # Enforce: if pts is provided it must come with time_base.
        if pts is not None and time_base is None:
            raise ValueError("If pts is provided, time_base must also be provided.")

        if timestamp_ms is not None:
            # Use the provided timestamp_ms as the primary timestamp.
            self.timestamp_ms = timestamp_ms
            # Use the given time_base or fall back to 1/1000 if omitted.
            self.time_base = time_base if time_base is not None else Fraction(1, 1000)
            # Compute pts from timestamp_ms and the effective time_base.
            self.pts = int(round((timestamp_ms / 1000) / float(self.time_base)))
        else:
            # No explicit timestamp_ms provided.
            if pts is not None and time_base is not None:
                self.pts = pts
                self.time_base = time_base
                self.timestamp_ms = int(round(pts * float(time_base) * 1000))
            else:
                # Auto generate timestamp using current time in microseconds.
                auto = int(time.time() * 1000000)
                self.pts = auto
                self.time_base = Fraction(1, 1000000)
                self.timestamp_ms = int(round(auto * float(self.time_base) * 1000))

        if self.pts < 0:
            raise ValueError("PTS cannot be negative")

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

    def __bytes__(self) -> bytes:
        """Convert frame to bytes using tobytes() method.

        This allows using bytes(frame) syntax.

        Returns:
            bytes: The serialized frame data
        """
        return self.tobytes()
