import asyncio
from unittest.mock import AsyncMock

import numpy as np
import pytest
from numpy.typing import NDArray

from livesync.frames.audio_frame import AudioFrame
from livesync.nodes.presets.livekit import LiveKitAudioSourceNode


class MockAudioFrame:
    """Mock for LiveKit AudioFrame."""

    def __init__(self, samples_per_channel: int, num_channels: int, sample_rate: int, data: bytes):
        self.samples_per_channel = samples_per_channel
        self.num_channels = num_channels
        self.sample_rate = sample_rate
        self.data = data


class MockFrameEvent:
    """Mock for LiveKit FrameEvent."""

    def __init__(self, frame: MockAudioFrame, timestamp_us: int):
        self.frame = frame
        self.timestamp_us = timestamp_us


class MockAudioStream:
    """Mock for LiveKit AudioStream."""

    def __init__(self, frame_events: list[MockFrameEvent]):
        self.frame_events = frame_events
        self.aclose = AsyncMock()
        self._iterator = self._create_iterator()

    async def _create_iterator(self):
        for event in self.frame_events:
            yield event

    def __aiter__(self):
        return self._iterator


class TestLiveKitAudioSourceNode:
    @pytest.fixture
    def sample_audio_data(self) -> NDArray[np.int16]:
        """Create sample audio data for testing."""
        return np.random.randint(-32768, 32767, (1024, 2), dtype=np.int16)

    @pytest.fixture
    def mock_audio_stream(self, sample_audio_data: NDArray[np.int16]):
        """Create a mock audio stream with predefined frame events."""
        frame_events: list[MockFrameEvent] = []
        base_time = 1000000

        # Create 3 frame events
        for i in range(3):
            frame = MockAudioFrame(
                samples_per_channel=1024, num_channels=2, sample_rate=48000, data=sample_audio_data.tobytes()
            )
            event = MockFrameEvent(frame=frame, timestamp_us=base_time + (i * 21333))  # ~46.875ms intervals
            frame_events.append(event)

        return MockAudioStream(frame_events)

    @pytest.mark.asyncio
    async def test_source_frames_output(self, mock_audio_stream: MockAudioStream, sample_audio_data: NDArray[np.int16]):
        """Test that source frames are correctly converted and yielded."""
        node = LiveKitAudioSourceNode(livekit_stream=mock_audio_stream)  # type: ignore

        frames_received: list[AudioFrame] = []
        async for frame in node._source_frames():
            frames_received.append(frame)
            if len(frames_received) >= 3:  # Collect 3 frames
                break

        assert len(frames_received) == 3

        # Verify first frame properties
        first_frame = frames_received[0]
        assert isinstance(first_frame, AudioFrame)
        assert first_frame.num_channels == 2
        assert first_frame.sample_rate == 48000
        assert first_frame.sample_format == "int16"
        assert first_frame.channel_layout == "stereo"
        assert np.array_equal(first_frame.data, sample_audio_data)

    @pytest.mark.asyncio
    async def test_stop_source(self, mock_audio_stream: MockAudioStream):
        """Test that stop_source properly closes the LiveKit stream."""
        node = LiveKitAudioSourceNode(livekit_stream=mock_audio_stream)  # type: ignore

        await node._stop_source()
        mock_audio_stream.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_source_node_lifecycle(self, mock_audio_stream: MockAudioStream):
        """Test the complete lifecycle of the LiveKit source node."""
        node = LiveKitAudioSourceNode(livekit_stream=mock_audio_stream)  # type: ignore

        # Test startup
        await node.start()
        await asyncio.sleep(0.1)  # Give some time for processing

        assert node._source_task is not None
        assert node._is_running

        # Test shutdown
        await node.stop()
        assert not node._is_running
        assert node._source_task is None
        mock_audio_stream.aclose.assert_called_once()
