from typing import Literal

import cv2

from ..._utils.logs import logger
from ...frames.video_frame import VideoFrame
from ..core.callable_layer import CallableLayer


class VideoQualityControlLayer(CallableLayer[VideoFrame, VideoFrame | None]):
    """A layer that adjusts video quality based on predefined quality presets."""

    QUALITY_PRESETS = {
        "4K": (3840, 2160),  # UHD (Ultra HD)
        "2K": (2560, 1440),  # QHD (Quad HD)
        "1080p": (1920, 1080),  # FHD (Full HD)
        "720p": (1280, 720),  # HD (High Definition)
        "480p": (854, 480),  # SD (Standard Definition)
        "360p": (640, 360),  # nHD (Near HD)
        "240p": (426, 240),  # WQVGA (Wide QVGA)
        "144p": (256, 144),  # QQVGA (Quarter-QVGA)
    }

    def __init__(
        self,
        quality: Literal["4K", "2K", "1080p", "720p", "480p", "360p", "240p", "144p"] = "720p",
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        if quality not in self.QUALITY_PRESETS:
            raise ValueError(f"Invalid quality setting: {quality}. Choose from {list(self.QUALITY_PRESETS.keys())}")

        self.quality = quality
        self._quality_preset = self.QUALITY_PRESETS[quality]

    async def call(self, x: VideoFrame) -> VideoFrame | None:
        """Resizes the frame while preserving its aspect ratio."""
        try:
            preset_width, preset_height = self._quality_preset
            downscaled = cv2.resize(x.data, (preset_width, preset_height), interpolation=cv2.INTER_AREA)  # type: ignore

            upscaled = cv2.resize(downscaled, (x.width, x.height), interpolation=cv2.INTER_LINEAR)  # type: ignore

            video_frame = VideoFrame(
                data=upscaled,  # type: ignore
                pts=x.pts,
                width=x.width,
                height=x.height,
                buffer_type=x.buffer_type,
            )
            return video_frame
        except Exception as e:
            logger.error(f"Error during quality control: {e}")
            return None
