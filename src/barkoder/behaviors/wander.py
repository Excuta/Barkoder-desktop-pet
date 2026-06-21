import random
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext


class WanderBehavior(Behavior):
    priority = 6
    name = "wander"

    def __init__(self, wander_threshold_s: float, walk_speed_px: float, screen_width: int) -> None:
        self._threshold = wander_threshold_s
        self._speed = walk_speed_px
        self._screen_width = screen_width
        self._target_x: float = 0.0

    def should_enter(self, ctx: CursorContext) -> bool:
        return ctx.cursor_idle_seconds > self._threshold

    def on_enter(self, ctx: CursorContext) -> None:
        self._pick_target(ctx.dog_x)

    def _pick_target(self, dog_x: float) -> None:
        margin = 50.0
        x = random.uniform(margin, self._screen_width - margin - 68)
        for _ in range(10):
            candidate = random.uniform(margin, self._screen_width - margin - 68)
            if abs(candidate - dog_x) >= 150.0:
                x = candidate
                break
        self._target_x = x

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        if abs(ctx.dog_x - self._target_x) < self._speed + 1:
            self._pick_target(ctx.dog_x)
        direction = "east" if self._target_x > ctx.dog_x else "west"
        delta = self._speed if direction == "east" else -self._speed
        return AnimationRequest("Walk", direction), delta
