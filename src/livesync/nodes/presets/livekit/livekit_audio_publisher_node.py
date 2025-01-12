from dataclasses import dataclass
from typing_extensions import override

from livekit import rtc  # type: ignore

from ...base_node import BaseNode
from ....frames.audio_frame import AudioFrame


@dataclass
class LiveKitAudioPublisherNode(BaseNode):
    """Sends audio frames to a LiveKit audio source."""

    livekit_source: rtc.AudioSource

    @override
    async def process_frame(self, frame: AudioFrame) -> None:  # type: ignore[override]
        samples_per_channel = frame.data.shape[0]
        lk_frame = rtc.AudioFrame(
            sample_rate=frame.sample_rate,
            num_channels=frame.num_channels,
            samples_per_channel=samples_per_channel,
            data=frame.data.tobytes(),
        )
        await self.livekit_source.capture_frame(lk_frame)

    @override
    async def _before_cleanup(self):
        await super()._before_cleanup()
        self.livekit_source.clear_queue()
