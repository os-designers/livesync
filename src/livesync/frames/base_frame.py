from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from fractions import Fraction

import numpy as np
from numpy.typing import NDArray


class BaseFrame(ABC):
    """Abstract base class for frame representation.

    Provides common functionality and interface for all frame types.
    """

    def __init__(self, frame_type: str, data: NDArray[np.number[Any]], pts: int, time_base: Fraction | None = None):
        self.frame_type = frame_type
        self.data = data
        self.pts = pts
        self.time_base = time_base

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
