import pytest
from barkoder.behaviors.bark_walk import BarkWalkBehavior
from barkoder.tracker import CursorContext


def ctx(**kw):
    d = dict(cursor_x=250, cursor_y=100, dog_x=200, dog_y=900,
             horizontal_distance=50, move_direction="east",
             bark_direction_4="north", cursor_idle_seconds=0.5,
             running_seconds=0, run_threshold=15)
    d.update(kw)
    return CursorContext(**d)


def test_barkwalk_enters_when_near_and_cursor_active():
    b = BarkWalkBehavior(near_x_px=80.0, bark_active_window_s=2.0)
    assert b.should_enter(ctx(horizontal_distance=50, cursor_idle_seconds=0.5))


def test_barkwalk_does_not_enter_when_too_far():
    b = BarkWalkBehavior(near_x_px=80.0, bark_active_window_s=2.0)
    assert not b.should_enter(ctx(horizontal_distance=100))


def test_barkwalk_does_not_enter_when_cursor_idle():
    b = BarkWalkBehavior(near_x_px=80.0, bark_active_window_s=2.0)
    assert not b.should_enter(ctx(cursor_idle_seconds=5.0))


def test_barkwalk_first_update_returns_bark():
    b = BarkWalkBehavior(near_x_px=80.0, bark_active_window_s=2.0)
    b.on_enter(ctx())
    req, _ = b.update(ctx(bark_direction_4="north"))
    assert req.animation == "Bark"
    assert req.direction == "north"


def test_barkwalk_after_bark_done_returns_walk():
    b = BarkWalkBehavior(near_x_px=80.0, bark_active_window_s=2.0)
    b.on_enter(ctx())
    b.notify_animation_finished()  # bark done
    req, delta = b.update(ctx(move_direction="east"))
    assert req.animation == "Walk"
    assert delta > 0


def test_barkwalk_bark_direction_follows_cursor():
    b = BarkWalkBehavior(near_x_px=80.0, bark_active_window_s=2.0)
    b.on_enter(ctx())
    req, _ = b.update(ctx(bark_direction_4="west"))
    assert req.direction == "west"
