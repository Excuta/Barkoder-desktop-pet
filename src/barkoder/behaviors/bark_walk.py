import logging

from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext

_log = logging.getLogger("barkoder.bark")

_WALK_STEPS = 3  # update ticks to walk before barking again


class BarkWalkBehavior(Behavior):
    priority = 2
    name = "bark_walk"
    min_dwell_s = 3.0
    max_dwell_s = 6.0
    exit_cooldown_s = 6.0

    def __init__(self, near_x_px: float, bark_active_window_s: float, audio=None) -> None:
        self._near = near_x_px
        self._active_window = bark_active_window_s
        self._barking = True   # True = show bark, False = show walk step
        self._walk_ticks = 0
        self._audio = audio
        self._bark_sound_played = False

    def should_enter(self, ctx: CursorContext) -> bool:
        return (
            ctx.horizontal_distance < self._near
            and ctx.cursor_idle_seconds < self._active_window
        )

    def on_enter(self, ctx: CursorContext) -> None:
        self._barking = True
        self._walk_ticks = 0
        self._bark_sound_played = False
        _log.info("bark_walk: entered (dist=%.0fpx)", ctx.horizontal_distance)

    def notify_animation_finished(self) -> None:
        self._barking = False
        self._walk_ticks = _WALK_STEPS
        self._bark_sound_played = False

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        if self._barking:
            if self._audio and not self._bark_sound_played:
                self._audio.play()
                self._bark_sound_played = True
            return AnimationRequest("Bark", ctx.bark_direction_4), 0.0
        if self._walk_ticks > 0:
            self._walk_ticks -= 1
            delta = 2.5 if ctx.move_direction == "east" else -2.5
            if self._walk_ticks == 0:
                self._barking = True
                self._bark_sound_played = False
            return AnimationRequest("Walk", ctx.move_direction), delta
        self._barking = True
        self._bark_sound_played = False
        return AnimationRequest("Bark", ctx.bark_direction_4), 0.0
