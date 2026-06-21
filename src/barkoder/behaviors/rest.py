from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext


class RestBehavior(Behavior):
    name = "rest"

    def __init__(self, rest_threshold_s: float) -> None:
        self._threshold = rest_threshold_s
        self._direction = "east"

    def should_enter(self, ctx: CursorContext) -> bool:
        return ctx.cursor_idle_seconds > self._threshold

    def on_enter(self, ctx: CursorContext) -> None:
        self._direction = ctx.bark_direction_4

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        return AnimationRequest("Rest", self._direction), 0.0
