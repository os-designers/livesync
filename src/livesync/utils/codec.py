from pathlib import Path

import cv2


def get_video_codec(filename: str) -> int:
    """
    Determines the appropriate video codec based on the file extension.

    Args:
        filename: Path to the video file

    Returns:
        OpenCV fourcc codec code
    """
    ext = Path(filename).suffix.lower()
    return {
        ".mp4": cv2.VideoWriter.fourcc(*"mp4v"),
        ".avi": cv2.VideoWriter.fourcc(*"XVID"),
        ".mov": cv2.VideoWriter.fourcc(*"mp4v"),
    }.get(ext, cv2.VideoWriter.fourcc(*"mp4v"))  # default to mp4v
