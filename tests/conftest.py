from __future__ import annotations

import logging
from fractions import Fraction

import numpy as np
import pytest
from numpy.typing import NDArray
from pytest_asyncio import is_async_test

from livesync import AudioFrame, VideoFrame

pytest.register_assert_rewrite("tests.utils")

logging.getLogger("livesync").setLevel(logging.DEBUG)


# automatically add `pytest.mark.asyncio()` to all of our async tests
# so we don't have to add that boilerplate everywhere
def pytest_collection_modifyitems(items: list[pytest.Function]) -> None:
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture
def sample_audio_data() -> NDArray[np.float32]:
    """Create sample audio data for testing."""
    return np.random.rand(1024, 2).astype(np.float32)


@pytest.fixture
def sample_video_data() -> NDArray[np.uint8]:
    """Create sample video data for testing."""
    return np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def mock_audio_frame(sample_audio_data: NDArray[np.float32]) -> AudioFrame:
    """Provides a mock audio frame for testing."""
    return AudioFrame(
        data=sample_audio_data,
        pts=1,
        sample_rate=44100,
        num_channels=2,
        sample_format="float32",
        channel_layout="stereo",
        time_base=Fraction(1, 44100),
    )


@pytest.fixture
def mock_video_frame(sample_video_data: NDArray[np.uint8]) -> VideoFrame:
    """Provides a mock video frame for testing."""
    return VideoFrame(
        data=sample_video_data,
        pts=1,
        width=1280,
        height=720,
        buffer_type="rgb24",
        time_base=Fraction(1, 30),
    )


@pytest.fixture
def mock_audio_frames() -> list[AudioFrame]:
    """Provides a sequence of mock audio frames for testing."""
    frames: list[AudioFrame] = []
    for i in range(5):
        data = np.random.rand(1024, 2).astype(np.float32)
        frame = AudioFrame(
            data=data,
            pts=i,
            sample_rate=44100,
            num_channels=2,
            sample_format="float32",
            channel_layout="stereo",
            time_base=Fraction(1, 44100),
        )
        frames.append(frame)
    return frames


@pytest.fixture
def mock_video_frames() -> list[VideoFrame]:
    """Provides a sequence of mock video frames for testing."""
    frames: list[VideoFrame] = []
    for i in range(5):
        data = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        frame = VideoFrame(
            data=data,
            pts=i,
            width=1280,
            height=720,
            buffer_type="rgb24",
            time_base=Fraction(1, 30),
        )
        frames.append(frame)
    return frames
