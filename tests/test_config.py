from pathlib import Path
import pytest
from barkoder.config import load_settings, Settings

CONFIG_PATH = Path(__file__).parent.parent / "config.toml"

def test_loads_real_config():
    s = load_settings(CONFIG_PATH)
    assert isinstance(s, Settings)

def test_near_x_px_default():
    s = load_settings(CONFIG_PATH)
    assert s.thresholds.near_x_px == 100.0

def test_walk_speed():
    s = load_settings(CONFIG_PATH)
    assert s.movement.walk_speed_px == 1.2

def test_panting_min_cycles():
    s = load_settings(CONFIG_PATH)
    assert s.panting.min_cycles == 2

def test_animation_fps_run():
    s = load_settings(CONFIG_PATH)
    assert s.animation_fps.Run == 8

def test_missing_key_uses_default():
    import tomllib, io
    raw = b"[thresholds]\nnear_x_px = 99.0\n"
    # AnimationFps fields not in raw — should fall back to defaults
    from barkoder.config import _parse_settings
    data = tomllib.loads(raw.decode())
    s = _parse_settings(data)
    assert s.animation_fps.Walk == 8   # default
    assert s.thresholds.near_x_px == 99.0

def test_display_defaults():
    s = load_settings(CONFIG_PATH)
    assert s.display.scale == 2
    assert s.display.sprite_bottom_pad_px == 15

def test_display_missing_uses_defaults():
    import tomllib
    raw = b"[thresholds]\nnear_x_px = 99.0\n"
    from barkoder.config import _parse_settings
    data = tomllib.loads(raw.decode())
    s = _parse_settings(data)
    assert s.display.scale == 2
    assert s.display.sprite_bottom_pad_px == 15
