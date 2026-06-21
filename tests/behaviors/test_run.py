import pytest
from unittest.mock import MagicMock
from barkoder.behaviors.run import RunBehavior
from barkoder.tracker import CursorContext


def ctx(**kw):
    d = dict(cursor_x=600, cursor_y=100, dog_x=200, dog_y=900,
             horizontal_distance=400, move_direction="east",
             bark_direction_4="north", cursor_idle_seconds=0,
             running_seconds=0, run_threshold=15)
    d.update(kw)
    return CursorContext(**d)


def make_run():
    sm = MagicMock()
    return RunBehavior(far_x_px=250.0, run_speed_px=6.0, sm=sm,
                       min_run_s=10.0, max_run_s=20.0), sm


def test_run_enters_when_beyond_far_threshold():
    b, _ = make_run()
    assert b.should_enter(ctx(horizontal_distance=300))


def test_run_does_not_enter_when_within_far_threshold():
    b, _ = make_run()
    assert not b.should_enter(ctx(horizontal_distance=200))


def test_run_on_enter_sets_threshold_via_sm(monkeypatch):
    b, sm = make_run()
    import random
    monkeypatch.setattr(random, "uniform", lambda a, b_: 12.0)
    b.on_enter(ctx())
    sm.set_run_threshold.assert_called_once_with(12.0)


def test_run_on_exit_resets_running_time():
    b, sm = make_run()
    b.on_exit(ctx())
    sm.reset_running_time.assert_called_once()


def test_run_update_adds_running_time():
    b, sm = make_run()
    b.on_enter(ctx())
    b.update(ctx(move_direction="east"))
    sm.add_running_time.assert_called()


def test_run_moves_at_run_speed_east():
    b, _ = make_run()
    req, delta = b.update(ctx(move_direction="east"))
    assert req.animation == "Run"
    assert delta == pytest.approx(6.0)
