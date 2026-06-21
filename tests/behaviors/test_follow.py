import pytest
from barkoder.behaviors.follow import FollowBehavior
from barkoder.tracker import CursorContext


def ctx(**kw):
    d = dict(cursor_x=300, cursor_y=100, dog_x=200, dog_y=900,
             horizontal_distance=100, move_direction="east",
             bark_direction_4="east", cursor_idle_seconds=0,
             running_seconds=0, run_threshold=15)
    d.update(kw)
    return CursorContext(**d)


class FakeSM:
    def __init__(self):
        self.run_threshold = 15.0
        self.running_seconds = 0.0
        self.reset_count = 0
        self.set_count = 0

    def set_run_threshold(self, v):
        self.run_threshold = v
        self.set_count += 1

    def reset_running_time(self):
        self.running_seconds = 0.0
        self.reset_count += 1


def make_follow(**kw):
    defaults = dict(
        near_x_px=100, far_x_px=280,
        walk_speed_px=1.2, run_speed_px=2.8,
        follow_window_s=5.0,
        min_run_s=7.0, max_run_s=13.0,
        sm=FakeSM(),
    )
    defaults.update(kw)
    return FollowBehavior(**defaults)


def test_follow_enters_when_cursor_active_and_far():
    b = make_follow()
    assert b.should_enter(ctx(horizontal_distance=150, cursor_idle_seconds=0))


def test_follow_does_not_enter_when_cursor_at_threshold():
    b = make_follow()
    assert not b.should_enter(ctx(horizontal_distance=100, cursor_idle_seconds=0))


def test_follow_ignores_idle_cursor():
    b = make_follow()
    # cursor_idle > follow_window (5s) → should not enter regardless of distance
    assert not b.should_enter(ctx(horizontal_distance=300, cursor_idle_seconds=10))


def test_follow_hysteresis_stays_until_very_close():
    b = make_follow()
    b._following = True
    # dist=60 is above 40% of 100px exit threshold (40px) → stays active
    assert b.should_enter(ctx(horizontal_distance=60, cursor_idle_seconds=0))


def test_follow_exits_when_close_enough():
    b = make_follow()
    b._following = True
    # dist=35 is below 40px exit threshold → exits
    assert not b.should_enter(ctx(horizontal_distance=35, cursor_idle_seconds=0))


def test_follow_exits_when_cursor_settles_even_if_far():
    b = make_follow()
    b._following = True
    assert not b.should_enter(ctx(horizontal_distance=300, cursor_idle_seconds=8))


def test_follow_returns_walk_when_near():
    b = make_follow()
    req, delta = b.update(ctx(horizontal_distance=150, move_direction="east"))
    assert req.animation == "Walk"
    assert req.direction == "east"
    assert delta > 0


def test_follow_returns_run_when_far():
    b = make_follow()
    req, delta = b.update(ctx(horizontal_distance=320, move_direction="east"))
    assert req.animation == "Run"
    assert delta > 0


def test_follow_moves_west_correctly():
    b = make_follow()
    req, delta = b.update(ctx(horizontal_distance=150, move_direction="west"))
    assert req.animation == "Walk"
    assert delta < 0


def test_follow_sets_run_threshold_on_enter_when_running():
    sm = FakeSM()
    b = make_follow(sm=sm)
    b.on_enter(ctx(horizontal_distance=350))
    assert sm.set_count == 1


def test_follow_skips_run_threshold_when_walking():
    sm = FakeSM()
    b = make_follow(sm=sm)
    b.on_enter(ctx(horizontal_distance=150))
    assert sm.set_count == 0


def test_follow_resets_running_on_exit():
    sm = FakeSM()
    b = make_follow(sm=sm)
    b._following = True
    b.on_exit(ctx())
    assert sm.reset_count == 1
    assert not b._following
