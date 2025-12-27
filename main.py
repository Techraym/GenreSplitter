"""GenreSplitter entrypoint."""

from __future__ import annotations

import logging
import os
import sys

from genresplitter.logging_config import setup_logging


def _install_excepthook() -> None:
    def excepthook(exc_type, exc, tb):
        logging.critical("Uncaught exception", exc_info=(exc_type, exc, tb))
    sys.excepthook = excepthook


# Debug logging is disabled by default for the final release.
# Enable by setting environment variable: GENRESPLITTER_DEBUG_LOG=1
DEBUG_LOGGING = os.environ.get("GENRESPLITTER_DEBUG_LOG", "").strip() in {"1", "true", "TRUE", "yes", "YES"}

LOG_FILE = setup_logging("genresplitter", enabled=DEBUG_LOGGING)
if DEBUG_LOGGING:
    _install_excepthook()
    logging.info("Debug logging enabled. Log file: %s", LOG_FILE)

from genresplitter.app import run_app  # noqa: E402  (import after logging setup)


if __name__ == "__main__":
    raise SystemExit(run_app())
