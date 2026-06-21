import random
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext


class PantBehavior(Behavior):
    priority = 1
    name = "pant"

    def __init__(self, sm: "StateMachine", min_cycles: int, max_cycles: int) -> None:  # noqa
        self._sm = sm
        self._min_cycles = min_cycles
        self._max_cycles = max_cycles
        self._cycles_remaining = 0
        self._exhausted = False

    def should_enter(self, ctx: CursorContext) -> bool:
        if self._exhausted:
            return False
        return ctx.running_seconds >= ctx.run_threshold

    def on_enter(self, ctx: CursorContext) -> None:
        self._cycles_remaining = random.randint(self._min_cycles, self._max_cycles)
        self._exhausted = False

    def on_exit(self, ctx: CursorContext) -> None:
        self._exhausted = False

    def _notify_cycle_done(self) -> None:
        self._cycles_remaining -= 1
        if self._cycles_remaining <= 0:
            self._exhausted = True
            self._sm.reset_running_time()

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        return AnimationRequest("Pant", ctx.move_direction), 0.0

    def notify_animation_finished(self) -> None:
        self._notify_cycle_done()
