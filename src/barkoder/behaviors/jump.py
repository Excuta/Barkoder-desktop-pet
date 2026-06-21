import random
import logging
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext

_log = logging.getLogger("barkoder.jump")


class JumpBehavior(Behavior):
    name = "jump"

    def __init__(self, trigger_chance_per_s: float = 0.05) -> None:
        self._chance = trigger_chance_per_s
        self._active = False
        self._direction = "east"

    def should_enter(self, ctx: CursorContext) -> bool:
        if self._active:
            return True  # hold until notify_animation_finished() clears _active
        # Only jump when cursor is idle and far (autonomous state, not chasing)
        idle = ctx.cursor_idle_seconds > 5.0 and ctx.horizontal_distance > 200
        return idle and (random.random() < self._chance * 0.016)

    def on_enter(self, ctx: CursorContext) -> None:
        self._active = True
        self._direction = ctx.move_direction
        _log.debug("jump: triggered")

    def on_exit(self, ctx: CursorContext) -> None:
        self._active = False

    def notify_animation_finished(self) -> None:
        self._active = False  # should_enter → False next tick → BTLeaf calls on_exit

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        return AnimationRequest("Jump", self._direction), 0.0
