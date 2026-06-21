import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QWidget

_log = logging.getLogger("barkoder.window")


class DogWindow(QWidget):
    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(136, 136)
        self._frame: QPixmap | None = None

    def set_frame(self, frame) -> None:
        if frame is None:
            self._frame = None
        else:
            _log.debug("frame %dx%d → %dx%d", frame.width(), frame.height(), self.width(), self.height())
            self._frame = frame.scaled(
                self.width(), self.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self.update()

    def paintEvent(self, _event) -> None:
        if self._frame is None:
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.drawPixmap(0, 0, self._frame)
        painter.end()

    def move_to(self, x: float, y: float) -> None:
        self.move(int(x), int(y))
