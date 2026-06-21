import logging

from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext

_log = logging.getLogger("barkoder.bark")


class BarkWalkBehavior(Behavior):
    priority = 2
    name = "bark_walk"
    _WALK_TICKS = 3

    def __init__(
        self,
        near_x_px: float,
        bark_active_window_s: float,
        audio=None,
        walk_speed_px: float = 1.2,
    ) -> None:
        self._near = near_x_px
        self._active_window = bark_active_window_s
        self._audio = audio
        self._walk_speed_px = walk_speed_px
        self._barking = True
        self._walk_ticks_remaining = 0
        self._bark_sound_played = False
        self._cycle_done = False  # True after one full bark+walk; exit so BTCooldown fires

    def should_enter(self, ctx: CursorContext) -> bool:
        # Stay active through the current bark or walk phase
        if self._bark_sound_played or self._walk_ticks_remaining > 0:
            return True
        # One cycle complete — exit so BTCooldown starts its 6s window
        if self._cycle_done:
            return False
        return (
            ctx.horizontal_distance < self._near
            and ctx.cursor_idle_seconds < self._active_window
        )

    def on_enter(self, ctx: CursorContext) -> None:
        self._barking = True
        self._walk_ticks_remaining = 0
        self._bark_sound_played = False
        self._cycle_done = False
        _log.info("bark_walk: entered (dist=%.0fpx)", ctx.horizontal_distance)

    def on_exit(self, ctx: CursorContext) -> None:
        self._barking = True
        self._walk_ticks_remaining = 0
        self._bark_sound_played = False
        self._cycle_done = False

    def notify_animation_finished(self) -> None:
        self._barking = False
        self._walk_ticks_remaining = self._WALK_TICKS
        self._bark_sound_played = False

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        if self._barking:
            if self._audio and not self._bark_sound_played:
                self._audio.play()
                self._bark_sound_played = True
            return AnimationRequest("Bark", ctx.bark_direction_4), 0.0
        else:
            self._walk_ticks_remaining -= 1
            if self._walk_ticks_remaining <= 0:
                self._cycle_done = True  # walk phase done → exit next tick → BTCooldown starts
            return AnimationRequest("Walk", ctx.move_direction), self._walk_speed_px
