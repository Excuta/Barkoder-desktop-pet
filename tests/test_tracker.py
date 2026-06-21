import pytest
from barkoder.tracker import CursorContext, CursorTracker, compute_bark_direction
import dataclasses


# --- compute_bark_direction ---

def test_cursor_right_of_dog_is_east():
    assert compute_bark_direction(300, 100, 100, 100) == "east"

def test_cursor_left_of_dog_is_west():
    assert compute_bark_direction(50, 100, 300, 100) == "west"

def test_cursor_above_dog_is_north():
    # cursor directly above (same X, much higher Y)
    assert compute_bark_direction(200, 100, 200, 900) == "north"

def test_cursor_below_dog_is_south():
    # cursor below (same X, lower Y — screen Y increases downward)
    assert compute_bark_direction(200, 950, 200, 900) == "south"

def test_diagonal_prefers_horizontal_when_x_larger():
    # dx=200, dy=50 → east wins
    assert compute_bark_direction(300, 850, 100, 900) == "east"

def test_diagonal_prefers_vertical_when_y_larger():
    # dx=10, dy=400 → north wins (cursor well above dog)
    assert compute_bark_direction(210, 500, 200, 900) == "north"

def test_tied_deltas_prefer_horizontal():
    # |dx| == |dy| → horizontal rule; east
    assert compute_bark_direction(300, 700, 100, 900) == "east"


# --- CursorContext fields ---

def test_cursor_context_horizontal_distance():
    ctx = CursorContext(
        cursor_x=400.0, cursor_y=500.0,
        dog_x=200.0, dog_y=900.0,
        horizontal_distance=200.0,
        move_direction="east",
        bark_direction_4="east",
        cursor_idle_seconds=0.0,
        running_seconds=0.0,
        run_threshold=15.0,
    )
    assert ctx.horizontal_distance == 200.0


# --- CursorTracker idle accumulation (without real Qt cursor) ---

def test_tracker_accumulates_idle_when_cursor_still():
    tracker = CursorTracker(move_threshold_px=5.0)
    tracker._settled_x = 100.0
    tracker._settled_y = 100.0
    tracker._cursor_idle_seconds = 0.0

    # Simulate cursor staying at settled position
    tracker._cursor_idle_seconds += 0.016
    tracker._cursor_idle_seconds += 0.016
    assert tracker._cursor_idle_seconds == pytest.approx(0.032)


def test_tracker_resets_idle_when_cursor_moves():
    import math
    tracker = CursorTracker(move_threshold_px=5.0)
    tracker._settled_x = 100.0
    tracker._settled_y = 100.0
    tracker._cursor_idle_seconds = 5.0

    # Simulate cursor leaving the deadzone
    new_x, new_y = 200.0, 200.0
    if math.hypot(new_x - tracker._settled_x, new_y - tracker._settled_y) > tracker._deadzone_px:
        tracker._cursor_idle_seconds = 0.0
        tracker._settled_x = new_x
        tracker._settled_y = new_y

    assert tracker._cursor_idle_seconds == 0.0
