from barkoder.behaviors.idle_sit import IdleSitBehavior
from barkoder.tracker import CursorContext


def ctx(**kw):
    d = dict(cursor_x=500, cursor_y=100, dog_x=200, dog_y=900,
             horizontal_distance=300, move_direction="east",
             bark_direction_4="north", cursor_idle_seconds=0,
             running_seconds=0, run_threshold=15)
    d.update(kw)
    return CursorContext(**d)


def test_idle_sit_enters_after_long_idle():
    b = IdleSitBehavior(sit_threshold_s=15.0)
    assert b.should_enter(ctx(cursor_idle_seconds=20.0))


def test_idle_sit_does_not_enter_before_threshold():
    b = IdleSitBehavior(sit_threshold_s=15.0)
    assert not b.should_enter(ctx(cursor_idle_seconds=10.0))


def test_idle_sit_returns_sit_in_cursor_direction():
    b = IdleSitBehavior(sit_threshold_s=15.0)
    req, delta = b.update(ctx(bark_direction_4="south"))
    assert req.animation == "Sit"
    assert req.direction == "south"
    assert delta == 0.0
