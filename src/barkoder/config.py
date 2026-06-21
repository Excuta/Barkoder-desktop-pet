import dataclasses
import tomllib
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class Thresholds:
    near_x_px: float = 80.0
    far_x_px: float = 250.0
    arrival_x_px: float = 50.0
    bark_active_window_s: float = 2.0
    wander_threshold_s: float = 6.0
    sit_threshold_s: float = 15.0
    sit_hold_seconds: float = 1.5
    cursor_move_threshold_px: float = 5.0
    follow_window_s: float = 5.0
    rest_threshold_s: float = 60.0


@dataclasses.dataclass(frozen=True)
class PantingSettings:
    min_run_seconds: float = 10.0
    max_run_seconds: float = 20.0
    min_cycles: int = 3
    max_cycles: int = 5


@dataclasses.dataclass(frozen=True)
class MovementSettings:
    walk_speed_px: float = 2.5
    run_speed_px: float = 6.0
    wander_run_chance: float = 0.3
    wander_lay_chance: float = 0.5


@dataclasses.dataclass(frozen=True)
class AnimationFps:
    Walk: int = 8
    Run: int = 12
    Bark: int = 8
    Idle: int = 6
    Pant: int = 10
    Sit: int = 1
    Rest: int = 1
    Jump: int = 8


@dataclasses.dataclass(frozen=True)
class DisplaySettings:
    scale: int = 2
    sprite_bottom_pad_px: int = 15


@dataclasses.dataclass(frozen=True)
class Settings:
    thresholds: Thresholds = dataclasses.field(default_factory=Thresholds)
    panting: PantingSettings = dataclasses.field(default_factory=PantingSettings)
    movement: MovementSettings = dataclasses.field(default_factory=MovementSettings)
    animation_fps: AnimationFps = dataclasses.field(default_factory=AnimationFps)
    display: DisplaySettings = dataclasses.field(default_factory=DisplaySettings)


def _parse_settings(data: dict) -> Settings:
    def _from_dict(cls, section: dict):
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in section.items() if k in fields})

    return Settings(
        thresholds=_from_dict(Thresholds, data.get("thresholds", {})),
        panting=_from_dict(PantingSettings, data.get("panting", {})),
        movement=_from_dict(MovementSettings, data.get("movement", {})),
        animation_fps=_from_dict(AnimationFps, data.get("animation_fps", {})),
        display=_from_dict(DisplaySettings, data.get("display", {})),
    )


def load_settings(path: Path) -> Settings:
    with path.open("rb") as f:
        data = tomllib.load(f)
    return _parse_settings(data)
