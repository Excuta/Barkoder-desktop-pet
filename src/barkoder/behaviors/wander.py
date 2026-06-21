import logging
import random
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext

_log = logging.getLogger("barkoder.wander")


class WanderBehavior(Behavior):
    priority = 6
    name = "wander"

    def __init__(self, wander_threshold_s: float, walk_speed_px: float, screen_width: int) -> None:
        self._threshold = wander_threshold_s
        self._speed = walk_speed_px
        self._screen_width = screen_width
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
        margin = 50.0
        x = random.uniform(margin, self._screen_width - margin - 68)
        for _ in range(10):
            candidate = random.uniform(margin, self._screen_width - margin - 68)
            if abs(candidate - dog_x) >= 150.0:
                x = candidate
                break
        self._target_x = x
        rest = random.uniform(0.5, 2.0)
        self._rest_remaining = rest
        _log.info("wander target=%.0f rest=%.1fs", x, rest)

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        # Rest at current target before picking a new one
        if self._rest_remaining > 0:
            self._rest_remaining -= 0.016
            return AnimationRequest("Idle", self._last_direction), 0.0

        if self._target_x is None or abs(ctx.dog_x - self._target_x) < self._speed + 1:
            self._pick_target(ctx.dog_x)
            return AnimationRequest("Idle", self._last_direction), 0.0

        direction = "east" if self._target_x > ctx.dog_x else "west"
        self._last_direction = direction
        delta = self._speed if direction == "east" else -self._speed
        return AnimationRequest("Walk", direction), delta
