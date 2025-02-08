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


def test_video_frame_pts_timebase():
    """
    Test creating a VideoFrame with pts and time_base supplied.
    The timestamp_ms should be computed from pts and time_base.
    Also verify that serialized and deserialized frames match.
    """
    width, height = 320, 240
    buffer_type = "rgba"
    data = np.zeros((height, width, 4), dtype=np.uint8)
    pts = 150
    time_base = Fraction(1, 1000)  # Each pts tick is 1 ms.
    vf = VideoFrame(width, height, buffer_type, data, pts=pts, time_base=time_base)

    expected_timestamp_ms = int(round(pts * float(time_base) * 1000))  # Expected 150 ms.
    assert vf.timestamp_ms == expected_timestamp_ms
    assert vf.pts == pts

    # Test serialization and deserialization.
    serialized = vf.tobytes()
    vf2 = VideoFrame.frombytes(serialized)
    assert vf2.width == vf.width
    assert vf2.height == vf.height
    assert vf2.buffer_type == vf.buffer_type
    assert np.array_equal(vf2.data, vf.data)
    assert vf2.pts == vf.pts
    assert vf2.time_base == vf.time_base


def test_video_frame_timestamp_ms_only():
    """
    Test creating a VideoFrame with only timestamp_ms provided.
    The default time_base should be Fraction(1, 1000).
    pts should be computed from timestamp_ms accordingly.
    """
    width, height = 640, 480
    buffer_type = "rgb24"  # A 3-channel format.
    data = np.zeros((height, width, 3), dtype=np.uint8)
    timestamp_ms = 200
    vf = VideoFrame(width, height, buffer_type, data, timestamp_ms=timestamp_ms)

    # With no time_base provided, it should default to Fraction(1, 1000).
    assert vf.time_base == Fraction(1, 1000)
    expected_pts = int(round((timestamp_ms / 1000) / float(Fraction(1, 1000))))  # Expected 200.
    assert vf.pts == expected_pts
    assert vf.timestamp_ms == timestamp_ms


def test_video_frame_both_pts_timestamp_ms():
    """
    Test that when both pts and timestamp_ms are provided,
    the timestamp_ms is used to determine pts.
    """
    width, height = 100, 100
    buffer_type = "bgra"
    data = np.zeros((height, width, 4), dtype=np.uint8)
    pts_provided = 999  # This should be overridden.
    timestamp_ms = 500
    time_base = Fraction(1, 50)  # float value 0.02.
    vf = VideoFrame(width, height, buffer_type, data, pts=pts_provided, time_base=time_base, timestamp_ms=timestamp_ms)

    expected_pts = int(round((timestamp_ms / 1000) / float(time_base)))  # Expected: round(0.5/0.02)=25.
    assert vf.timestamp_ms == timestamp_ms
    assert vf.pts == expected_pts


def test_audio_frame_pts_timebase():
    """
    Test creating an AudioFrame with pts and time_base.
    Verify that timestamp_ms is computed from pts, and the serialization round-trip works.
    """
    sample_rate = 44100
    num_channels = 2
    sample_format = "int16"
    channel_layout = "stereo"
    data = np.zeros((1000, num_channels), dtype=np.int16)
    pts = 300
    time_base = Fraction(1, 1000)
    af = AudioFrame(sample_rate, num_channels, sample_format, channel_layout, data, pts=pts, time_base=time_base)

    expected_timestamp_ms = int(round(pts * float(time_base) * 1000))  # Expected 300 ms.
    assert af.timestamp_ms == expected_timestamp_ms
    assert af.pts == pts

    # Test serialization and deserialization.
    serialized = af.tobytes()
    af2 = AudioFrame.frombytes(serialized)
    assert af2.sample_rate == af.sample_rate
    assert af2.num_channels == af.num_channels
    assert af2.sample_format == af.sample_format
    assert af2.channel_layout == af.channel_layout
    assert np.array_equal(af2.data, af.data)
    assert af2.pts == af.pts
    assert af2.time_base == af.time_base


def test_audio_frame_timestamp_ms_only():
    """
    Test creating an AudioFrame with only timestamp_ms provided.
    The default time_base should be Fraction(1, 1000), and pts computed accordingly.
    """
    sample_rate = 48000
    num_channels = 1
    sample_format = "float32"
    channel_layout = "mono"
    data = np.zeros((500, num_channels), dtype=np.float32)
    timestamp_ms = 250
    af = AudioFrame(sample_rate, num_channels, sample_format, channel_layout, data, timestamp_ms=timestamp_ms)
    assert af.time_base == Fraction(1, 1000)
    expected_pts = int(round((timestamp_ms / 1000) / float(Fraction(1, 1000))))  # Expected 250.
    assert af.pts == expected_pts
    assert af.timestamp_ms == timestamp_ms


def test_audio_frame_both_pts_timestamp_ms():
    """
    Test that when both pts and timestamp_ms are provided to AudioFrame,
    the timestamp_ms is the primary source for pts.
    """
    sample_rate = 32000
    num_channels = 2
    sample_format = "int32"
    channel_layout = "stereo"
    data = np.zeros((800, num_channels), dtype=np.int32)
    pts_provided = 800  # Should be overridden.
    timestamp_ms = 400
    time_base = Fraction(1, 50)  # float value 0.02, so expected pts = round(0.4/0.02)=20.
    af = AudioFrame(
        sample_rate,
        num_channels,
        sample_format,
        channel_layout,
        data,
        pts=pts_provided,
        time_base=time_base,
        timestamp_ms=timestamp_ms,
    )

    expected_pts = int(round((timestamp_ms / 1000) / float(time_base)))
    assert af.timestamp_ms == timestamp_ms
    assert af.pts == expected_pts


def test_auto_generated_timestamp_video():
    """
    Test that when no timestamp parameters are provided for VideoFrame,
    the auto-generated timestamps are positive and correctly computed.
    """
    width, height = 200, 200
    buffer_type = "rgba"
    data = np.zeros((height, width, 4), dtype=np.uint8)
    vf = VideoFrame(width, height, buffer_type, data)
    # Auto-generated pts should be positive.
    assert vf.pts > 0
    expected_timestamp_ms = int(round(vf.pts * float(vf.time_base) * 1000))
    assert vf.timestamp_ms == expected_timestamp_ms


def test_auto_generated_timestamp_audio():
    """
    Test that when no timestamp parameters are provided for AudioFrame,
    the auto-generated timestamps are positive and correctly computed.
    """
    sample_rate = 44100
    num_channels = 2
    sample_format = "int16"
    channel_layout = "stereo"
    data = np.zeros((1000, num_channels), dtype=np.int16)
    af = AudioFrame(sample_rate, num_channels, sample_format, channel_layout, data)
    assert af.pts > 0
    expected_timestamp_ms = int(round(af.pts * float(af.time_base) * 1000))
    assert af.timestamp_ms == expected_timestamp_ms
