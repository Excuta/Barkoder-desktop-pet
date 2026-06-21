import random
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext


class PantBehavior(Behavior):
    priority = 1
    name = "pant"

    _MIN_INTERVAL = 20.0
    _MAX_INTERVAL = 40.0
    _MIN_CYCLES = 2
    _MAX_CYCLES = 4
    _RUN_BEFORE_PANT = 1.0  # seconds of running required before pant fires

    def __init__(self) -> None:
        self._done = False
        self._direction = "east"
        self._interval_remaining: float = random.uniform(self._MIN_INTERVAL, self._MAX_INTERVAL)
        self._cycles_done: int = 0
        self._target_cycles: int = self._MIN_CYCLES

    def should_enter(self, ctx: CursorContext) -> bool:
        if self._done:
            return False
        self._interval_remaining -= 0.016
        if self._interval_remaining > 0.0:
            return False
        return ctx.running_seconds >= self._RUN_BEFORE_PANT

    def on_enter(self, ctx: CursorContext) -> None:
        self._done = False
        self._direction = ctx.move_direction
        self._cycles_done = 0
        self._target_cycles = random.randint(self._MIN_CYCLES, self._MAX_CYCLES)

    def on_exit(self, ctx: CursorContext) -> None:
        self._done = False
        self._interval_remaining = random.uniform(self._MIN_INTERVAL, self._MAX_INTERVAL)

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        return AnimationRequest("Pant", self._direction), 0.0

    def notify_animation_finished(self) -> None:
        self._cycles_done += 1
        if self._cycles_done >= self._target_cycles:
            self._done = True
