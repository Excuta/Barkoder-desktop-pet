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
        run_speed_px: float = 6.0,
        wander_run_chance: float = 0.3,
        wander_lay_chance: float = 0.5,
    ) -> None:
        self._threshold = wander_threshold_s
        self._speed = walk_speed_px
        self._run_speed = run_speed_px
        self._run_chance = wander_run_chance
        self._lay_chance = wander_lay_chance
        self._screen_width = screen_width
        self._dog_size = dog_size
        self._max_x = float(screen_width - dog_size)
        self._target_x: float | None = None
        self._last_direction: str = "east"
        self._force_active: bool = False
        self._is_running: bool = False
        self._pause_phases: list[tuple[float, str]] = []
        self._current_phase: int = 0
        self._phase_remaining: float = 0.0

    def force_start(self) -> None:
        self._force_active = True
        _log.info("force_start: dog loses interest, wanders away")

    def should_enter(self, ctx: CursorContext) -> bool:
        return self._force_active or ctx.cursor_idle_seconds > self._threshold

    def on_enter(self, ctx: CursorContext) -> None:
        self._pause_phases = []
        self._current_phase = 0
        self._phase_remaining = 0.0
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

        # Decide whether to run this trip
        self._is_running = random.random() < self._run_chance

        # Build pause sequence before this walk begins
        if random.random() < self._lay_chance:
            sit1 = random.uniform(0.5, 1.5)
            lay = random.uniform(2.0, 5.0)
            sit2 = random.uniform(0.3, 1.0)
            self._pause_phases = [(sit1, "Sit"), (lay, "Rest"), (sit2, "Sit")]
            _log.info("wander target=%.0f sit=%.1fs lay=%.1fs sit=%.1fs %s",
                      x, sit1, lay, sit2, "run" if self._is_running else "walk")
        else:
            sit = random.uniform(1.5, 3.5)
            self._pause_phases = [(sit, "Sit")]
            _log.info("wander target=%.0f sit=%.1fs %s",
                      x, sit, "run" if self._is_running else "walk")

        self._current_phase = 0
        self._phase_remaining = self._pause_phases[0][0]

    def _wall_bounce(self, dog_x: float) -> None:
        _log.info("wander: hit screen edge at %.0f, reversing", dog_x)
        self._target_x = None
        self._pause_phases = [(random.uniform(0.2, 0.5), "Idle")]
        self._current_phase = 0
        self._phase_remaining = self._pause_phases[0][0]

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        # Tick pause phases
        if self._current_phase < len(self._pause_phases):
            self._phase_remaining -= 0.016
            if self._phase_remaining <= 0.0:
                self._current_phase += 1
                if self._current_phase < len(self._pause_phases):
                    self._phase_remaining = self._pause_phases[self._current_phase][0]
            if self._current_phase < len(self._pause_phases):
                _, anim = self._pause_phases[self._current_phase]
                return AnimationRequest(anim, self._last_direction), 0.0
            # else: pause ended, fall through to walking

        # Wall bounce — brief idle then pick a new target
        at_wall = ctx.dog_x <= 2.0 or ctx.dog_x >= self._max_x - 2.0
        if at_wall:
            self._wall_bounce(ctx.dog_x)
            return AnimationRequest("Idle", self._last_direction), 0.0

        # Arrived at target or no target yet — pick next and start pause
        if self._target_x is None or abs(ctx.dog_x - self._target_x) < self._speed + 1:
            self._pick_target(ctx.dog_x)
            _, anim = self._pause_phases[0]
            return AnimationRequest(anim, self._last_direction), 0.0

        # Walk or run toward target
        direction = "east" if self._target_x > ctx.dog_x else "west"
        self._last_direction = direction
        if self._is_running:
            spd = self._run_speed
            return AnimationRequest("Run", direction), (spd if direction == "east" else -spd)
        spd = self._speed
        return AnimationRequest("Walk", direction), (spd if direction == "east" else -spd)
