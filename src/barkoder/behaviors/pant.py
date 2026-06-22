import logging
import random
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext

_log = logging.getLogger("barkoder.pant")


class PantBehavior(Behavior):
    priority = 1
    name = "pant"

    _MIN_INTERVAL = 20.0
    _MAX_INTERVAL = 40.0
    _MIN_CYCLES = 2
    _MAX_CYCLES = 4

    def __init__(self, pant_cycles_required: int = 2) -> None:
        self._done = False
        self._direction = "east"
        self._interval_remaining: float = random.uniform(self._MIN_INTERVAL, self._MAX_INTERVAL)
        self._cycles_done: int = 0
        self._target_cycles: int = self._MIN_CYCLES
        self._forced: bool = False

    def force_pant(self) -> None:
        self._forced = True
        self._interval_remaining = 0.0

    def should_enter(self, ctx: CursorContext) -> bool:
        if self._done:
            return False
        self._interval_remaining -= 0.016
        if self._interval_remaining > 0.0:
            return False
        return self._forced

    def on_enter(self, ctx: CursorContext) -> None:
        self._done = False
        self._forced = False
        self._direction = ctx.move_direction
        self._cycles_done = 0
        self._target_cycles = random.randint(self._MIN_CYCLES, self._MAX_CYCLES)
        _log.debug("[pant:start] target=%d cycles", self._target_cycles)

    def on_exit(self, ctx: CursorContext) -> None:
        self._done = False
        self._interval_remaining = random.uniform(self._MIN_INTERVAL, self._MAX_INTERVAL)

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        return AnimationRequest("Pant", self._direction), 0.0

    def notify_animation_finished(self) -> None:
        self._cycles_done += 1
        if self._cycles_done >= self._target_cycles:
            self._done = True
            _log.debug("[pant:done] %d cycles", self._cycles_done)
        else:
            _log.debug("[pant:cycle] %d/%d", self._cycles_done, self._target_cycles)
