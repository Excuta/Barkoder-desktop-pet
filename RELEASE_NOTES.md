# Barkoder v1.0.0

First public release. A pixel-art dog that lives on your Windows taskbar, follows your cursor, barks at you, and wanders around when you're idle.

---

## What's in v1.0.0

### Behaviors
- **Follow** — walks or runs toward the cursor depending on distance; suppresses briefly after arriving so the dog doesn't oscillate
- **Bark + walk** — greets the cursor with a bark then a short walk when you've been near for a while; 12-second cooldown between greets
- **Jump** — physics-based arc (pre-sit pause → projectile → landing sit) when the cursor is held high and close; 65% chance per arrival
- **Pant** — catches breath on a random interval (20–40 s) after running; plays 2–4 pant cycles
- **Wander** — roams the screen when the cursor is idle; walks to the physical screen edge then reverses
- **Arrival sit** — sits when the cursor pulls very close, then wanders away after a hold
- **Idle sit / Rest** — sits after 20 s idle, lies down after 60 s idle

### Animation & Audio
- Full 4-directional sprite set: Walk, Run, Bark, Idle, Pant, Sit, Rest, Jump
- Physics y-offset applied during jump arc so the dog visually leaves the ground
- Random bark sound picked from `assets/audio/` on each bark
- Direction hash suffixes in asset folder names stripped automatically at load time

### App
- Frameless, always-on-top transparent window that stays above the taskbar
- System tray: Mute, Start on Boot, Dev Mode (trigger any animation on demand), Quit
- Per-session log files in `%USERPROFILE%\.barkoder\` (10 most recent kept)
- Resilient tick loop — exceptions are logged and recovered without crashing
- Missing animation frames fall back to Idle with a log warning instead of crashing
- Single-instance enforcement: launching a second copy kills the first

### Configuration
Tune behaviour without rebuilding by editing `config.toml` next to the exe:

| Key | Default |
|---|---|
| `walk_speed_px` | 0.918 |
| `run_speed_px` | 2.142 |
| `near_x_px` | 100 |
| `far_x_px` | 280 |
| `wander_threshold_s` | 8 |
| `rest_threshold_s` | 60 |

### Build
- PyInstaller one-file exe with embedded icon (`assets/icon.ico`, 6 sizes)
- Icon path uses `SPECPATH` so builds work from any working directory

---

## Bug fixes in this release
- Screen edge hard stop: dog idles at the boundary instead of walking in place when cursor is at or beyond the edge
- Wander correctly reaches the physical screen edge then reverses (was stopping short or getting stuck against the right wall due to wrong sprite-size offset in the target picker)
- BTRandomDwell yield pause prevents one-tick bleed-through twitches when switching behaviors
- Cursor position uses a settled/deadzone value to eliminate walk/idle oscillation at thresholds
- Bark-walk cycle now exits cleanly so the 12-second BTCooldown fires correctly

---

## Requirements
- Windows 10/11 (64-bit)
- No install needed — download `barkoder.exe` and run

## Run from source
```powershell
uv sync
uv run python -m barkoder
```

## License
MIT — see LICENSE
