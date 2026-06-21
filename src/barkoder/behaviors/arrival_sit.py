from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext


class ArrivalSitBehavior(Behavior):
    priority = 3
    name = "arrival_sit"

    def __init__(self, arrival_x_px: float, sit_hold_seconds: float) -> None:
        self._arrival_px = arrival_x_px
        self._sit_hold = sit_hold_seconds
        self._triggered = False
        self._hold_elapsed = 0.0

    def should_enter(self, ctx: CursorContext) -> bool:
        if self._triggered:
            return False
        return ctx.horizontal_distance < self._arrival_px

    def on_enter(self, ctx: CursorContext) -> None:
        self._hold_elapsed = 0.0

    def on_exit(self, ctx: CursorContext) -> None:
        self._triggered = False

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        self._hold_elapsed += 0.016
        return AnimationRequest("Sit", ctx.bark_direction_4), 0.0

    @property
    def hold_done(self) -> bool:
        return self._hold_elapsed >= self._sit_hold
