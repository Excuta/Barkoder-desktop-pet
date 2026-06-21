from barkoder.behaviors.base import Behavior, AnimationRequest
from barkoder.tracker import CursorContext


class IdleBehavior(Behavior):
    priority = 8
    name = "idle"

    def should_enter(self, ctx: CursorContext) -> bool:
        return True

    def update(self, ctx: CursorContext) -> tuple[AnimationRequest, float]:
        return AnimationRequest("Idle", ctx.move_direction), 0.0
