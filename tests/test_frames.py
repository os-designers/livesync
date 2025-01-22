from __future__ import annotations

from typing import Any
from fractions import Fraction

import numpy as np
import pytest

from livesync import AudioFrame, VideoFrame


def test_audio_frame_serialization(mock_audio_frame: AudioFrame):
    """Test that AudioFrame serialization/deserialization preserves data."""
    # Serialize and deserialize
    frame_bytes = mock_audio_frame.tobytes()
    reconstructed = AudioFrame.frombytes(frame_bytes)

    # Check metadata
    assert reconstructed.sample_rate == mock_audio_frame.sample_rate
    assert reconstructed.num_channels == mock_audio_frame.num_channels
    assert reconstructed.sample_format == mock_audio_frame.sample_format
    assert reconstructed.channel_layout == mock_audio_frame.channel_layout
    assert reconstructed.pts == mock_audio_frame.pts
    assert reconstructed.time_base == mock_audio_frame.time_base

    # Check audio data
    np.testing.assert_array_equal(reconstructed.data, mock_audio_frame.data)


def test_video_frame_serialization(mock_video_frame: VideoFrame):
    """Test that VideoFrame serialization/deserialization preserves data."""
    # Serialize and deserialize
    frame_bytes = mock_video_frame.tobytes()
    reconstructed = VideoFrame.frombytes(frame_bytes)

    # Check metadata
    assert reconstructed.width == mock_video_frame.width
    assert reconstructed.height == mock_video_frame.height
    assert reconstructed.buffer_type == mock_video_frame.buffer_type
    assert reconstructed.pts == mock_video_frame.pts
    assert reconstructed.time_base == mock_video_frame.time_base

    # Check video data
    np.testing.assert_array_equal(reconstructed.data, mock_video_frame.data)


def test_audio_frame_sequence(mock_audio_frames: list[AudioFrame]):
    """Test that a sequence of AudioFrames maintains temporal order."""
    prev_pts = -1
    for frame in mock_audio_frames:
        assert frame.pts > prev_pts
        prev_pts = frame.pts

        # Test serialization for each frame
        frame_bytes = frame.tobytes()
        reconstructed = AudioFrame.frombytes(frame_bytes)
        np.testing.assert_array_equal(reconstructed.data, frame.data)


def test_video_frame_sequence(mock_video_frames: list[VideoFrame]):
    """Test that a sequence of VideoFrames maintains temporal order."""
    prev_pts = -1
    for frame in mock_video_frames:
        assert frame.pts > prev_pts
        prev_pts = frame.pts

        # Test serialization for each frame
        frame_bytes = frame.tobytes()
        reconstructed = VideoFrame.frombytes(frame_bytes)
        np.testing.assert_array_equal(reconstructed.data, frame.data)


@pytest.mark.parametrize(
    "sample_format,dtype",
    [
        ("float32", np.float32),
        ("int16", np.int16),
        ("int32", np.int32),
        ("uint8", np.uint8),
    ],
)
def test_audio_frame_formats(sample_format: str, dtype: np.dtype[Any]):
    """Test AudioFrame with different sample formats."""
    data = np.random.rand(1024, 2).astype(dtype)
    frame = AudioFrame(
        data=data,
        pts=1,
        sample_rate=44100,
        num_channels=2,
        sample_format=sample_format,
        channel_layout="stereo",
        time_base=Fraction(1, 44100),
    )

    frame_bytes = frame.tobytes()
    reconstructed = AudioFrame.frombytes(frame_bytes)
    np.testing.assert_array_equal(reconstructed.data, frame.data)


@pytest.mark.parametrize(
    "buffer_type,channels",
    [
        ("rgb24", 3),
        ("rgba", 4),
        ("bgra", 4),
    ],
)
def test_video_frame_formats(buffer_type: str, channels: int):
    """Test VideoFrame with different buffer types."""
    data = np.random.randint(0, 255, (720, 1280, channels), dtype=np.uint8)
    frame = VideoFrame(
        data=data,
        pts=1,
        width=1280,
        height=720,
        buffer_type=buffer_type,
        time_base=Fraction(1, 30),
    )

    frame_bytes = frame.tobytes()
    reconstructed = VideoFrame.frombytes(frame_bytes)
    np.testing.assert_array_equal(reconstructed.data, frame.data)
