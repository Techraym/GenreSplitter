"""Legacy shim.

This file used to contain the full application. It now delegates to the
modular `genresplitter` package to keep the codebase manageable.
"""

from genresplitter.app import run_app


if __name__ == "__main__":
    raise SystemExit(run_app())
