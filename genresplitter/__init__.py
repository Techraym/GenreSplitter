"""GenreSplitter package.

This package contains the modular implementation of the portable GenreSplitter app.

Entrypoint:
  - `genresplitter.app.run_app()`
"""

from .app import run_app  # noqa: F401


from .meta import APP_VERSION as __version__
