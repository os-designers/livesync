import time
from typing import AsyncIterator
from dataclasses import dataclass
from typing_extensions import override

import numpy as np
from livekit import rtc  # type: ignore

from ...source_node import SourceNode
from ....frames.audio_frame import AudioFrame


@dataclass
class LiveKitAudioSourceNode(SourceNode):
    """Captures audio from a LiveKit stream."""

    livekit_stream: rtc.AudioStream

    @override
    async def _source_frames(self) -> AsyncIterator[AudioFrame]:  # type: ignore[override]
        """Captures audio frames from the LiveKit stream."""
        async for frame_event in self.livekit_stream:
            lk_frame = frame_event.frame
            frame_data = np.frombuffer(lk_frame.data, dtype=np.int16).reshape(
                (lk_frame.samples_per_channel, lk_frame.num_channels)
            )
            audio_frame = AudioFrame(
                data=frame_data,
                timestamp_us=int(time.time() * 1_000_000),
                sample_rate=lk_frame.sample_rate,
                num_channels=lk_frame.num_channels,  # type: ignore
                sample_format="int16",
                channel_layout="stereo",
            )
            yield audio_frame

    @override
    async def _stop_source(self):
        """Stops the node and closes the LiveKit stream."""
        await self.livekit_stream.aclose()
