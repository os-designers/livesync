from typing import Any

from numpy.typing import NDArray

from .frames.audio_frame import AudioFrame
from .frames.video_frame import VideoFrame

NumberType = int | float
MediaFrameType = VideoFrame | AudioFrame
DataType = NDArray[Any] | bytes | str | NumberType | MediaFrameType
BytesableType = bytes | str | NumberType | MediaFrameType
StreamDataType = (
    DataType
    | MediaFrameType
    | dict[str, MediaFrameType]
    | dict[str, MediaFrameType | None]
    | dict[str, tuple[AudioFrame | VideoFrame, float] | None]
    | tuple[MediaFrameType | None, ...]
)
