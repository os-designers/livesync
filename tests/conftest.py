from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from unittest.mock import AsyncMock
from typing_extensions import override

import numpy as np
import pytest
from numpy.typing import NDArray
from pytest_asyncio import is_async_test

from livesync.nodes.base_node import BaseNode, NodeCallbackHandler
from livesync.frames.base_frame import BaseFrame

pytest.register_assert_rewrite("tests.utils")

logging.getLogger("livesync").setLevel(logging.DEBUG)


# automatically add `pytest.mark.asyncio()` to all of our async tests
# so we don't have to add that boilerplate everywhere
def pytest_collection_modifyitems(items: list[pytest.Function]) -> None:
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:8000")

api_key = os.environ.get("TEST_API_KEY", "test")


@pytest.fixture
def sample_audio_data() -> NDArray[np.float32]:
    """Create sample audio data for testing."""
    return np.random.rand(1024, 2).astype(np.float32)


@pytest.fixture
def sample_video_data() -> NDArray[np.uint8]:
    """Create sample video data for testing."""
    return np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)


@dataclass
class MockFrame(BaseFrame):
    """Mock frame implementation for testing."""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.frame_type = "mock"

    @override
    def tobytes(self) -> bytes:
        metadata = self.frame_type.encode() + b"\x00" + self.timestamp_us.to_bytes(8, "big")
        return metadata + self.data.tobytes()

    @override
    @classmethod
    def frombytes(cls, buffer: bytes) -> "MockFrame":
        type_end = buffer.index(b"\x00")
        timestamp_us = int.from_bytes(buffer[type_end + 1 : type_end + 9], "big")
        data = np.frombuffer(buffer[type_end + 9 :], dtype=np.float32).reshape(-1, 2)
        return cls(data=data, timestamp_us=timestamp_us)


class MockCallbackHandler(NodeCallbackHandler):
    """Mock callback handler for testing."""

    def __init__(self):
        self.on_received = AsyncMock()
        self.on_processed = AsyncMock()

    @override
    async def on_frame_received(self, node: BaseNode, frame: BaseFrame):
        await self.on_received(node, frame)

    @override
    async def on_frame_processed(self, node: BaseNode, frame: BaseFrame):
        await self.on_processed(node, frame)


@pytest.fixture
def mock_frame(sample_audio_data: NDArray[np.float32]) -> MockFrame:
    """Provides a mock frame for testing."""
    return MockFrame(data=sample_audio_data, timestamp_us=1000000)


@pytest.fixture
def callback_handler() -> MockCallbackHandler:
    """Provides a mock callback handler for testing."""
    return MockCallbackHandler()
