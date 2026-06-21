import pytest
from unittest.mock import MagicMock
from barkoder.behaviors.pant import PantBehavior
from barkoder.tracker import CursorContext


def ctx(**kw):
    d = dict(cursor_x=500, cursor_y=100, dog_x=200, dog_y=900,
             horizontal_distance=300, move_direction="east",
             bark_direction_4="north", cursor_idle_seconds=0,
             running_seconds=0, run_threshold=12.0)
    d.update(kw)
    return CursorContext(**d)


def make_pant():
    sm = MagicMock()
    return PantBehavior(sm=sm, min_cycles=3, max_cycles=5), sm


def test_pant_enters_when_running_exceeds_threshold():
    b, _ = make_pant()
    assert b.should_enter(ctx(running_seconds=13.0, run_threshold=12.0))


def test_pant_does_not_enter_when_below_threshold():
    b, _ = make_pant()
    assert not b.should_enter(ctx(running_seconds=5.0, run_threshold=12.0))


def test_pant_on_enter_rolls_cycles(monkeypatch):
    b, _ = make_pant()
    import random
    monkeypatch.setattr(random, "randint", lambda a, b_: 4)
    b.on_enter(ctx())
    assert b._cycles_remaining == 4


def test_pant_decrements_cycle_when_animation_finishes():
    b, sm = make_pant()
    b._cycles_remaining = 3
    b._notify_cycle_done()
    assert b._cycles_remaining == 2


def test_pant_exits_sm_when_cycles_exhausted():
    b, sm = make_pant()
    b._cycles_remaining = 1
    b._notify_cycle_done()
    sm.reset_running_time.assert_called_once()


def test_pant_returns_pant_animation():
    b, _ = make_pant()
    b._cycles_remaining = 2
    req, delta = b.update(ctx(move_direction="east"))
    assert req.animation == "Pant"
    assert req.direction == "east"
    assert delta == 0.0
