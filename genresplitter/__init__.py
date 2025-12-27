"""GenreSplitter package.

Entrypoint:
  - `genresplitter.app.run_app()`

We keep imports light so headless tools/tests can import the package without Qt.
"""

from .meta import APP_VERSION as __version__

def run_app(*args, **kwargs):
    from .app import run_app as _run_app
    return _run_app(*args, **kwargs)
