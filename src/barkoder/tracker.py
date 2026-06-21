import dataclasses
import math
from PyQt6.QtGui import QCursor


@dataclasses.dataclass(frozen=True)
class CursorContext:
    cursor_x: float
    cursor_y: float
    dog_x: float
    dog_y: float
    horizontal_distance: float
    move_direction: str        # "east" | "west"
    bark_direction_4: str      # "north" | "south" | "east" | "west"
    cursor_idle_seconds: float
    running_seconds: float
    run_threshold: float       # set by StateMachine, default 15.0


def compute_bark_direction(
    cursor_x: float, cursor_y: float, dog_x: float, dog_y: float
) -> str:
    dx = cursor_x - dog_x
    dy = cursor_y - dog_y  # positive = cursor is below dog (south)
    if abs(dx) >= abs(dy):
        return "east" if dx >= 0 else "west"
    return "south" if dy >= 0 else "north"


class CursorTracker:
    def __init__(self, move_threshold_px: float = 5.0) -> None:
        self._deadzone_px = move_threshold_px
        pos = QCursor.pos()
        # Track "settled" position — only updates when cursor leaves the deadzone.
        # Jitter smaller than deadzone_px never resets cursor_idle_seconds.
        self._settled_x: float = float(pos.x())
        self._settled_y: float = float(pos.y())
        self._cursor_idle_seconds: float = 0.0

    def compute(
        self,
        dog_x: float,
        dog_y: float,
        delta_s: float,
        running_seconds: float = 0.0,
        run_threshold: float = 15.0,
    ) -> CursorContext:
        pos = QCursor.pos()
        cx = float(pos.x())
        cy = float(pos.y())

        dist_from_settled = math.hypot(cx - self._settled_x, cy - self._settled_y)
        if dist_from_settled > self._deadzone_px:
            self._cursor_idle_seconds = 0.0
            self._settled_x = cx
            self._settled_y = cy
        else:
            self._cursor_idle_seconds += delta_s

        # Use settled position for all behavior decisions — prevents boundary oscillation
        # when raw cursor jitter crosses a threshold while "resting" within the deadzone.
        h_dist = abs(self._settled_x - dog_x)
        move_dir = "east" if self._settled_x > dog_x else "west"
        bark_dir = compute_bark_direction(self._settled_x, self._settled_y, dog_x, dog_y)

        return CursorContext(
            cursor_x=cx,
            cursor_y=cy,
            dog_x=dog_x,
            dog_y=dog_y,
            horizontal_distance=h_dist,
            move_direction=move_dir,
            bark_direction_4=bark_dir,
            cursor_idle_seconds=self._cursor_idle_seconds,
            running_seconds=running_seconds,
            run_threshold=run_threshold,
        )
