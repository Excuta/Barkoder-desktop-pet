# Barkoder

A pixel-art dog that lives on your Windows taskbar. He follows your cursor, barks at you, wanders around when you're away, and occasionally jumps.

Built with PyQt6. No installer needed — just run the exe.

---

## Download

Grab the latest `barkoder.exe` from [Releases](../../releases).

---

## Run from Source

**Requirements:** Python 3.11+, [uv](https://docs.astral.sh/uv/)

```powershell
git clone https://github.com/YahiaFarid/barkoder
cd barkoder
uv sync
uv run python -m barkoder
```

Pass `--debug` to also stream logs to stderr:

```powershell
uv run python -m barkoder --debug
```

---

## Build

```powershell
uv run pyinstaller barkoder.spec
# exe lands at dist\barkoder.exe
```

---

## Tune Behaviour

Edit `config.toml` next to the exe (or in the repo root) to adjust speeds, thresholds, and timing without rebuilding:

| Key | Default | Meaning |
|---|---|---|
| `walk_speed_px` | 0.918 | Pixels per tick at walk speed |
| `run_speed_px` | 2.142 | Pixels per tick at run speed |
| `near_x_px` | 100 | Distance (px) considered "near" cursor |
| `far_x_px` | 280 | Beyond this → dog runs |
| `wander_threshold_s` | 8 | Idle seconds before wander starts |
| `rest_threshold_s` | 60 | Idle seconds before dog lies down |

---

## System Tray

Right-click the tray icon for: Mute, Start on Boot, Dev Mode (trigger animations), Quit.

Logs are written to `%USERPROFILE%\.barkoder\` (10 most recent sessions kept).

---

## License

MIT — see [LICENSE](LICENSE).
