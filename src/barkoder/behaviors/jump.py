import random
import logging
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext

_log = logging.getLogger("barkoder.jump")

_MIN_IDLE_S = 5.0        # cursor must have been idle at least this long
_MIN_DISTANCE_PX = 200.0  # dog must be at least this far from cursor


class JumpBehavior(Behavior):
    name = "jump"

    def __init__(self, trigger_chance_per_s: float = 0.5) -> None:
        self._chance = trigger_chance_per_s * 0.016  # convert to per-tick probability
        self._active = False
        self._direction = "east"

    def should_enter(self, ctx: CursorContext) -> bool:
        if self._active:
            return True
        if ctx.cursor_idle_seconds < _MIN_IDLE_S:
            return False
        if ctx.horizontal_distance < _MIN_DISTANCE_PX:
            return False
        return random.random() < self._chance

    def on_enter(self, ctx: CursorContext) -> None:
        self._active = True
        self._direction = ctx.move_direction
        _log.debug("[jump:trigger] idle=%.1fs dist=%.0fpx dir=%s",
                   ctx.cursor_idle_seconds, ctx.horizontal_distance, self._direction)

    def on_exit(self, ctx: CursorContext) -> None:
        self._active = False

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        return AnimationRequest("Jump", self._direction), 0.0

    def notify_animation_finished(self) -> None:
        self._active = False
        _log.debug("[jump:done]")
