import logging
import random
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext

_log = logging.getLogger("barkoder.wander")

_WALK, _RUN, _SIT, _LAY, _POST_LAY = "walk", "run", "sit", "lay", "post_lay"

_DURATIONS: dict[str, tuple[float, float]] = {
    _WALK: (8.0, 15.0),
    _RUN: (6.0, 12.0),
    _SIT: (5.0, 10.0),
    _LAY: (15.0, 25.0),
    _POST_LAY: (1.5, 3.0),
}
_NEXT = {_WALK: _RUN, _RUN: _SIT, _SIT: _LAY, _LAY: _POST_LAY, _POST_LAY: _WALK}


class WanderBehavior(Behavior):
    priority = 6
    name = "wander"

    def __init__(
        self,
        wander_threshold_s: float,
        walk_speed_px: float,
        screen_width: int,
        dog_size: int = 68,
        run_speed_px: float = 6.0,
        pant_cycles_required: int = 2,
    ) -> None:
        self._threshold = wander_threshold_s
        self._speed = walk_speed_px
        self._run_speed = run_speed_px
        self._max_x = float(screen_width - dog_size)
        self._pant_cycles_required = pant_cycles_required
        self._target_x: float | None = None
        self._last_direction: str = "east"
        self._force_active: bool = False
        self._state: str = _POST_LAY  # non-movement so first on_enter doesn't count as phase
        self._phase_timer: float = 0.0
        self._activity_phases: int = 0
        self._pant_due: bool = False

    def force_start(self) -> None:
        self._force_active = True
        _log.info("[wander:enter] force_start — dog loses interest")

    def should_enter(self, ctx: CursorContext) -> bool:
        return self._force_active or ctx.cursor_idle_seconds > self._threshold

    def on_enter(self, ctx: CursorContext) -> None:
        self._target_x = None
        self._activity_phases = 0
        self._pant_due = False
        _log.info("[wander:enter] starting cycle")
        self._enter_phase(_WALK)

    def on_exit(self, ctx: CursorContext) -> None:
        self._force_active = False
        self._target_x = None
        self._activity_phases = 0
        self._pant_due = False
        _log.info("[wander:exit] state=%s remaining=%.1fs", self._state, self._phase_timer)

    def _enter_phase(self, phase: str) -> None:
        old_state = self._state
        if old_state in (_WALK, _RUN):
            self._activity_phases += 1
            if self._activity_phases >= self._pant_cycles_required:
                self._pant_due = True
                self._activity_phases = 0
                _log.info("[wander:pant] %d phases done → signaling pant",
                          self._pant_cycles_required)
        self._state = phase
        self._phase_timer = random.uniform(*_DURATIONS[phase])
        if phase in (_SIT, _LAY, _POST_LAY):
            self._target_x = None
        _log.info("[wander:phase] %s → %s (%.1fs)", old_state, phase, self._phase_timer)

    def _pick_target(self, dog_x: float) -> None:
        lo = 0.0
        hi = self._max_x
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
        _log.debug("[wander:move] target=%.0f", x)

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        dt = 0.016
        self._phase_timer -= dt
        if self._phase_timer <= 0:
            self._enter_phase(_NEXT[self._state])

        if self._state == _LAY:
            return AnimationRequest("Rest", self._last_direction), 0.0
        if self._state in (_SIT, _POST_LAY):
            return AnimationRequest("Sit", self._last_direction), 0.0

        # WALK or RUN
        speed = self._run_speed if self._state == _RUN else self._speed
        anim = "Run" if self._state == _RUN else "Walk"

        at_wall = ctx.dog_x <= 2.0 or ctx.dog_x >= self._max_x - 2.0
        if at_wall:
            self._pick_target(ctx.dog_x)
            direction = "east" if self._target_x > ctx.dog_x else "west"
            self._last_direction = direction
            _log.debug("[wander:wall] dog_x=%.0f reversed to %s", ctx.dog_x, direction)
            delta = speed if direction == "east" else -speed
            return AnimationRequest(anim, direction), delta

        if self._target_x is None or abs(ctx.dog_x - self._target_x) < speed + 1:
            self._pick_target(ctx.dog_x)

        direction = "east" if self._target_x > ctx.dog_x else "west"
        self._last_direction = direction
        delta = speed if direction == "east" else -speed
        return AnimationRequest(anim, direction), delta
