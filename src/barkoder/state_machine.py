import dataclasses
import random
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext


class StateMachine:
    def __init__(self, behaviors: list[Behavior]) -> None:
        if not behaviors:
            raise ValueError("StateMachine requires at least one Behavior")
        self._behaviors = sorted(behaviors, key=lambda b: b.priority)
        self._current: Behavior | None = None
        self._running_seconds: float = 0.0
        self._run_threshold: float = 15.0
        self._dwell_s: float = 0.0
        self._dwell_budget: float = 0.0
        self._cooldowns: dict[str, float] = {}

    @property
    def current_behavior(self) -> Behavior | None:
        return self._current

    def set_run_threshold(self, threshold: float) -> None:
        self._run_threshold = threshold

    def add_running_time(self, delta_s: float) -> None:
        self._running_seconds += delta_s

    def reset_running_time(self) -> None:
        self._running_seconds = 0.0

    @property
    def running_seconds(self) -> float:
        return self._running_seconds

    def tick(self, base_ctx: CursorContext, delta_s: float = 0.016) -> tuple[AnimationRequest, float]:
        import logging
        log = logging.getLogger("barkoder.sm")

        ctx = dataclasses.replace(
            base_ctx,
            running_seconds=self._running_seconds,
            run_threshold=self._run_threshold,
        )

        # Decay cooldowns
        for name in list(self._cooldowns):
            self._cooldowns[name] = max(0.0, self._cooldowns[name] - delta_s)

        # Accumulate dwell
        self._dwell_s += delta_s

        # Find winner — skip behaviors on cooldown
        winner = next(
            (b for b in self._behaviors
             if self._cooldowns.get(b.name, 0.0) <= 0 and b.should_enter(ctx)),
            self._behaviors[-1]
        )

        if winner is not self._current:
            current_priority = self._current.priority if self._current is not None else float("inf")
            can_transition = (
                winner.priority < current_priority        # higher-priority: always preempts
                or self._dwell_s >= self._dwell_budget    # lower-priority: only after dwell
            )
            if can_transition:
                prev_name = self._current.name if self._current is not None else "None"
                if self._current is not None:
                    cd = getattr(self._current, "exit_cooldown_s", 0.0)
                    if cd > 0:
                        self._cooldowns[self._current.name] = cd
                        log.info("%s → %s (cooldown %.1fs set)", prev_name, winner.name, cd)
                    self._current.on_exit(ctx)

                min_d = getattr(winner, "min_dwell_s", 0.0)
                max_d = getattr(winner, "max_dwell_s", 0.0)
                self._dwell_budget = random.uniform(min_d, max_d) if max_d > min_d else min_d

                log.info("%s → %s (budget=%.1fs)", prev_name, winner.name, self._dwell_budget)
                winner.on_enter(ctx)
                self._current = winner
                self._dwell_s = 0.0

        req, delta_x = self._current.update(ctx)
        return req, delta_x
