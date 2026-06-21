from pathlib import Path
import pytest
from barkoder.config import load_settings, Settings

CONFIG_PATH = Path(__file__).parent.parent / "config.toml"

def test_loads_real_config():
    s = load_settings(CONFIG_PATH)
    assert isinstance(s, Settings)

def test_near_x_px_default():
    s = load_settings(CONFIG_PATH)
    assert s.thresholds.near_x_px == 80.0

def test_walk_speed():
    s = load_settings(CONFIG_PATH)
    assert s.movement.walk_speed_px == 2.0

def test_panting_min_cycles():
    s = load_settings(CONFIG_PATH)
    assert s.panting.min_cycles == 3

def test_animation_fps_run():
    s = load_settings(CONFIG_PATH)
    assert s.animation_fps.Run == 12

def test_missing_key_uses_default():
    import tomllib, io
    raw = b"[thresholds]\nnear_x_px = 99.0\n"
    # AnimationFps fields not in raw — should fall back to defaults
    from barkoder.config import _parse_settings
    data = tomllib.loads(raw.decode())
    s = _parse_settings(data)
    assert s.animation_fps.Walk == 8   # default
    assert s.thresholds.near_x_px == 99.0
