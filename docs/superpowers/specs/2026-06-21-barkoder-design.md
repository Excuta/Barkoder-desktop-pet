# Barkoder — Design Spec
**Date:** 2026-06-21  
**Status:** Approved

---

## Context

Barkoder is a Windows desktop-pet application. A 68×68 pixel dog character lives along the bottom of the screen and reacts to the mouse cursor in real time: chasing it, barking at it, wandering when it's idle, and catching its breath after a long run. The goal is a delightful, low-resource background companion that ships as a single `.exe`, runs on startup, and is designed so new behaviors and animations can be added with minimal code.

---

## Architecture

Six cleanly separated layers, all wired through a 16ms `QTimer` main loop:

```
DogWindow (PyQt6 transparent QWidget)
    │
    ├── AnimationPlayer   — plays frame sequences at configurable FPS
    │       └── AssetLoader — reads metadata.json, caches QPixmap frames
    │
    ├── StateMachine      — holds current Behavior, evaluates transitions each tick
    │       └── [Behavior subclasses] — one class per state, registered in priority order
    │
    ├── CursorTracker     — polls cursor every 16ms, emits CursorContext
    │
    ├── SystemTray        — right-click menu: Quit, Mute/Unmute, Start on Boot
    │
    └── StartupManager    — reads/writes HKCU\Software\Microsoft\Windows\CurrentVersion\Run
```

No global state. `CursorContext` is a plain dataclass threaded through each tick.

---

## CursorContext

Computed fresh every tick by `CursorTracker`:

| Field | Type | Description |
|---|---|---|
| `cursor_pos` | `QPoint` | Absolute screen position |
| `dog_x` | `float` | Dog's current X (left edge of window) |
| `horizontal_distance` | `float` | `abs(cursor.x - dog_x)` |
| `move_direction` | `str` | `"east"` or `"west"` (toward cursor) |
| `bark_direction_4` | `str` | `"north"/"south"/"east"/"west"` — whichever axis delta is larger |
| `cursor_idle_seconds` | `float` | Seconds since cursor last moved |
| `running_seconds` | `float` | Seconds continuously in `RunBehavior` |

**Bark direction logic:** compare `|cursor.x - dog_x|` vs `|cursor.y - dog_y|`. Larger delta picks the axis; sign picks the cardinal.

---

## Behavior System

### Interface

```python
class Behavior(ABC):
    priority: int   # lower = higher priority; evaluated in ascending order
    name: str

    def should_enter(self, ctx: CursorContext) -> bool: ...
    def update(self, ctx: CursorContext) -> AnimationRequest: ...
    def on_enter(self, ctx: CursorContext) -> None: ...   # optional
    def on_exit(self, ctx: CursorContext) -> None: ...    # optional
```

`AnimationRequest` is a dataclass: `(animation: str, direction: str)`.

Adding a new behavior: create a subclass, set `priority`, implement `should_enter` + `update`, register in `StateMachine`.

### Registered Behaviors (priority order)

| Priority | Class | Trigger |
|---|---|---|
| 1 | `PantBehavior` | `running_seconds ≥ run_threshold` (rolled 10–20s on each Run entry) |
| 2 | `BarkWalkBehavior` | `horizontal_distance < near_x_px` AND `cursor_idle_seconds < bark_active_window_s` (default 2.0s — cursor moved within the last 2 seconds) |
| 3 | `ArrivalSitBehavior` | just transitioned to `horizontal_distance < arrival_x_px` (one-shot) |
| 4 | `RunBehavior` | `horizontal_distance > far_x_px` |
| 5 | `WalkBehavior` | `horizontal_distance > near_x_px` |
| 6 | `WanderBehavior` | `cursor_idle_seconds > wander_threshold_s` |
| 7 | `IdleSitBehavior` | `cursor_idle_seconds > sit_threshold_s` |
| 8 | `IdleBehavior` | default fallback |

### Panting Detail

- Run duration threshold rolled randomly: `random.uniform(10, 20)` seconds, chosen fresh each time the dog enters `RunBehavior`.
- Pant cycles rolled on entry: `random.randint(3, 5)`. One-shot animation; `AnimationPlayer` emits `animation_finished` after each cycle. State machine exits `PantBehavior` after the rolled cycle count.

### Arrival Detection

No raw pixel distance. The dog "arrives" when `abs(cursor.x - dog_x) < arrival_x_px` — i.e., the dog is horizontally aligned with the cursor column. Since the dog is constrained to horizontal movement, this is the correct definition of arrival.

`ArrivalSitBehavior` is one-shot: it plays the sit still once, then exits. After it completes, normal priority evaluation resumes — typically falling into `BarkWalkBehavior` if the cursor is still nearby.

### Sitting as a Still Frame

The `sitting` asset has no animation frames — only 4 directional rotation stills. The `AssetLoader` treats each rotation still as a 1-frame list. `AnimationPlayer` with `fps=1` and `loop=True` effectively holds the image static. Direction is chosen from `bark_direction_4` so the dog faces the cursor.

---

## Animation System

### AssetLoader

- Reads `assets/metadata.json` once at startup.
- Builds `Dict[str, Dict[str, List[QPixmap]]]` keyed by `(animation_name, direction)`.
- Aliases the long panting folder name to `"Pant"` internally.
- Character-agnostic: swap the metadata path to load a different character.

### AnimationPlayer

- Holds `frames: List[QPixmap]`, `frame_index: int`, `fps: float`, `loop: bool`.
- Called each tick; advances frame only when elapsed time ≥ `1/fps`.
- One-shot animations emit `animation_finished` signal.
- Loops all others.

### FPS per animation (config.toml)

```toml
[animation_fps]
Walk = 8
Run  = 12
Bark = 8
Idle = 6
Pant = 10
Sit  = 1
```

---

## Window Layer

**`DogWindow(QWidget)`**
- `Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint`
- `WA_TranslucentBackground = True`
- Size: 68×68. Y: `screen_height - taskbar_height - 68` (detected via `QScreen`; clamped).
- Movement: `self.move(new_x, fixed_y)` — no GPU overhead.
- Invisible to Alt-Tab and taskbar (ToolWindow type).

**Main tick (16ms QTimer):**
1. `CursorTracker` computes `CursorContext`
2. `StateMachine.tick(ctx)` → `(AnimationRequest, delta_x)`
3. Window moves by `delta_x`
4. `AnimationPlayer` advances frame
5. `repaint()` — `paintEvent` draws current `QPixmap`

---

## Configuration

`config.toml` at project root — user-tunable without touching code:

```toml
[thresholds]
near_x_px            = 80
bark_active_window_s = 2.0   # seconds after last cursor move that BarkWalk remains eligible
far_x_px        = 250
arrival_x_px    = 50
wander_threshold_s = 6.0
sit_threshold_s    = 15.0

[panting]
min_run_seconds = 10.0
max_run_seconds = 20.0
min_cycles = 3
max_cycles = 5

[animation_fps]
Walk = 8
Run  = 12
Bark = 8
Idle = 6
Pant = 10
Sit  = 1
```

---

## System Tray

Right-click context menu:
- **Mute / Unmute** — toggles bark sound
- **Start on Boot** — toggles registry key via `StartupManager`
- **Quit**

---

## Audio

`AudioController` wraps `QSoundEffect`. A bundled `bark.wav` plays when `BarkWalkBehavior` triggers the Bark animation. `muted` flag exposed via system tray toggle. No audio in v1; added in milestone 7.

---

## Distribution

- **v1:** PyInstaller single-file `.exe` (hidden console, icon embedded).
- **v2:** NSIS or Inno Setup installer — handles startup registry write, Start Menu shortcut, uninstall.
- `pyproject.toml` manages deps (`PyQt6`, `tomllib`/`tomli`).

---

## Project Structure

```
barkoder/
├── assets/
│   └── metadata.json
├── src/
│   └── barkoder/
│       ├── __main__.py
│       ├── app.py
│       ├── window.py
│       ├── animation.py
│       ├── tracker.py
│       ├── state_machine.py
│       ├── behaviors/
│       │   ├── __init__.py
│       │   ├── base.py          # Behavior ABC + AnimationRequest
│       │   ├── run.py
│       │   ├── walk.py
│       │   ├── bark_walk.py
│       │   ├── pant.py
│       │   ├── wander.py
│       │   ├── idle.py
│       │   ├── arrival_sit.py
│       │   └── idle_sit.py
│       ├── audio.py
│       ├── startup.py
│       └── config.py
├── config.toml
├── docs/superpowers/specs/
├── pyproject.toml
└── barkoder.spec                # PyInstaller spec
```

---

## Milestones (step-by-step, never fix everything at once)

| Step | Goal |
|---|---|
| 1 | Transparent window on screen, dog visible, Idle animation playing |
| 2 | CursorTracker + Walk/Run behaviors — dog chases cursor left/right |
| 3 | Pant behavior (randomized duration + cycles) |
| 4 | Bark behavior with 4-directional awareness |
| 5 | Wander + Sit behaviors (idle detection, arrival sit) |
| 6 | System tray (Quit, Mute, Start on Boot) |
| 7 | Audio (optional bark sound, mute toggle) |
| 8 | PyInstaller build + NSIS installer |
| 9 | BT upgrade — swap `StateMachine.evaluate` for a Behavior Tree traversal |

---

## BT Upgrade Path

`StateMachine.evaluate(ctx)` iterates behaviors in priority order and calls `should_enter`. To upgrade to a Behavior Tree, replace this evaluation loop with a BT traversal — the `Behavior` interface is unchanged. All behavior classes survive the upgrade unmodified.

---

## Verification

Each milestone verified by:
1. Running `python -m barkoder` and visually confirming the new behavior.
2. Moving cursor to trigger each state transition.
3. Leaving cursor idle to confirm wander → sit progression.
4. Checking `config.toml` changes take effect on next launch.
