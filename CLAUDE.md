# Barkoder – Project Map

## What It Is
A Windows desktop-pet app: a pixel-art dog that lives on the taskbar, follows your cursor, barks at you, and idles around. Built with **PyQt6**, packaged with **PyInstaller**.

## Run & Build

```powershell
# Dev run
uv run python -m barkoder

# Dev run with debug logging
uv run python -m barkoder --debug

# Tests
uv run pytest

# Build exe (kill running instance first)
uv run pyinstaller barkoder.spec
# Confirm success by reading build_output.txt (don't trust exit code alone)
```

## Key Files

| Path | Purpose |
|---|---|
| `src/barkoder/app.py` | Entry point: wires everything together, Qt event loop, system tray |
| `src/barkoder/config.py` | Typed settings dataclasses; loaded from `config.toml` at startup |
| `config.toml` | User-tunable parameters (near/far thresholds, speeds, FPS, etc.) |
| `src/barkoder/behavior_tree.py` | `BehaviorTree` — thin wrapper around a root `BTNode`; call `.tick()` each frame |
| `src/barkoder/bt/nodes.py` | BT primitives: `BTLeaf`, `BTSelector`, `BTCooldown`, `BTRandomDwell` |
| `src/barkoder/behaviors/base.py` | `Behavior` ABC + `AnimationRequest(animation, direction, y_offset)` dataclass |
| `src/barkoder/tracker.py` | `CursorTracker` — wraps `QCursor.pos()`, computes `CursorContext` each tick |
| `src/barkoder/animation.py` | `AssetLoader` (reads `assets/metadata.json`) + `AnimationPlayer` (frame advance) |
| `src/barkoder/audio.py` | `AudioController` — plays random WAV from `assets/audio/` via `QSoundEffect` |
| `src/barkoder/window.py` | `DogWindow` — frameless, always-on-top, transparent `QWidget` |
| `src/barkoder/logging_setup.py` | Writes session log to `~/.barkoder/barkoder_YYYYMMDD_HHMMSS.log` (10 kept) |
| `src/barkoder/startup.py` | Windows registry run-on-boot via `StartupManager` |

## Behavior Tree (priority order, highest first)

```
BTSelector
  1. BTLeaf(PantBehavior)                   — dog catches breath after running
  2. BTCooldown(BTLeaf(BarkWalkBehavior), 6s) — greets cursor when close; bark→walk cycle
  3. BTLeaf(JumpBehavior)                   — 65% chance jump when cursor is high & near
  4. BTLeaf(ArrivalSitBehavior)             — sits when cursor arrives very close
  5. BTLeaf(FollowBehavior)                 — chases cursor (walk / run based on distance)
  6. BTRandomDwell(BTLeaf(WanderBehavior))  — wanders screen when cursor idle
  7. BTRandomDwell(BTLeaf(IdleSitBehavior)) — sits after prolonged idle
  8. BTRandomDwell(BTLeaf(RestBehavior))    — lies down after extended idle
  9. BTLeaf(IdleBehavior)                   — fallback: always active
```

All behaviors implement `should_enter(ctx) → bool`, `update(ctx) → (AnimationRequest, delta_x)`, and optional `on_enter` / `on_exit` / `notify_animation_finished` hooks.

## BT Node Semantics

- **`BTLeaf`**: calls `should_enter` each tick; calls `on_enter`/`on_exit` on transitions.
- **`BTSelector`**: tries children left-to-right; returns first non-None result.
- **`BTCooldown`**: blocks child for `cooldown_s` after it exits.
- **`BTRandomDwell`**: holds child for a random budget `[min_s, max_s]`, then pauses `[min_yield_s, max_yield_s]`.

## Animation System

Assets live in `assets/`. `AssetLoader` reads `assets/metadata.json` at startup, indexes frames as `dict[animation_name][direction] → list[QPixmap]`. `AnimationPlayer.advance(delta_s)` ticks frames by elapsed time. Non-looping animations (`Bark`, `Pant`, `Jump`) set `is_finished = True` on last frame; `app.py` polls this flag to call `notify_animation_finished()` on the active behavior.

Animation keys: `Walk`, `Run`, `Bark`, `Idle`, `Pant`, `Sit`, `Rest`, `Jump`.  
Direction keys: `north`, `south`, `east`, `west`.

## CursorContext Fields (computed each tick)

```python
cursor_x, cursor_y          # raw QCursor.pos()
dog_x, dog_y                # current dog window position
horizontal_distance         # abs(settled_cursor_x - dog_x)
move_direction              # "east" | "west" (cursor vs dog)
bark_direction_4            # "north" | "south" | "east" | "west" (cursor relative to dog)
cursor_idle_seconds         # seconds since cursor moved > cursor_move_threshold_px (30 px)
running_seconds             # cumulative seconds dog has been running (reset on follow exit)
run_threshold               # pant trigger (randomized per run session)
```

## Config Reference (`config.toml`)

| Key | Default | Meaning |
|---|---|---|
| `near_x_px` | 100 | Horizontal distance (px) considered "near" cursor |
| `far_x_px` | 280 | Beyond this → dog runs instead of walks |
| `arrival_x_px` | 65 | Cursor this close → arrival-sit triggers |
| `bark_active_window_s` | 30 | Max cursor idle seconds for bark to trigger |
| `wander_threshold_s` | 8 | Idle seconds before wander activates |
| `sit_threshold_s` | 20 | Idle seconds before idle-sit |
| `rest_threshold_s` | 60 | Idle seconds before rest |
| `walk_speed_px` | 1.2 | Pixels per tick at walk speed |
| `run_speed_px` | 2.8 | Pixels per tick at run speed |

## Logging

Logs write to `%USERPROFILE%\.barkoder\barkoder_<timestamp>.log`. Logger hierarchy rooted at `barkoder`. Key child loggers: `barkoder.bark`, `barkoder.follow`, `barkoder.jump`, `barkoder.wander`, `barkoder.bt`, `barkoder.bt.tree`. Run with `--debug` to also get DEBUG to stderr.

## Dev Mode (system tray)

Right-click tray → "Dev Mode" checkbox → "▶ Trigger Animation" submenu. Plays a 1-second override animation directly. `AnimationRequest` must be imported from `barkoder.behaviors.base` in `app.py` for this to work.

## Pre-existing Test Failures (not caused by recent work)

`test_jump`, `test_pant`, `test_audio` — 20 tests fail due to constructor mismatches or stale test expectations. Bark, follow, idle, wander, arrival-sit, rest, idle-sit, bt-nodes, config, tracker, animation tests all pass.
