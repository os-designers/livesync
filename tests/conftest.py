from __future__ import annotations

import logging

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
    """Provides a mock frame for testing."""
    return AudioFrame(
        data=sample_audio_data,
        timestamp_us=1000000,
        sample_rate=44100,
        num_channels=2,
        sample_format="float32",
        channel_layout="stereo",
    )


@pytest.fixture
def mock_video_frame(sample_video_data: NDArray[np.uint8]) -> VideoFrame:
    """Provides a mock video frame for testing."""
    return VideoFrame(
        data=sample_video_data,
        timestamp_us=1000000,
        width=1280,
        height=720,
        buffer_type="uint8",
    )
