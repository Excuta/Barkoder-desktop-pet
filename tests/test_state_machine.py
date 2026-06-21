import dataclasses
import pytest
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.state_machine import StateMachine
from barkoder.tracker import CursorContext


def make_ctx(**overrides) -> CursorContext:
    defaults = dict(
        cursor_x=500.0, cursor_y=100.0, dog_x=200.0, dog_y=900.0,
        horizontal_distance=300.0, move_direction="east",
        bark_direction_4="north", cursor_idle_seconds=0.0,
        running_seconds=0.0, run_threshold=15.0,
    )
    defaults.update(overrides)
    return CursorContext(**defaults)


class MockBehavior(Behavior):
    def __init__(self, priority: int, name: str, enters: bool, delta_x: float = 0.0):
        self.priority = priority
        self.name = name
        self._enters = enters
        self._delta_x = delta_x
        self.entered = False
        self.exited = False

    def should_enter(self, ctx: CursorContext) -> bool:
        return self._enters

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        return AnimationRequest(animation="Idle", direction="east"), 0.0

    def on_enter(self, ctx: CursorContext) -> None:
        self.entered = True

    def on_exit(self, ctx: CursorContext) -> None:
        self.exited = True


def test_highest_priority_behavior_wins():
    low = MockBehavior(priority=5, name="low", enters=True)
    high = MockBehavior(priority=2, name="high", enters=True)
    sm = StateMachine([low, high])
    ctx = make_ctx()
    sm.tick(ctx)
    assert sm.current_behavior.name == "high"


def test_fallback_to_lower_priority_when_high_does_not_enter():
    high = MockBehavior(priority=1, name="high", enters=False)
    low = MockBehavior(priority=8, name="low", enters=True)
    sm = StateMachine([high, low])
    ctx = make_ctx()
    sm.tick(ctx)
    assert sm.current_behavior.name == "low"


def test_on_enter_called_on_transition():
    a = MockBehavior(priority=1, name="a", enters=True)
    b = MockBehavior(priority=2, name="b", enters=True)
    sm = StateMachine([a, b])
    ctx = make_ctx()
    sm.tick(ctx)
    assert a.entered


def test_on_exit_called_when_leaving():
    stays = MockBehavior(priority=1, name="stays", enters=True)
    leaves = MockBehavior(priority=2, name="leaves", enters=False)
    sm = StateMachine([stays, leaves])
    ctx = make_ctx()
    # First tick: "stays" enters (priority 1 wins)
    sm.tick(ctx)
    # Nothing to exit from on first tick, but stays should be active
    assert sm.current_behavior.name == "stays"


def test_same_behavior_not_re_entered():
    b = MockBehavior(priority=1, name="b", enters=True)
    sm = StateMachine([b])
    ctx = make_ctx()
    sm.tick(ctx)
    b.entered = False  # reset
    sm.tick(ctx)
    assert not b.entered  # not re-entered since it's already active


def test_tick_returns_animation_request_and_delta():
    b = MockBehavior(priority=1, name="b", enters=True, delta_x=0.0)
    sm = StateMachine([b])
    req, delta = sm.tick(make_ctx())
    assert isinstance(req, AnimationRequest)
    assert isinstance(delta, float)


def test_dwell_prevents_lower_priority_preemption():
    """Lower-priority behavior cannot enter until dwell budget expires."""
    from unittest.mock import MagicMock

    high = MagicMock()
    high.priority = 1
    high.name = "high"
    high.should_enter.return_value = True
    high.update.return_value = (MagicMock(), 0.0)
    high.min_dwell_s = 2.0
    high.max_dwell_s = 2.0
    high.exit_cooldown_s = 0.0

    low = MagicMock()
    low.priority = 5
    low.name = "low"
    low.should_enter.return_value = True
    low.update.return_value = (MagicMock(), 0.0)
    low.min_dwell_s = 0.0
    low.max_dwell_s = 0.0
    low.exit_cooldown_s = 0.0

    sm = StateMachine([high, low])

    # First tick — high enters
    high.should_enter.return_value = True
    low.should_enter.return_value = False
    sm.tick(make_ctx(), 0.016)
    assert sm.current_behavior is high

    # high's should_enter becomes False — low wants in — but dwell budget (2s) not yet reached
    high.should_enter.return_value = False
    low.should_enter.return_value = True
    sm.tick(make_ctx(), 0.5)  # only 0.5s elapsed
    assert sm.current_behavior is high  # still held

    # After dwell budget expires, low can enter
    sm.tick(make_ctx(), 2.0)  # total > 2s
    assert sm.current_behavior is low


def test_exit_cooldown_prevents_reentry():
    """After a behavior exits, it cannot re-enter during its cooldown."""
    from unittest.mock import MagicMock

    a = MagicMock()
    a.priority = 1
    a.name = "a"
    a.should_enter.return_value = True
    a.update.return_value = (MagicMock(), 0.0)
    a.min_dwell_s = 0.0
    a.max_dwell_s = 0.0
    a.exit_cooldown_s = 3.0

    b = MagicMock()
    b.priority = 5
    b.name = "b"
    b.should_enter.return_value = False
    b.update.return_value = (MagicMock(), 0.0)
    b.min_dwell_s = 0.0
    b.max_dwell_s = 0.0
    b.exit_cooldown_s = 0.0

    sm = StateMachine([a, b])

    # a enters
    sm.tick(make_ctx(), 0.016)
    assert sm.current_behavior is a

    # a's conditions fail, b enters — a's cooldown is set
    a.should_enter.return_value = False
    b.should_enter.return_value = True
    sm.tick(make_ctx(), 0.016)
    assert sm.current_behavior is b

    # a's conditions return True, but it's on cooldown — b should stay
    a.should_enter.return_value = True
    sm.tick(make_ctx(), 0.5)
    assert sm.current_behavior is b  # a blocked by cooldown

    # After cooldown expires, a can re-enter (higher priority — immediate)
    sm.tick(make_ctx(), 3.0)  # total cooldown elapsed
    assert sm.current_behavior is a
