from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from barkoder.behaviors.base import Behavior
    from barkoder.tracker import CursorContext
    from barkoder.state_machine import AnimationRequest

_log = logging.getLogger("barkoder.bt")


@dataclass
class BTResult:
    request: object   # AnimationRequest at runtime
    delta_x: float
    running: bool     # True = still running; False = behavior signalled done (for BTSequence)


class BTNode(ABC):
    @abstractmethod
    def tick(self, ctx: "CursorContext", delta_s: float) -> Optional[BTResult]:
        """Return BTResult if running/active, None if not applicable."""
        ...


class BTLeaf(BTNode):
    """Wraps a single Behavior. Activates when should_enter() is True."""

    def __init__(self, behavior: "Behavior") -> None:
        self._b = behavior
        self._active = False

    @property
    def behavior(self) -> "Behavior":
        return self._b

    def tick(self, ctx: "CursorContext", delta_s: float) -> Optional[BTResult]:
        if not self._b.should_enter(ctx):
            if self._active:
                self._b.on_exit(ctx)
                self._active = False
            return None
        if not self._active:
            _log.debug("BTLeaf enter: %s", self._b.name)
            self._b.on_enter(ctx)
            self._active = True
        req, dx = self._b.update(ctx)
        return BTResult(req, dx, running=True)


class BTSelector(BTNode):
    """Tries children in order; returns first non-None result (priority selector)."""

    def __init__(self, children: list[BTNode]) -> None:
        self._children = children

    def tick(self, ctx: "CursorContext", delta_s: float) -> Optional[BTResult]:
        for child in self._children:
            result = child.tick(ctx, delta_s)
            if result is not None:
                return result
        return None


class BTCooldown(BTNode):
    """Blocks re-entry of child for cooldown_s after it exits."""

    def __init__(self, child: BTNode, cooldown_s: float) -> None:
        self._child = child
        self._cooldown_s = cooldown_s
        self._remaining: float = 0.0
        self._was_active: bool = False

    def tick(self, ctx: "CursorContext", delta_s: float) -> Optional[BTResult]:
        if self._remaining > 0:
            self._remaining = max(0.0, self._remaining - delta_s)
            return None
        result = self._child.tick(ctx, delta_s)
        if result is not None:
            self._was_active = True
        elif self._was_active:
            # Child just exited — start cooldown
            self._remaining = self._cooldown_s
            self._was_active = False
            _log.info("BTCooldown: %.1fs started", self._cooldown_s)
        return result


class BTRandomDwell(BTNode):
    """Holds child running for a random duration [min_s, max_s], then yields.

    When the budget expires the decorator returns None, letting the parent
    selector re-evaluate priorities on the next tick.  The inner BTLeaf is
    NOT deactivated (on_exit is not called) — the child stays "entered" and
    resumes without on_enter if the selector selects it again.  This is
    intentional: dwell throttles the selector, not the behavior lifecycle.
    """

    def __init__(self, child: BTNode, min_s: float, max_s: float) -> None:
        self._child = child
        self._min = min_s
        self._max = max_s
        self._budget: float = 0.0
        self._elapsed: float = 0.0
        self._has_budget: bool = False

    def tick(self, ctx: "CursorContext", delta_s: float) -> Optional[BTResult]:
        result = self._child.tick(ctx, delta_s)
        if result is not None:
            if not self._has_budget:
                self._budget = random.uniform(self._min, self._max)
                self._has_budget = True
                _log.debug("BTRandomDwell: budget=%.1fs", self._budget)
            self._elapsed += delta_s
            if self._elapsed >= self._budget:
                self._elapsed = 0.0
                self._budget = 0.0
                self._has_budget = False
                _log.debug("BTRandomDwell: budget expired, yielding")
                return None  # budget exhausted — let selector re-evaluate next tick
            return result
        # Child not active — reset
        self._elapsed = 0.0
        self._budget = 0.0
        self._has_budget = False
        return None
