from typing_extensions import override

import numpy as np
import pytest

from livesync.frames import BaseFrame


class MockFrame(BaseFrame):
    """Mock implementation of BaseFrame for testing."""

    @override
    def tobytes(self) -> bytes:
        return b""

    @override
    @classmethod
    def frombytes(cls, buffer: bytes) -> "BaseFrame":
        return cls(data=np.array([]), timestamp_us=0)


class TestBaseFrame:
    def test_negative_timestamp_validation(self) -> None:
        """Test that negative timestamps are rejected."""
        with pytest.raises(ValueError, match="Timestamp cannot be negative"):
            MockFrame(data=np.array([]), timestamp_us=-1)

    def test_repr_format(self) -> None:
        """Test the string representation of the frame."""
        frame = MockFrame(data=np.array([[1, 2], [3, 4]]), timestamp_us=1000)
        frame.frame_type = "mock"
        expected = "Frame(type=mock, timestamp_us=1000, data_shape=(2, 2))"
        assert repr(frame) == expected
