from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

from livesync import VideoFrame


def create_black_pixmap(width: int, height: int) -> QPixmap:
    """Creates a black QPixmap of given width and height."""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.black)
    return pixmap


def convert_cv_frame_to_qpixmap(frame: VideoFrame) -> QPixmap:
    """
    Converts a VideoFrame (assuming its `data` is a NumPy array in RGB888)
    to a QPixmap suitable for display.
    """
    img_data = frame.data  # e.g., shape: (H, W, 3)

    h, w, ch = img_data.shape
    bytes_per_line = ch * w
    q_image = QImage(img_data.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(q_image)
