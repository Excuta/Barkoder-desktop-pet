import logging
import logging.handlers
from datetime import datetime
from pathlib import Path


def setup_logging(debug: bool = False) -> None:
    log_dir = Path.home() / ".barkoder"
    log_dir.mkdir(exist_ok=True)

    # One file per session, named by start time
    session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"barkoder_{session_time}.log"

    # Keep only the 9 most recent previous logs (+ this one = 10 total)
    existing = sorted(log_dir.glob("barkoder_*.log"))
    for old in existing[:-9]:
        old.unlink(missing_ok=True)

    root = logging.getLogger("barkoder")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s.%(msecs)03d [%(levelname)-5s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if debug else logging.WARNING)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    root.info("Logging initialized → %s", log_path)
