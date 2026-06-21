import sys
import time
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from barkoder.animation import AnimationPlayer, AssetLoader
from barkoder.config import load_settings
from barkoder.window import DogWindow


ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
CONFIG_PATH = Path(__file__).parent.parent.parent / "config.toml"


def _detect_taskbar_height(screen) -> int:
    geo = screen.geometry()
    avail = screen.availableGeometry()
    return max(0, geo.height() - avail.height())


def run() -> None:
    settings = load_settings(CONFIG_PATH)
    app = QApplication.instance() or QApplication(sys.argv)

    loader = AssetLoader(ASSETS_DIR)
    player = AnimationPlayer()
    player.set_animation(
        loader.get_frames("Idle", "east"),
        fps=settings.animation_fps.Idle,
        loop=True,
    )

    screen = app.primaryScreen()
    geo = screen.geometry()
    taskbar_h = _detect_taskbar_height(screen)
    dog_y = geo.height() - taskbar_h - 68

    window = DogWindow()
    dog_x = float(geo.width() // 2 - 34)
    window.move_to(dog_x, dog_y)
    window.show()

    last_tick = time.monotonic()

    def tick() -> None:
        nonlocal last_tick, dog_x
        now = time.monotonic()
        delta_s = min(now - last_tick, 0.1)
        last_tick = now

        player.advance(delta_s)
        frame = player.current_frame
        if frame is not None:
            window.set_frame(frame)

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(16)

    sys.exit(app.exec())
