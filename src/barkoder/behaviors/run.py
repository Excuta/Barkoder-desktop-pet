import random
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext


class RunBehavior(Behavior):
    priority = 4
    name = "run"
    min_dwell_s = 3.0
    max_dwell_s = 8.0
    exit_cooldown_s = 2.0

    def __init__(
        self,
        far_x_px: float,
        run_speed_px: float,
        sm: "StateMachine",  # noqa: F821
        min_run_s: float,
        max_run_s: float,
    ) -> None:
        self._far = far_x_px
        self._speed = run_speed_px
        self._sm = sm
        self._min_run_s = min_run_s
        self._max_run_s = max_run_s

    def should_enter(self, ctx: CursorContext) -> bool:
        return ctx.horizontal_distance > self._far

    def on_enter(self, ctx: CursorContext) -> None:
        threshold = random.uniform(self._min_run_s, self._max_run_s)
        self._sm.set_run_threshold(threshold)

    def on_exit(self, ctx: CursorContext) -> None:
        self._sm.reset_running_time()

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        delta = self._speed if ctx.move_direction == "east" else -self._speed
        return AnimationRequest("Run", ctx.move_direction), delta
