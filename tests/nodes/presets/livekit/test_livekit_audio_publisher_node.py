from unittest.mock import Mock, AsyncMock

import numpy as np
import pytest
from livekit import rtc  # type: ignore
from numpy.typing import NDArray

from livesync.frames.audio_frame import AudioFrame
from livesync.nodes.presets.livekit import LiveKitAudioPublisherNode


class TestLiveKitAudioPublisherNode:
    @pytest.fixture
    def mock_livekit_source(self):
        """Create a mock LiveKit audio source."""
        source = Mock(spec=rtc.AudioSource)
        source.capture_frame = AsyncMock()
        source.clear_queue = Mock()
        return source

    @pytest.fixture
    def sample_audio_frame(self) -> AudioFrame:
        """Create a sample audio frame for testing."""
        # Create 1 second of stereo audio at 48kHz
        samples = 48000
        audio_data: NDArray[np.float32] = np.random.rand(samples, 2).astype(np.float32)

        return AudioFrame(
            sample_rate=48000,
            num_channels=2,
            sample_format="float32",
            channel_layout="stereo",
            data=audio_data,
            timestamp_us=1000000,
        )

    @pytest.mark.asyncio
    async def test_process_frame(self, mock_livekit_source: Mock, sample_audio_frame: AudioFrame):
        """Test that audio frames are correctly processed and sent to LiveKit."""
        node = LiveKitAudioPublisherNode(livekit_source=mock_livekit_source)

        # Process the frame
        await node.process_frame(sample_audio_frame)

        # Verify that capture_frame was called
        mock_livekit_source.capture_frame.assert_called_once()

        # Verify the LiveKit frame properties
        called_frame = mock_livekit_source.capture_frame.call_args[0][0]
        assert isinstance(called_frame, rtc.AudioFrame)
        assert called_frame.sample_rate == sample_audio_frame.sample_rate
        assert called_frame.num_channels == sample_audio_frame.num_channels
        assert called_frame.samples_per_channel == len(sample_audio_frame.data)

        # Verify the audio data was converted to bytes
        assert bytes(called_frame.data) == sample_audio_frame.data.tobytes()

    @pytest.mark.asyncio
    async def test_cleanup(self, mock_livekit_source: Mock, sample_audio_frame: AudioFrame):
        """Test that the node properly cleans up resources."""
        node = LiveKitAudioPublisherNode(livekit_source=mock_livekit_source)

        # Start and process a frame
        await node.start()
        await node.process_frame(sample_audio_frame)

        # Stop the node
        await node.stop()

        # Verify cleanup
        mock_livekit_source.clear_queue.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_frames(self, mock_livekit_source: Mock):
        """Test processing multiple audio frames."""
        node = LiveKitAudioPublisherNode(livekit_source=mock_livekit_source)

        # Create multiple frames with different data
        frames: list[AudioFrame] = []
        for i in range(3):
            audio_data: NDArray[np.float32] = np.random.rand(1000, 2).astype(np.float32)
            frame = AudioFrame(
                sample_rate=48000,
                num_channels=2,
                sample_format="float32",
                channel_layout="stereo",
                data=audio_data,
                timestamp_us=1000000 + i * 1000,
            )
            frames.append(frame)

        # Process all frames
        for frame in frames:
            await node.process_frame(frame)

        # Verify number of calls
        assert mock_livekit_source.capture_frame.call_count == len(frames)

        # Verify each frame was processed correctly
        for i, call_args in enumerate(mock_livekit_source.capture_frame.call_args_list):
            lk_frame = call_args[0][0]
            assert isinstance(lk_frame, rtc.AudioFrame)
            assert lk_frame.sample_rate == frames[i].sample_rate
            assert lk_frame.num_channels == frames[i].num_channels
            assert bytes(lk_frame.data) == frames[i].data.tobytes()

    @pytest.mark.asyncio
    async def test_mono_audio(self, mock_livekit_source: Mock):
        """Test processing mono audio frames."""
        node = LiveKitAudioPublisherNode(livekit_source=mock_livekit_source)

        # Create mono audio frame
        audio_data: NDArray[np.float32] = np.random.rand(1000, 1).astype(np.float32)
        mono_frame = AudioFrame(
            sample_rate=44100,
            num_channels=1,
            sample_format="float32",
            channel_layout="mono",
            data=audio_data,
            timestamp_us=1000000,
        )

        # Process the frame
        await node.process_frame(mono_frame)

        # Verify the LiveKit frame properties
        called_frame = mock_livekit_source.capture_frame.call_args[0][0]
        assert called_frame.num_channels == 1
        assert called_frame.samples_per_channel == len(mono_frame.data)
