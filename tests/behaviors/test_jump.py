from barkoder.behaviors.jump import JumpBehavior
from barkoder.tracker import CursorContext


def ctx(**kw):
    d = dict(cursor_x=500, cursor_y=100, dog_x=200, dog_y=900,
             horizontal_distance=300, move_direction="east",
             bark_direction_4="east", cursor_idle_seconds=10,
             running_seconds=0, run_threshold=15)
    d.update(kw)
    return CursorContext(**d)


def test_jump_does_not_enter_when_cursor_active():
    b = JumpBehavior(trigger_chance_per_s=1.0)  # max probability
    # cursor is active (idle_s=1, not > 5) → should never enter
    for _ in range(100):
        assert not b.should_enter(ctx(cursor_idle_seconds=1, horizontal_distance=300))


def test_jump_does_not_enter_when_cursor_close():
    b = JumpBehavior(trigger_chance_per_s=1.0)
    # cursor is idle but close (< 200px) → should not enter
    for _ in range(100):
        assert not b.should_enter(ctx(cursor_idle_seconds=10, horizontal_distance=150))


def test_jump_stays_active_until_finished():
    b = JumpBehavior()
    b._active = True
    # always returns True while active, regardless of context
    assert b.should_enter(ctx(cursor_idle_seconds=0, horizontal_distance=50))


def test_jump_exits_after_notify():
    b = JumpBehavior()
    b._active = True
    b.notify_animation_finished()
    assert not b._active
    # should_enter now follows probability (not staying active)
    # With very low chance per tick, expect False essentially always
    b._chance = 0.0
    assert not b.should_enter(ctx())


def test_jump_returns_jump_animation():
    b = JumpBehavior()
    b._active = True
    b._direction = "east"
    req, delta = b.update(ctx())
    assert req.animation == "Jump"
    assert req.direction == "east"
    assert delta == 0.0


def test_jump_on_exit_clears_active():
    b = JumpBehavior()
    b._active = True
    b.on_exit(ctx())
    assert not b._active
