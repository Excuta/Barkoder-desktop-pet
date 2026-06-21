from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QWidget


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
        self.setFixedSize(68, 68)
        self._frame: QPixmap | None = None

    def set_frame(self, pixmap: QPixmap) -> None:
        self._frame = pixmap
        self.update()

    def paintEvent(self, _event) -> None:
        if self._frame is None:
            return
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._frame)
        painter.end()

    def move_to(self, x: float, y: float) -> None:
        self.move(int(x), int(y))
