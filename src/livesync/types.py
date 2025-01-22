from typing import Any

from numpy.typing import NDArray

from .frames.audio_frame import AudioFrame
from .frames.video_frame import VideoFrame

MediaFrameType = VideoFrame | AudioFrame
DataType = NDArray[Any] | str | float | int | bool | MediaFrameType
StreamDataType = DataType | dict[str, MediaFrameType] | tuple[MediaFrameType | None, ...]
