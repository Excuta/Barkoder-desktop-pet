import logging
import logging.handlers
from pathlib import Path


def setup_logging(debug: bool = False) -> None:
    log_dir = Path.home() / ".barkoder"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "barkoder.log"

    root = logging.getLogger("barkoder")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s.%(msecs)03d [%(levelname)-5s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    fh = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if debug else logging.WARNING)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    root.info("Logging initialized → %s", log_path)
