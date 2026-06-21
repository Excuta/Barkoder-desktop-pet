import logging
import random
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext

_log = logging.getLogger("barkoder.wander")

_SITTING = "sitting"
_LAYING = "laying"
_WALKING = "walking"
_RUNNING = "running"


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
        wander_run_chance: float = 0.1,
        wander_lay_chance: float = 0.2,
    ) -> None:
        self._threshold = wander_threshold_s
        self._speed = walk_speed_px
        self._run_speed = run_speed_px
        self._run_chance = wander_run_chance
        self._lay_chance = wander_lay_chance
        self._max_x = float(screen_width - dog_size)
        self._target_x: float | None = None
        self._last_direction: str = "east"
        self._force_active: bool = False
        # State machine
        self._state: str = _WALKING   # default; on_enter switches to sitting
        self._state_timer: float = 0.0
        self._transition_cd: float = 0.0
        self._sit_anim: str = "Sit"
        self._lay_eligible: bool = True

    def _enter_sit(
        self,
        duration: float,
        anim: str = "Sit",
        lay_eligible: bool = True,
        cd: float = 0.8,
    ) -> None:
        self._state = _SITTING
        self._state_timer = duration
        self._sit_anim = anim
        self._lay_eligible = lay_eligible
        self._transition_cd = cd

    def force_start(self) -> None:
        self._force_active = True
        _log.info("force_start: dog loses interest, wanders away")

    def should_enter(self, ctx: CursorContext) -> bool:
        return self._force_active or ctx.cursor_idle_seconds > self._threshold

    def on_enter(self, ctx: CursorContext) -> None:
        self._target_x = None
        self._enter_sit(random.uniform(2.0, 4.0))

    def on_exit(self, ctx: CursorContext) -> None:
        self._force_active = False
        self._target_x = None
        _log.info("wander exit")

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
        _log.info("wander target=%.0f", x)

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        dt = 0.016
        self._transition_cd = max(0.0, self._transition_cd - dt)

        # --- LAYING ---
        if self._state == _LAYING:
            self._state_timer -= dt
            if self._state_timer <= 0.0:
                self._enter_sit(random.uniform(1.5, 3.0), lay_eligible=False, cd=0.0)
                _log.info("wander: lay finished, brief sit")
            return AnimationRequest("Rest", self._last_direction), 0.0

        # --- SITTING ---
        if self._state == _SITTING:
            self._state_timer -= dt
            if self._lay_eligible and self._transition_cd <= 0.0 and random.random() < self._lay_chance * dt:
                self._state = _LAYING
                self._state_timer = random.uniform(15.0, 25.0)
                _log.info("wander: lying down for %.1fs", self._state_timer)
            elif self._state_timer <= 0.0:
                self._pick_target(ctx.dog_x)
                self._state = _WALKING
                self._transition_cd = 1.5  # must walk 1.5s before first run burst
            return AnimationRequest(self._sit_anim, self._last_direction), 0.0

        # --- WALKING / RUNNING ---
        at_wall = ctx.dog_x <= 2.0 or ctx.dog_x >= self._max_x - 2.0
        if at_wall:
            _log.info("wander: hit screen edge at %.0f, reversing", ctx.dog_x)
            self._target_x = None
            self._enter_sit(random.uniform(0.2, 0.5), "Idle", lay_eligible=False, cd=0.0)
            return AnimationRequest("Idle", self._last_direction), 0.0

        spd = self._run_speed if self._state == _RUNNING else self._speed
        if self._target_x is None or abs(ctx.dog_x - self._target_x) < spd + 1:
            self._enter_sit(random.uniform(5.0, 10.0))
            return AnimationRequest("Sit", self._last_direction), 0.0

        direction = "east" if self._target_x > ctx.dog_x else "west"
        self._last_direction = direction

        is_running = self._state == _RUNNING
        if not is_running and self._transition_cd <= 0.0 and random.random() < self._run_chance * dt:
            self._state = _RUNNING
            self._state_timer = random.uniform(1.5, 4.0)
            is_running = True
            _log.debug("wander: run burst %.1fs", self._state_timer)

        if is_running:
            self._state_timer -= dt
            if self._state_timer <= 0.0:
                self._state = _WALKING
                self._transition_cd = 2.5  # walk 2.5s before another burst
            return AnimationRequest("Run", direction), (self._run_speed if direction == "east" else -self._run_speed)

        return AnimationRequest("Walk", direction), (self._speed if direction == "east" else -self._speed)
