import dataclasses
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext


class StateMachine:
    def __init__(self, behaviors: list[Behavior], min_dwell_s: float = 1.0) -> None:
        if not behaviors:
            raise ValueError("StateMachine requires at least one Behavior")
        self._behaviors = sorted(behaviors, key=lambda b: b.priority)
        self._current: Behavior | None = None
        self._running_seconds: float = 0.0
        self._run_threshold: float = 15.0
        self._min_dwell_s: float = min_dwell_s
        self._dwell_s: float = 0.0

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
        ctx = dataclasses.replace(
            base_ctx,
            running_seconds=self._running_seconds,
            run_threshold=self._run_threshold,
        )
        self._dwell_s += delta_s

        winner = next(
            (b for b in self._behaviors if b.should_enter(ctx)), self._behaviors[-1]
        )

        if winner is not self._current:
            current_priority = self._current.priority if self._current is not None else float("inf")
            # Higher-priority (lower number) behaviors always interrupt immediately.
            # Lower-priority behaviors wait until min_dwell_s has elapsed.
            can_transition = (
                winner.priority < current_priority
                or self._dwell_s >= self._min_dwell_s
            )
            if can_transition:
                if self._current is not None:
                    self._current.on_exit(ctx)
                winner.on_enter(ctx)
                self._current = winner
                self._dwell_s = 0.0

        req, delta_x = self._current.update(ctx)
        return req, delta_x
