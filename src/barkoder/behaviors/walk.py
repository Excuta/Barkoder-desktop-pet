from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext


class WalkBehavior(Behavior):
    priority = 5
    name = "walk"
    min_dwell_s = 3.0
    max_dwell_s = 8.0
    exit_cooldown_s = 1.0

    def __init__(self, near_x_px: float, walk_speed_px: float) -> None:
        self._near = near_x_px
        self._speed = walk_speed_px

    def should_enter(self, ctx: CursorContext) -> bool:
        return ctx.horizontal_distance > self._near

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        delta = self._speed if ctx.move_direction == "east" else -self._speed
        return AnimationRequest("Walk", ctx.move_direction), delta
