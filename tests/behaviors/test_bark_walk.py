import pytest
from unittest.mock import MagicMock
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


def test_barkwalk_audio_plays_at_start_of_bark():
    """Audio should play once when barking starts."""
    mock_audio = MagicMock()
    b = BarkWalkBehavior(near_x_px=80.0, bark_active_window_s=2.0, audio=mock_audio)
    b.on_enter(ctx())

    # First update while barking - should play audio
    b.update(ctx())
    mock_audio.play.assert_called_once()

    # Second update while still barking - should not play again
    b.update(ctx())
    mock_audio.play.assert_called_once()


def test_barkwalk_exits_after_one_cycle():
    """After one bark+walk cycle, should_enter returns False so BTCooldown fires."""
    mock_audio = MagicMock()
    b = BarkWalkBehavior(near_x_px=80.0, bark_active_window_s=2.0, audio=mock_audio)
    c = ctx()
    b.on_enter(c)

    b.update(c)                          # first bark tick — audio plays
    assert mock_audio.play.call_count == 1

    b.notify_animation_finished()        # bark animation done → walk phase

    for _ in range(3):
        b.update(ctx(move_direction="east"))  # exhaust walk ticks → _cycle_done = True

    # Cycle complete: should_enter must return False even if cursor is still near
    assert not b.should_enter(c), "should exit after one cycle so BTCooldown can start"
    assert mock_audio.play.call_count == 1, "no extra bark during cooldown handoff"

def test_barkwalk_audio_plays_again_on_reentry():
    """After on_enter is called again (post-cooldown), audio plays for the new bark."""
    mock_audio = MagicMock()
    b = BarkWalkBehavior(near_x_px=80.0, bark_active_window_s=2.0, audio=mock_audio)
    c = ctx()

    # First session
    b.on_enter(c)
    b.update(c)
    b.notify_animation_finished()
    for _ in range(3):
        b.update(ctx(move_direction="east"))
    b.on_exit(c)   # BTCooldown triggers on_exit, then waits 6s

    # Second session (cooldown expired, BT re-enters)
    b.on_enter(c)
    b.update(c)
    assert mock_audio.play.call_count == 2


def test_barkwalk_without_audio():
    """BarkWalkBehavior should work fine without audio (audio=None)."""
    b = BarkWalkBehavior(near_x_px=80.0, bark_active_window_s=2.0, audio=None)
    b.on_enter(ctx())
    req, _ = b.update(ctx())
    assert req.animation == "Bark"
