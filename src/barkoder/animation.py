import json
from pathlib import Path
from typing import Any

_PANT_FOLDER = "Dog_should_look_tired_catching_its_breath_with_a_p"


class AnimationPlayer:
    def __init__(self) -> None:
        self._frames: list[Any] = []
        self._index: int = 0
        self._fps: float = 8.0
        self._loop: bool = True
        self._elapsed: float = 0.0
        self._finished: bool = False

    def set_animation(self, frames: list[Any], fps: float, loop: bool = True) -> None:
        self._frames = list(frames)
        self._index = 0
        self._fps = fps
        self._loop = loop
        self._elapsed = 0.0
        self._finished = False

    def advance(self, delta_s: float) -> None:
        if not self._frames or self._finished:
            return
        self._elapsed += delta_s
        interval = 1.0 / self._fps
        while self._elapsed >= interval:
            self._elapsed -= interval
            self._index += 1
            if self._index >= len(self._frames):
                if self._loop:
                    self._index = 0
                else:
                    self._index = len(self._frames) - 1
                    self._finished = True
                    break

    @property
    def current_frame(self) -> Any:
        if not self._frames:
            return None
        return self._frames[self._index]

    @property
    def is_finished(self) -> bool:
        return self._finished

    def reset_finished(self) -> None:
        self._finished = False


class AssetLoader:
    def __init__(self, assets_dir: Path) -> None:
        from PyQt6.QtGui import QPixmap  # imported here so tests can mock Qt

        self._frames: dict[str, dict[str, list[QPixmap]]] = {}
        self._load(assets_dir, QPixmap)

    def _load(self, assets_dir: Path, QPixmap_cls: type) -> None:
        meta_path = assets_dir / "metadata.json"
        with meta_path.open() as f:
            meta = json.load(f)

        for state in meta["states"]:
            folder = state["folder"]
            animations = state["frames"].get("animations", {})
            for raw_name, directions in animations.items():
                key = "Pant" if raw_name == _PANT_FOLDER else raw_name
                self._frames.setdefault(key, {})
                for direction, frame_paths in directions.items():
                    # Normalize "west-a1019c9d" → "west" (strip AI generation hash suffixes)
                    norm_dir = direction.split("-")[0]
                    if norm_dir not in self._frames[key]:  # first occurrence wins
                        self._frames[key][norm_dir] = [
                            QPixmap_cls(str(assets_dir / p)) for p in frame_paths
                        ]

            # Load rotation stills as single-frame "Sit" animation
            if folder == "sitting":
                rotations = state["frames"].get("rotations", {})
                self._frames.setdefault("Sit", {})
                for direction, rel_path in rotations.items():
                    self._frames["Sit"][direction] = [
                        QPixmap_cls(str(assets_dir / rel_path))
                    ]

            # Load laying_down rotation stills as single-frame "Rest" animation
            if folder == "laying_down":
                rotations = state["frames"].get("rotations", {})
                self._frames.setdefault("Rest", {})
                for direction, rel_path in rotations.items():
                    self._frames["Rest"][direction] = [
                        QPixmap_cls(str(assets_dir / rel_path))
                    ]

    def register_synthetic(self, animation: str, direction: str, frames: list) -> None:
        """Register a manually assembled frame sequence under a new animation name."""
        self._frames.setdefault(animation, {})[direction] = list(frames)

    def get_frames(self, animation: str, direction: str) -> list:
        key = (animation, direction)
        flat = {(anim, direc) for anim, dirs in self._frames.items() for direc in dirs}
        if key not in flat:
            available = sorted(flat)
            raise KeyError(
                f"No frames found for animation={animation!r}, direction={direction!r}. "
                f"Available: {available}"
            )
        return self._frames[animation][direction]

    def has_animation(self, animation: str, direction: str) -> bool:
        return animation in self._frames and direction in self._frames.get(animation, {})
