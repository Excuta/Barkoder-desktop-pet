import dataclasses
from abc import ABC, abstractmethod


@dataclasses.dataclass(frozen=True)
class AnimationRequest:
    animation: str
    direction: str
    y_offset: float = 0.0


class Behavior(ABC):
    priority: int
    name: str
    min_dwell_s: float = 0.0       # minimum time before a lower-priority behavior can preempt
    max_dwell_s: float = 0.0       # random budget upper bound; 0 means use min_dwell_s exactly
    exit_cooldown_s: float = 0.0   # seconds before this behavior can re-enter after exiting

    @abstractmethod
    def should_enter(self, ctx: "CursorContext") -> bool: ...  # noqa: F821

    @abstractmethod
    def update(self, ctx: "CursorContext") -> tuple[AnimationRequest, float]: ...  # noqa: F821

    def on_enter(self, ctx: "CursorContext") -> None:
        pass

    def on_exit(self, ctx: "CursorContext") -> None:
        pass
