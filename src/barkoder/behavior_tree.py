import logging
from barkoder.bt.nodes import BTNode, BTResult

_log = logging.getLogger("barkoder.bt.tree")


class BehaviorTree:
    """Replaces StateMachine. Wraps a root BTNode; same external API."""

    _run_threshold: float = 15.0  # seconds of running before PantBehavior triggers

    def __init__(self, root: BTNode) -> None:
        self._root = root
        self._running_seconds: float = 0.0
        self._current_leaf = None  # BTLeaf of the currently active behavior (informational)

    @property
    def running_seconds(self) -> float:
        return self._running_seconds

    @property
    def current_behavior(self):
        """Return the active Behavior object, or None."""
        if self._current_leaf is None:
            return None
        return self._current_leaf.behavior

    def add_running_time(self, delta_s: float) -> None:
        self._running_seconds += delta_s

    def reset_running_time(self) -> None:
        self._running_seconds = 0.0

    def set_run_threshold(self, threshold: float) -> None:
        self._run_threshold = threshold

    def tick(self, ctx, delta_s: float):
        """Tick the root node. Returns (AnimationRequest, delta_x)."""
        result = self._root.tick(ctx, delta_s)
        if result is None:
            _log.warning("BT root returned None — no behavior active")
            from barkoder.state_machine import AnimationRequest
            return AnimationRequest("Idle", "east"), 0.0
        return result.request, result.delta_x
