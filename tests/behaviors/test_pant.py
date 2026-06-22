import random
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
    return PantBehavior(pant_cycles_required=2)


def test_pant_does_not_enter_when_not_forced():
    b = make_pant()
    b._interval_remaining = 0.0
    assert not b.should_enter(ctx())


def test_pant_enters_when_forced_and_interval_expired():
    b = make_pant()
    b.force_pant()  # sets _forced=True and _interval_remaining=0
    assert b.should_enter(ctx())


def test_pant_does_not_enter_when_forced_but_interval_not_expired():
    b = make_pant()
    b._forced = True
    b._interval_remaining = 10.0
    assert not b.should_enter(ctx())


def test_pant_on_enter_rolls_cycles(monkeypatch):
    b = make_pant()
    monkeypatch.setattr(random, "randint", lambda a, b_: 4)
    b.on_enter(ctx())
    assert b._target_cycles == 4


def test_pant_increments_cycle_when_animation_finishes():
    b = make_pant()
    b.on_enter(ctx())
    b.notify_animation_finished()
    assert b._cycles_done == 1


def test_pant_done_when_cycles_exhausted():
    b = make_pant()
    b._target_cycles = 1
    b.notify_animation_finished()
    assert b._done is True


def test_pant_not_done_before_cycles_exhausted():
    b = make_pant()
    b._target_cycles = 3
    b.notify_animation_finished()
    assert b._done is False


def test_pant_returns_pant_animation():
    b = make_pant()
    b.on_enter(ctx(move_direction="east"))
    req, delta = b.update(ctx())
    assert req.animation == "Pant"
    assert req.direction == "east"
    assert delta == 0.0
