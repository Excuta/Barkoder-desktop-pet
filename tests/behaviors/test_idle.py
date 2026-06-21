from barkoder.behaviors.idle import IdleBehavior
from barkoder.tracker import CursorContext
import dataclasses


def ctx(**kw):
    d = dict(cursor_x=500, cursor_y=100, dog_x=200, dog_y=900,
             horizontal_distance=300, move_direction="east",
             bark_direction_4="north", cursor_idle_seconds=0,
             running_seconds=0, run_threshold=15)
    d.update(kw)
    return CursorContext(**d)


def test_idle_always_enters():
    b = IdleBehavior()
    assert b.should_enter(ctx())


def test_idle_plays_idle_animation():
    b = IdleBehavior()
    req, delta = b.update(ctx(move_direction="west"))
    assert req.animation == "Idle"
    assert req.direction == "west"
    assert delta == 0.0
