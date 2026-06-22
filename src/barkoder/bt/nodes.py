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
            _log.debug("[bt:enter] %s", self._b.name)
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
            _log.info("[bt:cooldown] %.1fs started", self._cooldown_s)
        return result


class BTRandomDwell(BTNode):
    """Holds child running for a random duration [min_s, max_s], then yields.

    After the budget expires the node stays dark for a random pause
    [min_yield_s, max_yield_s] before competing again.  During the pause the
    child is NOT ticked — it retains _active=True so no spurious on_enter when
    it resumes.  This prevents lower-priority behaviors from getting only one
    frame of screen time (the original one-tick bleed-through twitch).
    """

    def __init__(
        self,
        child: BTNode,
        min_s: float,
        max_s: float,
        min_yield_s: float = 1.0,
        max_yield_s: float = 3.0,
    ) -> None:
        self._child = child
        self._min = min_s
        self._max = max_s
        self._min_yield = min_yield_s
        self._max_yield = max_yield_s
        self._budget: float = 0.0
        self._elapsed: float = 0.0
        self._has_budget: bool = False
        self._yield_remaining: float = 0.0

    def tick(self, ctx: "CursorContext", delta_s: float) -> Optional[BTResult]:
        # During yield pause — stay dark; don't tick child
        if self._yield_remaining > 0.0:
            self._yield_remaining = max(0.0, self._yield_remaining - delta_s)
            return None

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
                self._yield_remaining = random.uniform(self._min_yield, self._max_yield)
                _log.debug("BTRandomDwell: budget expired, yielding %.1fs",
                           self._yield_remaining)
                return None
            return result
        # Child not active — reset everything including any pending pause
        self._elapsed = 0.0
        self._budget = 0.0
        self._has_budget = False
        self._yield_remaining = 0.0
        return None
