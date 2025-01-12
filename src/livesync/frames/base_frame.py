from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
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

    @override
    def __repr__(self) -> str:
        return f"Frame(type={self.frame_type}, timestamp_us={self.timestamp_us}, data_shape={self.data.shape})"
