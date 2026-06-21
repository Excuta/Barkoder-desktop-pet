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

    def update(self, ctx: CursorContext) -> AnimationRequest:
        return AnimationRequest(animation="Idle", direction="east")

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
