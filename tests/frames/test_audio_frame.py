from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

from livesync import AudioFrame


class TestAudioFrame:
    @pytest.fixture
    def valid_audio_params(self) -> dict[str, Any]:
        """Return valid parameters for AudioFrame creation."""
        return {
            "timestamp_us": 1000000,
            "num_channels": 2,
            "sample_rate": 44100,
            "sample_format": "float32",
            "channel_layout": "stereo",
        }

    def test_audio_frame_initialization(
        self, sample_audio_data: NDArray[np.float32], valid_audio_params: dict[str, Any]
    ) -> None:
        """Test successful initialization of AudioFrame with valid parameters."""
        frame = AudioFrame(data=sample_audio_data, **valid_audio_params)

        assert frame.timestamp_us == valid_audio_params["timestamp_us"]
        assert frame.num_channels == valid_audio_params["num_channels"]
        assert frame.sample_rate == valid_audio_params["sample_rate"]
        assert frame.sample_format == valid_audio_params["sample_format"]
        assert frame.channel_layout == valid_audio_params["channel_layout"]
        assert frame.frame_type == "audio"
        np.testing.assert_array_equal(frame.data, sample_audio_data)

    @pytest.mark.parametrize(
        "param,invalid_value,error_pattern",
        [
            ("num_channels", 3, "Audio channels must be 1 \\(mono\\) or 2 \\(stereo\\)"),
            ("sample_rate", -44100, "Sample rate must be greater than 0"),
            ("sample_format", "invalid", "Invalid sample format"),
            ("channel_layout", "invalid", "Invalid channel layout"),
        ],
    )
    def test_audio_frame_validation(
        self,
        sample_audio_data: NDArray[np.float32],
        valid_audio_params: dict[str, Any],
        param: str,
        invalid_value: object,
        error_pattern: str,
    ) -> None:
        """Test validation of AudioFrame parameters."""
        params = valid_audio_params.copy()
        params[param] = invalid_value

        with pytest.raises(ValueError, match=error_pattern):
            AudioFrame(data=sample_audio_data, **params)

    def test_audio_frame_serialization(
        self, sample_audio_data: NDArray[np.float32], valid_audio_params: dict[str, Any]
    ) -> None:
        """Test serialization and deserialization of AudioFrame."""
        original_frame = AudioFrame(data=sample_audio_data, **valid_audio_params)

        serialized = original_frame.tobytes()
        deserialized = AudioFrame.frombytes(serialized)

        # Verify all attributes are preserved
        for attr in valid_audio_params:
            assert getattr(deserialized, attr) == getattr(original_frame, attr)
        np.testing.assert_array_equal(deserialized.data, original_frame.data)
