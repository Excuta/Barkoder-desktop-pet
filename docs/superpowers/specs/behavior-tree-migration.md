# Behavior Tree Migration Design Spec

## 1. Current Architecture

The current `StateMachine` (in `src/barkoder/state_machine.py`) evaluates behaviors in priority order, calling `should_enter()` on each until a winner is found. The winner runs until preempted. Three per-behavior attributes (`min_dwell_s`, `max_dwell_s`, `exit_cooldown_s`) handle timing and re-entry blocking — these are the FSM's approximation of BT decorators.

## 2. Why Migrate

The FSM encodes tree structure implicitly (via priority numbers). Adding multi-step sequences (e.g., ArrivalSit → force-Wander) requires wiring callbacks in `app.py` rather than expressing the sequence declaratively. As behaviors become more interdependent, the priority list becomes harder to reason about.

## 3. Target Architecture

### BTNode ABC

File: `src/barkoder/bt/node.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class BTResult:
    request: "AnimationRequest"
    delta_x: float
    success: bool  # True = still running/succeeded, False = failed

class BTNode(ABC):
    @abstractmethod
    def tick(self, ctx: "CursorContext", delta_s: float) -> Optional[BTResult]:
        ...  # None = failure / not running
```

### Leaf Node

```python
class BTLeaf(BTNode):
    def __init__(self, behavior: Behavior) -> None:
        self._b = behavior
        self._active = False

    def tick(self, ctx, delta_s):
        if not self._b.should_enter(ctx):
            if self._active:
                self._b.on_exit(ctx)
                self._active = False
            return None
        if not self._active:
            self._b.on_enter(ctx)
            self._active = True
        req, dx = self._b.update(ctx)
        return BTResult(req, dx, True)
```

### Selector

Tries children in order, returns first success:

```python
class BTSelector(BTNode):
    def __init__(self, children: list[BTNode]) -> None:
        self._children = children
        self._running: Optional[BTNode] = None

    def tick(self, ctx, delta_s):
        for child in self._children:
            result = child.tick(ctx, delta_s)
            if result is not None:
                self._running = child
                return result
        self._running = None
        return None
```

### Sequence

Runs children in order, fails if any fails:

```python
class BTSequence(BTNode):
    def __init__(self, children: list[BTNode]) -> None:
        self._children = children
        self._index = 0

    def tick(self, ctx, delta_s):
        while self._index < len(self._children):
            result = self._children[self._index].tick(ctx, delta_s)
            if result is None:  # child failed
                self._index = 0
                return None
            if result.success:
                return result  # still running
            self._index += 1  # child succeeded, advance
        self._index = 0
        return None  # all done
```

### Cooldown Decorator

Blocks re-entry of child for `cooldown_s` after it exits:

```python
class BTCooldown(BTNode):
    def __init__(self, child: BTNode, cooldown_s: float) -> None:
        self._child = child
        self._cooldown_s = cooldown_s
        self._remaining: float = 0.0

    def tick(self, ctx, delta_s):
        self._remaining = max(0.0, self._remaining - delta_s)
        if self._remaining > 0:
            return None
        result = self._child.tick(ctx, delta_s)
        if result is None and self._remaining == 0.0:
            self._remaining = self._cooldown_s
        return result
```

### Random Dwell Decorator

Holds child running for a random duration:

```python
class BTRandomDwell(BTNode):
    def __init__(self, child: BTNode, min_s: float, max_s: float) -> None:
        self._child = child
        self._min = min_s
        self._max = max_s
        self._budget: float = 0.0
        self._elapsed: float = 0.0

    def tick(self, ctx, delta_s):
        result = self._child.tick(ctx, delta_s)
        if result is not None:
            self._elapsed += delta_s
            if self._budget == 0.0:
                self._budget = random.uniform(self._min, self._max)
            if self._elapsed >= self._budget:
                self._elapsed = 0.0
                self._budget = 0.0
                return None  # budget expired, yield
            return result
        self._elapsed = 0.0
        self._budget = 0.0
        return None
```

## 4. Example Behavior Tree

```
Selector (root)
├── BTLeaf(PantBehavior)
├── BTCooldown(BTLeaf(BarkWalkBehavior), 6s)
├── BTSequence
│   ├── BTLeaf(ArrivalSitBehavior)
│   └── BTRandomDwell(BTLeaf(WanderBehavior), 5s, 10s)
├── BTRandomDwell(BTLeaf(RunBehavior), 3s, 8s)
├── BTRandomDwell(BTLeaf(WalkBehavior), 3s, 8s)
├── BTRandomDwell(BTLeaf(WanderBehavior), 5s, 10s)
├── BTRandomDwell(BTLeaf(IdleSitBehavior), 5s, 15s)
└── BTLeaf(IdleBehavior)
```

Note: `WanderBehavior`'s `force_start()` is replaced by the BTSequence — when ArrivalSit succeeds (hold_done), the sequence advances to Wander automatically, no callback needed in `app.py`.

## 5. Migration Path

1. Create `src/barkoder/bt/` package with `node.py`, `leaf.py`, `selector.py`, `sequence.py`, `decorator.py`
2. All existing `Behavior` subclasses are unchanged — they become BTLeaf children
3. Replace `StateMachine` in `app.py` with `BehaviorTree(root_node)` — same `tick(ctx, delta_s)` interface
4. Remove per-behavior `min_dwell_s`/`max_dwell_s`/`exit_cooldown_s` class attrs (replaced by BT decorators)
5. Remove `wander_b.force_start()` callback from `app.py` (replaced by BTSequence)
6. Remove `arrival_sit_b._triggered` manipulation from `app.py` (BTSequence handles sequencing)

The `Behavior` ABC interface (`should_enter`, `on_enter`, `on_exit`, `update`) is unchanged throughout.

## 6. When to Migrate

Recommended trigger: when adding a third multi-step behavior chain, OR when priority ordering requires more than 8 behaviors. The current implementation (per-behavior dwell + cooldown in FSM) handles the current feature set cleanly.
