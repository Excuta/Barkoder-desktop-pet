import random
import logging
import time
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext

_log = logging.getLogger("barkoder.follow")


class FollowBehavior(Behavior):
    name = "follow"

    def __init__(
        self,
        near_x_px: float,
        far_x_px: float,
        walk_speed_px: float,
        run_speed_px: float,
        follow_window_s: float,
        min_run_s: float,
        max_run_s: float,
        sm,
    ) -> None:
        self._near = near_x_px
        self._far = far_x_px
        self._walk_speed = walk_speed_px
        self._run_speed = run_speed_px
        self._window = follow_window_s
        self._min_run_s = min_run_s
        self._max_run_s = max_run_s
        self._sm = sm
        self._following = False  # hysteresis: keeps follow active until very close
        self._suppressed_until: float = 0.0

    def suppress(self, duration_s: float) -> None:
        self._suppressed_until = time.monotonic() + duration_s

    def should_enter(self, ctx: CursorContext) -> bool:
        if time.monotonic() < self._suppressed_until:
            return False
        cursor_active = ctx.cursor_idle_seconds < self._window
        if self._following:
            # exit only when very close (40% of near threshold) OR cursor settled
            return ctx.horizontal_distance > self._near * 0.4 and cursor_active
        return ctx.horizontal_distance > self._near and cursor_active

    def on_enter(self, ctx: CursorContext) -> None:
        self._following = True
        if ctx.horizontal_distance > self._far:
            self._sm.set_run_threshold(random.uniform(self._min_run_s, self._max_run_s))
        _log.debug("follow: enter dist=%.0fpx", ctx.horizontal_distance)

    def on_exit(self, ctx: CursorContext) -> None:
        self._following = False
        self._sm.reset_running_time()

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        direction = ctx.move_direction
        if ctx.horizontal_distance > self._far:
            speed = self._run_speed if direction == "east" else -self._run_speed
            return AnimationRequest("Run", direction), speed
        speed = self._walk_speed if direction == "east" else -self._walk_speed
        return AnimationRequest("Walk", direction), speed
