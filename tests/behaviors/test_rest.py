from barkoder.behaviors.rest import RestBehavior
from barkoder.tracker import CursorContext


def ctx(**kw):
    d = dict(cursor_x=300, cursor_y=100, dog_x=200, dog_y=900,
             horizontal_distance=200, move_direction="east",
             bark_direction_4="east", cursor_idle_seconds=0,
             running_seconds=0, run_threshold=15)
    d.update(kw)
    return CursorContext(**d)


def test_rest_enters_when_cursor_idle_long():
    b = RestBehavior(rest_threshold_s=60.0)
    assert b.should_enter(ctx(cursor_idle_seconds=65))


def test_rest_does_not_enter_when_cursor_active():
    b = RestBehavior(rest_threshold_s=60.0)
    assert not b.should_enter(ctx(cursor_idle_seconds=30))


def test_rest_at_exact_threshold_does_not_enter():
    b = RestBehavior(rest_threshold_s=60.0)
    assert not b.should_enter(ctx(cursor_idle_seconds=60.0))


def test_rest_returns_rest_animation():
    b = RestBehavior(rest_threshold_s=60.0)
    b.on_enter(ctx(bark_direction_4="west"))
    req, delta = b.update(ctx())
    assert req.animation == "Rest"
    assert delta == 0.0


def test_rest_faces_cursor_direction_on_enter():
    b = RestBehavior(rest_threshold_s=60.0)
    b.on_enter(ctx(bark_direction_4="west"))
    req, _ = b.update(ctx())
    assert req.direction == "west"
