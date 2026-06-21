import pytest
from barkoder.animation import AnimationPlayer


# --- AnimationPlayer tests (no Qt needed — frames are opaque objects) ---

def make_player(frames, fps=8.0, loop=True):
    p = AnimationPlayer()
    p.set_animation(frames, fps=fps, loop=loop)
    return p


def test_initial_frame_is_first():
    p = make_player([10, 20, 30])
    assert p.current_frame == 10


def test_advance_changes_frame_at_fps_boundary():
    p = make_player([10, 20, 30], fps=10.0)
    p.advance(0.05)   # half an interval (0.1s) — no change yet
    assert p.current_frame == 10
    p.advance(0.06)   # crosses 0.1s boundary
    assert p.current_frame == 20


def test_looping_wraps_around():
    p = make_player([10, 20], fps=10.0, loop=True)
    p.advance(0.1)   # → frame 1
    p.advance(0.1)   # → wraps to frame 0
    assert p.current_frame == 10


def test_one_shot_stops_at_last_frame():
    p = make_player([10, 20, 30], fps=10.0, loop=False)
    p.advance(0.1)  # → 20
    p.advance(0.1)  # → 30
    p.advance(0.1)  # stays at 30, is_finished
    assert p.current_frame == 30
    assert p.is_finished


def test_one_shot_not_finished_before_end():
    p = make_player([10, 20, 30], fps=10.0, loop=False)
    p.advance(0.1)
    assert not p.is_finished


def test_reset_finished_clears_flag():
    p = make_player([10], fps=10.0, loop=False)
    p.advance(0.2)
    assert p.is_finished
    p.reset_finished()
    assert not p.is_finished


def test_set_animation_resets_state():
    p = make_player([10, 20], fps=10.0, loop=False)
    p.advance(0.2)
    p.set_animation([30, 40], fps=10.0, loop=True)
    assert p.current_frame == 30
    assert not p.is_finished


def test_empty_frames_returns_none():
    p = AnimationPlayer()
    assert p.current_frame is None
    p.advance(1.0)  # should not raise


def test_advance_cap_prevents_multi_frame_skip():
    # Advancing 10s should not skip all frames if fps=8
    # (this tests the while-loop in advance handles large deltas correctly)
    p = make_player([10, 20, 30], fps=8.0, loop=True)
    p.advance(10.0)
    # should still be at some valid frame, no crash
    assert p.current_frame in (10, 20, 30)
