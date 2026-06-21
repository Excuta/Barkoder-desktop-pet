import logging
import random
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext

_log = logging.getLogger("barkoder.wander")


class WanderBehavior(Behavior):
    priority = 6
    name = "wander"

    def __init__(
        self,
        wander_threshold_s: float,
        walk_speed_px: float,
        screen_width: int,
        dog_size: int = 68,
    ) -> None:
        self._threshold = wander_threshold_s
        self._speed = walk_speed_px
        self._screen_width = screen_width
        self._dog_size = dog_size
        self._max_x = float(screen_width - dog_size)
        self._target_x: float | None = None
        self._rest_remaining: float = 0.0
        self._last_direction: str = "east"
        self._force_active: bool = False

    def force_start(self) -> None:
        self._force_active = True
        _log.info("force_start: dog loses interest, wanders away")

    def should_enter(self, ctx: CursorContext) -> bool:
        return self._force_active or ctx.cursor_idle_seconds > self._threshold

    def on_enter(self, ctx: CursorContext) -> None:
        self._target_x = None
        self._rest_remaining = 0.0
        self._pick_target(ctx.dog_x)

    def on_exit(self, ctx: CursorContext) -> None:
        self._force_active = False
        self._target_x = None
        _log.info("wander exit")

    def _pick_target(self, dog_x: float) -> None:
        lo = 0.0
        hi = self._max_x

        # Bias toward the opposite side when already near an edge
        near_left = dog_x < self._max_x * 0.2
        near_right = dog_x > self._max_x * 0.8
        if near_left:
            lo = self._max_x * 0.3
        elif near_right:
            hi = self._max_x * 0.7

        x = random.uniform(lo, hi)
        for _ in range(10):
            candidate = random.uniform(lo, hi)
            if abs(candidate - dog_x) >= 150.0:
                x = candidate
                break
        self._target_x = x
        self._rest_remaining = random.uniform(0.5, 2.0)
        _log.info("wander target=%.0f rest=%.1fs", x, self._rest_remaining)

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        if self._rest_remaining > 0:
            self._rest_remaining -= 0.016
            return AnimationRequest("Idle", self._last_direction), 0.0

        # Dog has reached the physical screen edge — turn around
        at_wall = ctx.dog_x <= 2.0 or ctx.dog_x >= self._max_x - 2.0
        if at_wall:
            _log.info("wander: hit screen edge at %.0f, reversing", ctx.dog_x)
            self._pick_target(ctx.dog_x)
            return AnimationRequest("Idle", self._last_direction), 0.0

        if self._target_x is None or abs(ctx.dog_x - self._target_x) < self._speed + 1:
            self._pick_target(ctx.dog_x)
            return AnimationRequest("Idle", self._last_direction), 0.0

        direction = "east" if self._target_x > ctx.dog_x else "west"
        self._last_direction = direction
        delta = self._speed if direction == "east" else -self._speed
        return AnimationRequest("Walk", direction), delta
