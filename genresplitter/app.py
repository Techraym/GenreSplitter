from __future__ import annotations

import sys
import traceback
import faulthandler
from datetime import datetime

import os
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from .ui import MainWindow, SplashScreen, DARK_QSS


def run_app() -> int:
    """Run the GenreSplitter GUI application."""
    # Defensive: log any unhandled exceptions to a file so "silent" crashes
    # can be diagnosed.
    log_dir = os.path.join(os.path.expanduser("~"), ".genresplitter")
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        log_dir = os.getcwd()

    crash_log = os.path.join(log_dir, "crash.log")
    try:
        faulthandler.enable(open(crash_log, "a", encoding="utf-8"))
    except Exception:
        # If this fails, continue without faulthandler.
        pass

    def _excepthook(exc_type, exc, tb):
        try:
            with open(crash_log, "a", encoding="utf-8") as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"[{datetime.now().isoformat(timespec='seconds')}] Unhandled exception\n")
                traceback.print_exception(exc_type, exc, tb, file=f)
        except Exception:
            pass
        # Also print to stderr for development runs.
        traceback.print_exception(exc_type, exc, tb)

    sys.excepthook = _excepthook

    app = QApplication(sys.argv)
    # v2.10.0: set application icon (Logo.ico)
    try:
        from PyQt6.QtGui import QIcon
        _icon_path = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "Logo.ico"))
        if os.path.exists(_icon_path):
            app.setWindowIcon(QIcon(_icon_path))
    except Exception:
        pass
    # v2.10.3: inject asset paths into stylesheet (reliable QSS icons)
    qss = DARK_QSS
    try:
        _root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _arrow = os.path.join(_root_dir, 'assets', 'arrow_down_light.png')
        _arrow = os.path.abspath(_arrow).replace('\\', '/')
        qss = qss.replace('{ARROW_ICON_URL}', f'"file:///{_arrow}"')
    except Exception:
        qss = qss.replace('{ARROW_ICON_URL}', '')
    app.setStyleSheet(qss)
    title = "GenreSplitter"



    
    subtitle = "Release v2.10.1"
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logo.svg")

    splash = SplashScreen(title=title, subtitle=subtitle, logo_path=logo_path)
    splash.show()
    splash.raise_()
    splash.activateWindow()

    # Create the main window early so heavy UI work happens while the splash is visible.
    w = MainWindow()

    # Make the splash progress/status feel ~5 seconds slower by scheduling updates.
    # Total duration: 5000 ms.
    steps = [
        (0, "Settings laden…", 25),
        (2000, "UI laden…", 55),
        (4500, "Gereed.", 100),
    ]

    for delay_ms, msg, pct in steps:
        QTimer.singleShot(delay_ms, lambda m=msg, p=pct: splash.set_status(m, p))

    def _show_main() -> None:
        splash.close()
        w.show()

    QTimer.singleShot(5000, _show_main)

    return app.exec()