from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext


class IdleSitBehavior(Behavior):
    priority = 7
    name = "idle_sit"

    def __init__(self, sit_threshold_s: float) -> None:
        self._threshold = sit_threshold_s

    def should_enter(self, ctx: CursorContext) -> bool:
        return ctx.cursor_idle_seconds > self._threshold

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        return AnimationRequest("Sit", ctx.bark_direction_4), 0.0
