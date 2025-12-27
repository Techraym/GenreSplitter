"""Logging configuration for GenreSplitter.

In the final release, debug logging is disabled by default.
When enabled, a per-run log file is created and both file and console handlers are configured.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(app_name: str = "genresplitter", enabled: bool = False) -> Optional[Path]:
    """
    Configure logging.

    If enabled=False (default), logging is configured to a minimal WARNING-level console logger
    and no log file is created. Returns None.

    If enabled=True, creates a per-run log file under ./logs and returns its path.
    """
    if not enabled:
        # Minimal console logging only; no file output.
        logging.basicConfig(
            level=logging.WARNING,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        return None

    root = Path(__file__).resolve().parent.parent  # project root (where main.py lives)
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / f"{app_name}_{datetime.now():%Y-%m-%d_%H%M%S}.log"

    # Avoid duplicate handlers if called more than once.
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers to prevent duplicates.
    for h in list(logger.handlers):
        logger.removeHandler(h)

    fh = logging.FileHandler(log_path, encoding="utf-8")
    sh = logging.StreamHandler(sys.stdout)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)

    return log_path
