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
        lo = margin
        hi = self._screen_width - margin - 68

        # Bias away from edge to prevent wall-hugging
        near_left = dog_x < 100.0
        near_right = dog_x > self._screen_width - 100.0 - 68
        if near_left:
            lo = max(lo, self._screen_width * 0.2)
            rest_bonus = random.uniform(0.5, 1.5)
        elif near_right:
            hi = min(hi, self._screen_width * 0.8)
            rest_bonus = random.uniform(0.5, 1.5)
        else:
            rest_bonus = 0.0

        x = random.uniform(lo, hi)
        for _ in range(10):
            candidate = random.uniform(lo, hi)
            if abs(candidate - dog_x) >= 150.0:
                x = candidate
                break
        self._target_x = x
        rest = random.uniform(0.5, 2.0) + rest_bonus
        self._rest_remaining = rest
        _log.info("wander target=%.0f rest=%.1fs", x, rest)

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        # Rest at current target before picking a new one
        if self._rest_remaining > 0:
            self._rest_remaining -= 0.016
            return AnimationRequest("Idle", self._last_direction), 0.0

        # Detect stuck at actual screen wall — sit and re-pick toward centre
        at_left_wall = ctx.dog_x < 30.0
        at_right_wall = ctx.dog_x > self._screen_width - 98.0  # 30 + 68
        if self._target_x is not None:
            toward_wall = (at_left_wall and self._target_x < ctx.dog_x) or \
                          (at_right_wall and self._target_x > ctx.dog_x)
            if toward_wall:
                _log.info("wander: hit screen wall, resting and re-picking")
                self._pick_target(ctx.dog_x)
                self._rest_remaining += random.uniform(1.0, 2.0)
                return AnimationRequest("Sit", self._last_direction), 0.0

        if self._target_x is None or abs(ctx.dog_x - self._target_x) < self._speed + 1:
            self._pick_target(ctx.dog_x)
            return AnimationRequest("Idle", self._last_direction), 0.0

        direction = "east" if self._target_x > ctx.dog_x else "west"
        self._last_direction = direction
        delta = self._speed if direction == "east" else -self._speed
        return AnimationRequest("Walk", direction), delta
