import logging
import sys
import time
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from barkoder.animation import AnimationPlayer, AssetLoader
from barkoder.audio import AudioController
from barkoder.behaviors.idle import IdleBehavior
from barkoder.behaviors.walk import WalkBehavior
from barkoder.behaviors.run import RunBehavior
from barkoder.behaviors.pant import PantBehavior
from barkoder.behaviors.bark_walk import BarkWalkBehavior
from barkoder.behaviors.wander import WanderBehavior
from barkoder.behaviors.arrival_sit import ArrivalSitBehavior
from barkoder.behaviors.idle_sit import IdleSitBehavior
from barkoder.config import load_settings
from barkoder.logging_setup import setup_logging
from barkoder.startup import StartupManager
from barkoder.state_machine import StateMachine
from barkoder.tracker import CursorTracker
from barkoder.window import DogWindow


def _resource_dir() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent.parent

ASSETS_DIR = _resource_dir() / "assets"
CONFIG_PATH = _resource_dir() / "config.toml"


def _detect_taskbar_height(screen) -> int:
    geo = screen.geometry()
    avail = screen.availableGeometry()
    return max(0, geo.height() - avail.height())


def run() -> None:
    setup_logging(debug="--debug" in sys.argv)
    log = logging.getLogger("barkoder.app")

    settings = load_settings(CONFIG_PATH)
    app = QApplication.instance() or QApplication(sys.argv)

    screen = app.primaryScreen()
    geo = screen.geometry()
    avail = screen.availableGeometry()

    disp = settings.display
    DOG_SIZE = 68 * disp.scale
    pad_scaled = disp.sprite_bottom_pad_px * disp.scale
    dog_y = float(avail.y() + avail.height() - DOG_SIZE + pad_scaled)

    log.info("config=%s", CONFIG_PATH)
    log.info("screen=%dx%d avail_y=%d DOG_SIZE=%d dog_y=%d pad_px=%d",
             geo.width(), geo.height(), avail.y(), DOG_SIZE, dog_y, pad_scaled)

    loader = AssetLoader(ASSETS_DIR)
    player = AnimationPlayer()
    window = DogWindow()
    dog_x = float(geo.width() // 2 - DOG_SIZE // 2)
    window.move_to(dog_x, dog_y)
    window.show()

    # Audio controller
    audio = AudioController(ASSETS_DIR / "bark.wav")

    # System tray — add pixmap at every size Windows may request
    png_path = ASSETS_DIR / "sitting" / "rotations" / "south.png"
    tray_icon = QIcon()
    if png_path.exists():
        src = QPixmap(str(png_path))
        for sz in [16, 20, 24, 32, 40, 48, 64, 128, 256]:
            tray_icon.addPixmap(
                src.scaled(sz, sz, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
            )
    startup_mgr = StartupManager("Barkoder")

    tray = QSystemTrayIcon(tray_icon, parent=app)
    menu = QMenu()

    mute_action = menu.addAction("Mute")
    mute_action.setCheckable(True)
    mute_action.setChecked(False)

    def toggle_mute(checked: bool) -> None:
        audio.toggle_mute()

    mute_action.toggled.connect(toggle_mute)

    boot_action = menu.addAction("Start on Boot")
    boot_action.setCheckable(True)
    boot_action.setChecked(startup_mgr.is_enabled())

    def toggle_boot(checked: bool) -> None:
        if checked:
            startup_mgr.enable(str(Path(sys.executable).resolve()))
        else:
            startup_mgr.disable()

    boot_action.toggled.connect(toggle_boot)
    menu.addSeparator()
    quit_action = menu.addAction("Quit")
    quit_action.triggered.connect(app.quit)
    tray.setContextMenu(menu)
    tray.show()

    th = settings.thresholds
    mv = settings.movement
    pa = settings.panting

    log.info("cfg near_x=%.0f far_x=%.0f walk=%.1f run=%.1f wander_s=%.0f sit_s=%.0f",
             th.near_x_px, th.far_x_px, mv.walk_speed_px, mv.run_speed_px,
             th.wander_threshold_s, th.sit_threshold_s)

    run_b = RunBehavior(
        far_x_px=th.far_x_px, run_speed_px=mv.run_speed_px, sm=None,
        min_run_s=pa.min_run_seconds, max_run_s=pa.max_run_seconds,
    )
    walk_b = WalkBehavior(near_x_px=th.near_x_px, walk_speed_px=mv.walk_speed_px)
    idle_b = IdleBehavior()
    pant_b = PantBehavior(sm=None, min_cycles=pa.min_cycles, max_cycles=pa.max_cycles)
    bark_walk_b = BarkWalkBehavior(near_x_px=th.near_x_px, bark_active_window_s=th.bark_active_window_s, audio=audio)
    wander_b = WanderBehavior(
        wander_threshold_s=th.wander_threshold_s,
        walk_speed_px=mv.walk_speed_px,
        screen_width=geo.width(),
    )
    arrival_sit_b = ArrivalSitBehavior(
        arrival_x_px=th.arrival_x_px,
        sit_hold_seconds=th.sit_hold_seconds,
    )
    idle_sit_b = IdleSitBehavior(sit_threshold_s=th.sit_threshold_s)
    sm = StateMachine([idle_b, bark_walk_b, walk_b, pant_b, run_b, wander_b, arrival_sit_b, idle_sit_b])
    run_b._sm = sm  # inject after construction
    pant_b._sm = sm  # inject after construction

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
        req, delta_x = sm.tick(ctx, delta_s)

        if req.animation == "Run":
            sm.add_running_time(delta_s)

        dog_x = max(0.0, min(float(geo.width() - DOG_SIZE), dog_x + delta_x))
        window.move_to(dog_x, dog_y)

        anim_key = (req.animation, req.direction)
        if anim_key != current_anim:
            current_anim = anim_key
            anim_fps = getattr(fps, req.animation, fps.Idle)
            is_loop = req.animation not in ("Pant", "Bark")
            player.set_animation(
                loader.get_frames(req.animation, req.direction),
                fps=float(anim_fps),
                loop=is_loop,
            )

        player.advance(delta_s)

        # Handle pant animation cycle completion
        if req.animation == "Pant" and player.is_finished:
            player.reset_finished()
            pant_b.notify_animation_finished()
            if pant_b._exhausted:
                # Force re-evaluation next tick by clearing the one-shot state
                current_anim = ("", "")

        # Handle bark animation cycle completion
        if req.animation == "Bark" and player.is_finished:
            player.reset_finished()
            bark_walk_b.notify_animation_finished()
            current_anim = ("", "")  # force re-evaluation

        # Handle arrival-sit hold completion
        if req.animation == "Sit" and sm.current_behavior is arrival_sit_b:
            if arrival_sit_b.hold_done:
                arrival_sit_b._triggered = True
                wander_b.force_start()
                current_anim = ("", "")

        frame = player.current_frame
        if frame is not None:
            window.set_frame(frame)

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(16)
    sys.exit(app.exec())
