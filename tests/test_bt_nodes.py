"""Tests for behavior tree node infrastructure."""
from __future__ import annotations

import random
from unittest.mock import MagicMock, call

import pytest

from barkoder.bt import BTLeaf, BTSelector, BTCooldown, BTRandomDwell, BTResult
from barkoder.tracker import CursorContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ctx(**overrides) -> CursorContext:
    defaults = dict(
        cursor_x=500.0, cursor_y=100.0, dog_x=200.0, dog_y=900.0,
        horizontal_distance=300.0, move_direction="east",
        bark_direction_4="north", cursor_idle_seconds=0.0,
        running_seconds=0.0, run_threshold=15.0,
    )
    defaults.update(overrides)
    return CursorContext(**defaults)


def make_behavior(enters: bool = True, delta_x: float = 0.0) -> MagicMock:
    b = MagicMock()
    b.should_enter.return_value = enters
    b.update.return_value = (MagicMock(), delta_x)
    b.name = "test"
    return b


CTX = make_ctx()
DT = 0.016  # ~60 fps delta


# ---------------------------------------------------------------------------
# BTLeaf
# ---------------------------------------------------------------------------

def test_leaf_activates_when_should_enter_true():
    b = make_behavior(enters=True)
    leaf = BTLeaf(b)
    result = leaf.tick(CTX, DT)
    assert result is not None
    assert isinstance(result, BTResult)
    assert result.running is True


def test_leaf_deactivates_when_should_enter_false():
    b = make_behavior(enters=True)
    leaf = BTLeaf(b)

    # First tick: becomes active
    leaf.tick(CTX, DT)
    assert leaf._active

    # Second tick: should_enter is now False
    b.should_enter.return_value = False
    result = leaf.tick(CTX, DT)

    assert result is None
    assert not leaf._active
    b.on_exit.assert_called_once_with(CTX)


def test_leaf_calls_on_enter_once():
    b = make_behavior(enters=True)
    leaf = BTLeaf(b)

    # Tick 3 times while active
    leaf.tick(CTX, DT)
    leaf.tick(CTX, DT)
    leaf.tick(CTX, DT)

    b.on_enter.assert_called_once_with(CTX)


# ---------------------------------------------------------------------------
# BTSelector
# ---------------------------------------------------------------------------

def test_selector_returns_first_active():
    # Three leaves; first two return None (should_enter=False), third is active
    b1 = make_behavior(enters=False)
    b2 = make_behavior(enters=False)
    b3 = make_behavior(enters=True, delta_x=5.0)

    selector = BTSelector([BTLeaf(b1), BTLeaf(b2), BTLeaf(b3)])
    result = selector.tick(CTX, DT)

    assert result is not None
    assert result.running is True
    assert result.delta_x == 5.0


def test_selector_returns_none_when_all_fail():
    b1 = make_behavior(enters=False)
    b2 = make_behavior(enters=False)
    b3 = make_behavior(enters=False)

    selector = BTSelector([BTLeaf(b1), BTLeaf(b2), BTLeaf(b3)])
    result = selector.tick(CTX, DT)

    assert result is None


# ---------------------------------------------------------------------------
# BTCooldown
# ---------------------------------------------------------------------------

def test_cooldown_blocks_after_exit():
    b = make_behavior(enters=True)
    leaf = BTLeaf(b)
    cooldown_s = 3.0
    node = BTCooldown(leaf, cooldown_s)

    # Tick 1: child becomes active
    r1 = node.tick(CTX, DT)
    assert r1 is not None

    # Tick 2: child still active
    r2 = node.tick(CTX, DT)
    assert r2 is not None

    # Child exits (should_enter → False)
    b.should_enter.return_value = False
    r3 = node.tick(CTX, 0.0)  # child exits; cooldown starts
    assert r3 is None
    assert node._remaining == cooldown_s

    # During cooldown — child would re-enter but is blocked
    b.should_enter.return_value = True
    r4 = node.tick(CTX, 1.0)   # 2s remaining
    assert r4 is None
    assert abs(node._remaining - 2.0) < 1e-9

    r5 = node.tick(CTX, 1.5)   # 0.5s remaining
    assert r5 is None

    # Cooldown expires — drains remaining 0.5s; remaining reaches 0 this tick,
    # but the guard (self._remaining > 0) fires before the subtraction, so the
    # child is NOT ticked yet; it resumes on the NEXT tick.
    r6 = node.tick(CTX, 1.0)   # remaining: 0.5 → 0
    assert r6 is None
    assert node._remaining == 0.0

    # Next tick after cooldown cleared — child active again
    r7 = node.tick(CTX, DT)
    assert r7 is not None


def test_cooldown_no_block_if_never_active():
    b = make_behavior(enters=False)
    leaf = BTLeaf(b)
    node = BTCooldown(leaf, cooldown_s=5.0)

    # Tick many times; child never activates — cooldown must never fire
    for _ in range(10):
        result = node.tick(CTX, 1.0)
        assert result is None

    assert node._remaining == 0.0
    assert node._was_active is False


# ---------------------------------------------------------------------------
# BTRandomDwell
# ---------------------------------------------------------------------------

def test_random_dwell_holds_child():
    b = make_behavior(enters=True)
    leaf = BTLeaf(b)
    # Disable yield pause for this test to isolate budget behaviour
    node = BTRandomDwell(leaf, min_s=2.0, max_s=2.0, min_yield_s=0.0, max_yield_s=0.0)

    # Tick 1 at t=0.0 — budget is set to 2.0, elapsed becomes 1.0
    r1 = node.tick(CTX, 1.0)
    assert r1 is not None
    assert node._has_budget is True
    assert node._budget == 2.0
    assert node._elapsed == 1.0

    # Tick 2 at t=1.0 — elapsed becomes 2.0 == budget → yields
    r2 = node.tick(CTX, 1.0)
    assert r2 is None
    assert node._has_budget is False
    assert node._elapsed == 0.0
    assert node._yield_remaining == 0.0  # no pause (disabled in test)


def test_random_dwell_yield_pause_blocks_reentry():
    b = make_behavior(enters=True)
    leaf = BTLeaf(b)
    # budget=1s expires immediately, yield pause=2s (deterministic)
    node = BTRandomDwell(leaf, min_s=1.0, max_s=1.0, min_yield_s=2.0, max_yield_s=2.0)

    r1 = node.tick(CTX, 1.0)   # budget starts AND expires in same tick
    assert r1 is None           # expired; yield pause begins
    assert node._yield_remaining == 2.0
    assert node._has_budget is False

    r2 = node.tick(CTX, 1.0)   # 1s into 2s pause — still dark
    assert r2 is None
    assert node._yield_remaining == 1.0

    r3 = node.tick(CTX, 1.0)   # pause drains to 0 this tick
    assert r3 is None
    assert node._yield_remaining == 0.0

    r4 = node.tick(CTX, 0.016)  # pause over — child ticked normally again
    assert r4 is not None


def test_random_dwell_resets_on_child_failure():
    b = make_behavior(enters=True)
    leaf = BTLeaf(b)
    node = BTRandomDwell(leaf, min_s=5.0, max_s=5.0, min_yield_s=0.0, max_yield_s=0.0)

    # Tick once to set budget and accrue elapsed
    node.tick(CTX, 1.0)
    assert node._has_budget is True
    assert node._budget == 5.0
    assert node._elapsed == 1.0

    # Child now stops entering mid-budget
    b.should_enter.return_value = False
    result = node.tick(CTX, 1.0)

    assert result is None
    assert node._has_budget is False
    assert node._elapsed == 0.0
    assert node._yield_remaining == 0.0
