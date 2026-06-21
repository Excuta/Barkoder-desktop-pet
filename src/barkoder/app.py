import sys
import time
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from barkoder.animation import AnimationPlayer, AssetLoader
from barkoder.behaviors.idle import IdleBehavior
from barkoder.behaviors.walk import WalkBehavior
from barkoder.behaviors.run import RunBehavior
from barkoder.config import load_settings
from barkoder.state_machine import StateMachine
from barkoder.tracker import CursorTracker
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

    screen = app.primaryScreen()
    geo = screen.geometry()
    taskbar_h = _detect_taskbar_height(screen)
    dog_y = float(geo.height() - taskbar_h - 68)

    loader = AssetLoader(ASSETS_DIR)
    player = AnimationPlayer()
    window = DogWindow()
    dog_x = float(geo.width() // 2 - 34)
    window.move_to(dog_x, dog_y)
    window.show()

    th = settings.thresholds
    mv = settings.movement
    pa = settings.panting

    run_b = RunBehavior(
        far_x_px=th.far_x_px, run_speed_px=mv.run_speed_px, sm=None,
        min_run_s=pa.min_run_seconds, max_run_s=pa.max_run_seconds,
    )
    walk_b = WalkBehavior(near_x_px=th.near_x_px, walk_speed_px=mv.walk_speed_px)
    idle_b = IdleBehavior()
    sm = StateMachine([idle_b, walk_b, run_b])
    run_b._sm = sm  # inject after construction

    tracker = CursorTracker(move_threshold_px=th.cursor_move_threshold_px)
    last_tick = time.monotonic()
    fps = settings.animation_fps
    current_anim: tuple[str, str] = ("", "")

    def tick() -> None:
        nonlocal last_tick, dog_x, current_anim
        now = time.monotonic()
        delta_s = min(now - last_tick, 0.1)
        last_tick = now

        ctx = tracker.compute(dog_x, dog_y, delta_s,
                              sm.running_seconds, sm._run_threshold)
        req, delta_x = sm.tick(ctx)

        dog_x = max(0.0, min(geo.width() - 68.0, dog_x + delta_x))
        window.move_to(dog_x, dog_y)

        anim_key = (req.animation, req.direction)
        if anim_key != current_anim:
            current_anim = anim_key
            anim_fps = getattr(fps, req.animation, fps.Idle)
            is_loop = req.animation not in ("Pant",)
            player.set_animation(
                loader.get_frames(req.animation, req.direction),
                fps=float(anim_fps),
                loop=is_loop,
            )

        player.advance(delta_s)
        frame = player.current_frame
        if frame is not None:
            window.set_frame(frame)

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(16)
    sys.exit(app.exec())
