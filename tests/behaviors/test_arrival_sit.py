import pytest
from barkoder.behaviors.arrival_sit import ArrivalSitBehavior
from barkoder.tracker import CursorContext


def ctx(**kw):
    d = dict(cursor_x=220, cursor_y=100, dog_x=200, dog_y=900,
             horizontal_distance=20, move_direction="east",
             bark_direction_4="north", cursor_idle_seconds=0,
             running_seconds=0, run_threshold=15)
    d.update(kw)
    return CursorContext(**d)


def test_arrival_enters_when_within_arrival_px():
    b = ArrivalSitBehavior(arrival_x_px=50.0, sit_hold_seconds=1.5)
    assert b.should_enter(ctx(horizontal_distance=30))


def test_arrival_does_not_enter_when_too_far():
    b = ArrivalSitBehavior(arrival_x_px=50.0, sit_hold_seconds=1.5)
    assert not b.should_enter(ctx(horizontal_distance=80))


def test_arrival_is_oneshot():
    b = ArrivalSitBehavior(arrival_x_px=50.0, sit_hold_seconds=1.5)
    b.on_enter(ctx())
    assert b.should_enter(ctx(horizontal_distance=20))  # triggered once
    b._triggered = True
    assert not b.should_enter(ctx(horizontal_distance=20))


def test_arrival_returns_sit_animation():
    b = ArrivalSitBehavior(arrival_x_px=50.0, sit_hold_seconds=1.5)
    b.on_enter(ctx())
    req, delta = b.update(ctx(bark_direction_4="west"))
    assert req.animation == "Sit"
    assert req.direction == "west"
    assert delta == 0.0


def test_arrival_resets_on_exit():
    b = ArrivalSitBehavior(arrival_x_px=50.0, sit_hold_seconds=1.5)
    b._triggered = True
    b.on_exit(ctx())
    assert not b._triggered
