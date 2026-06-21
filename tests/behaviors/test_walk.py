import pytest
from barkoder.behaviors.walk import WalkBehavior
from barkoder.tracker import CursorContext


def ctx(**kw):
    d = dict(cursor_x=500, cursor_y=100, dog_x=200, dog_y=900,
             horizontal_distance=300, move_direction="east",
             bark_direction_4="north", cursor_idle_seconds=0,
             running_seconds=0, run_threshold=15)
    d.update(kw)
    return CursorContext(**d)


def test_walk_enters_when_beyond_near_threshold():
    b = WalkBehavior(near_x_px=80.0, walk_speed_px=2.5)
    assert b.should_enter(ctx(horizontal_distance=100))


def test_walk_does_not_enter_when_within_near_threshold():
    b = WalkBehavior(near_x_px=80.0, walk_speed_px=2.5)
    assert not b.should_enter(ctx(horizontal_distance=50))


def test_walk_moves_east():
    b = WalkBehavior(near_x_px=80.0, walk_speed_px=2.5)
    req, delta = b.update(ctx(move_direction="east"))
    assert req.animation == "Walk"
    assert req.direction == "east"
    assert delta == pytest.approx(2.5)


def test_walk_moves_west():
    b = WalkBehavior(near_x_px=80.0, walk_speed_px=2.5)
    req, delta = b.update(ctx(move_direction="west"))
    assert delta == pytest.approx(-2.5)
