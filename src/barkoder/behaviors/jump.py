import random
import logging
from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext

_log = logging.getLogger("barkoder.jump")

_JUMP_CHANCE = 0.65
_JUMP_HEIGHT_PX = 60.0
_JUMP_HALF_TIME_S = 0.5  # seconds to reach peak

_PRE_SIT = "pre_sit"
_JUMPING = "jumping"
_POST_SIT = "post_sit"


class JumpBehavior(Behavior):
    name = "jump"

    def __init__(self, screen_height: int, near_x_px: float = 100.0) -> None:
        self._screen_height = screen_height
        self._near = near_x_px
        self._active = False
        self._jumped_this_arrival = False
        self._phase = _PRE_SIT
        self._phase_timer = 0.0
        self._vy = 0.0
        self._y_offset = 0.0
        self._gravity = 2 * _JUMP_HEIGHT_PX / (_JUMP_HALF_TIME_S ** 2)
        self._direction = "east"

    def should_enter(self, ctx: CursorContext) -> bool:
        if self._active:
            return True
        # Reset per-arrival guard once dog has moved away from cursor
        if ctx.horizontal_distance > self._near * 3:
            self._jumped_this_arrival = False
        if self._jumped_this_arrival:
            return False
        near = ctx.horizontal_distance < self._near
        cursor_high = ctx.cursor_y < self._screen_height * 0.6
        cursor_active = ctx.cursor_idle_seconds < 5.0
        if not (near and cursor_high and cursor_active):
            return False
        # One roll per arrival — mark attempted regardless of outcome
        self._jumped_this_arrival = True
        return random.random() < _JUMP_CHANCE

    def on_enter(self, ctx: CursorContext) -> None:
        self._active = True
        self._direction = ctx.move_direction
        self._phase = _PRE_SIT
        self._phase_timer = random.uniform(0.5, 1.0)
        self._y_offset = 0.0
        _log.debug("jump: triggered, pre-sit %.2fs", self._phase_timer)

    def on_exit(self, ctx: CursorContext) -> None:
        self._active = False
        self._y_offset = 0.0

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        dt = 0.016

        if self._phase == _PRE_SIT:
            self._phase_timer -= dt
            if self._phase_timer <= 0:
                self._phase = _JUMPING
                self._vy = -self._gravity * _JUMP_HALF_TIME_S
                self._y_offset = 0.0
                _log.debug("jump: launching")
            return AnimationRequest("Sit", "north"), 0.0

        if self._phase == _JUMPING:
            self._vy += self._gravity * dt
            self._y_offset += self._vy * dt
            if self._y_offset >= 0.0:
                self._y_offset = 0.0
                self._phase = _POST_SIT
                self._phase_timer = random.uniform(0.5, 1.0)
                _log.debug("jump: landed, post-sit %.2fs", self._phase_timer)
            return AnimationRequest("Run", "north", self._y_offset), 0.0

        # _POST_SIT
        self._phase_timer -= dt
        if self._phase_timer <= 0:
            self._active = False
        return AnimationRequest("Sit", "north"), 0.0
