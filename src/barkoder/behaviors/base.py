import dataclasses
from abc import ABC, abstractmethod


@dataclasses.dataclass(frozen=True)
class AnimationRequest:
    animation: str
    direction: str


class Behavior(ABC):
    priority: int
    name: str

    @abstractmethod
    def should_enter(self, ctx: "CursorContext") -> bool: ...  # noqa: F821

    @abstractmethod
    def update(self, ctx: "CursorContext") -> tuple[AnimationRequest, float]: ...  # noqa: F821

    def on_enter(self, ctx: "CursorContext") -> None:
        pass

    def on_exit(self, ctx: "CursorContext") -> None:
        pass
