from __future__ import annotations

import sys

import os
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from .ui import MainWindow, SplashScreen, DARK_QSS


def run_app() -> int:
    """Run the GenreSplitter GUI application."""
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)

    title = "GenreSplitter"



    
    subtitle = "Release v2.9.0-hotfix5."
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