import pytest
from barkoder.behaviors.wander import WanderBehavior
from barkoder.tracker import CursorContext


def ctx(**kw):
    d = dict(cursor_x=500, cursor_y=100, dog_x=200, dog_y=900,
             horizontal_distance=300, move_direction="east",
             bark_direction_4="north", cursor_idle_seconds=0,
             running_seconds=0, run_threshold=15)
    d.update(kw)
    return CursorContext(**d)


def test_wander_enters_when_cursor_idle_enough():
    b = WanderBehavior(wander_threshold_s=6.0, walk_speed_px=2.5, screen_width=1920)
    assert b.should_enter(ctx(cursor_idle_seconds=7.0))


def test_wander_does_not_enter_before_threshold():
    b = WanderBehavior(wander_threshold_s=6.0, walk_speed_px=2.5, screen_width=1920)
    assert not b.should_enter(ctx(cursor_idle_seconds=3.0))


def test_wander_exits_when_cursor_moves():
    b = WanderBehavior(wander_threshold_s=6.0, walk_speed_px=2.5, screen_width=1920)
    assert not b.should_enter(ctx(cursor_idle_seconds=1.0))


def test_wander_on_enter_starts_walking():
    b = WanderBehavior(wander_threshold_s=6.0, walk_speed_px=2.5, screen_width=1920)
    b.on_enter(ctx())
    req, delta = b.update(ctx(dog_x=200))
    assert req.animation == "Walk"


def test_wander_returns_walk_animation():
    b = WanderBehavior(wander_threshold_s=6.0, walk_speed_px=2.5, screen_width=1920)
    b.on_enter(ctx())
    b._target_x = 500.0
    req, delta = b.update(ctx(dog_x=200))
    assert req.animation == "Walk"
    assert delta != 0.0
