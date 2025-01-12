from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

from livesync import VideoFrame


class TestVideoFrame:
    @pytest.fixture
    def valid_video_params(self) -> dict[str, Any]:
        """Return valid parameters for VideoFrame creation."""
        return {
            "timestamp_us": 1000000,
            "width": 1280,
            "height": 720,
            "buffer_type": "rgb24",
        }

    def test_video_frame_initialization(
        self, sample_video_data: NDArray[np.uint8], valid_video_params: dict[str, Any]
    ) -> None:
        """Test successful initialization of VideoFrame with valid parameters."""
        frame = VideoFrame(data=sample_video_data, **valid_video_params)

        assert frame.timestamp_us == valid_video_params["timestamp_us"]
        assert frame.width == valid_video_params["width"]
        assert frame.height == valid_video_params["height"]
        assert frame.buffer_type == valid_video_params["buffer_type"]
        assert frame.frame_type == "video"
        np.testing.assert_array_equal(frame.data, sample_video_data)

    @pytest.mark.parametrize(
        "buffer_type,channels",
        [
            ("rgba", 4),
            ("rgb24", 3),
            ("bgra", 4),
        ],
    )
    def test_video_frame_buffer_types(
        self,
        buffer_type: str,
        channels: int,
        valid_video_params: dict[str, Any],
    ) -> None:
        """Test different buffer types and their corresponding channel counts."""
        data = np.random.randint(0, 255, (720, 1280, channels), dtype=np.uint8)
        params = valid_video_params.copy()
        params["buffer_type"] = buffer_type

        frame = VideoFrame(data=data, **params)
        assert frame.buffer_type == buffer_type
        assert frame.data.shape[-1] == channels

    def test_video_frame_serialization(
        self, sample_video_data: NDArray[np.uint8], valid_video_params: dict[str, Any]
    ) -> None:
        """Test serialization and deserialization of VideoFrame."""
        original_frame = VideoFrame(data=sample_video_data, **valid_video_params)

        serialized = original_frame.tobytes()
        deserialized = VideoFrame.frombytes(serialized)

        # Verify all attributes are preserved
        for attr in valid_video_params:
            assert getattr(deserialized, attr) == getattr(original_frame, attr)
        np.testing.assert_array_equal(deserialized.data, original_frame.data)

    def test_invalid_buffer_type(
        self, sample_video_data: NDArray[np.uint8], valid_video_params: dict[str, Any]
    ) -> None:
        """Test rejection of invalid buffer types."""
        params = valid_video_params.copy()
        params["buffer_type"] = "invalid"

        with pytest.raises(ValueError, match="Invalid buffer type or channel count"):
            VideoFrame(data=sample_video_data, **params)
