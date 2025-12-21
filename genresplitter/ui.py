from __future__ import annotations

import os
import subprocess
import time
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QDialog,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QPlainTextEdit,
    QCheckBox,
    QRadioButton,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QGroupBox,
    QFrame,
    QSplitter,
    QScrollArea,
    QProgressBar,
    QStatusBar,
    QToolButton,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QSizePolicy,
    QDialogButtonBox,
)
from .meta import APP_NAME, APP_VERSION, APP_DATE, APP_COPYRIGHT, APP_RELEASE_NOTES
from .storage import load_settings, save_settings, LOG_PATH
from .api_resolver import ApiConfig, GenreResolver
from .fpcalc_manager import find_fpcalc
from .workers import SortWorker
from .api_health import (
    test_lastfm, test_discogs, test_spotify, test_musicbrainz, info_acousticbrainz,
    test_theaudiodb, test_itunes, test_rateyourmusic, test_acoustid
)


DARK_QSS = """
QWidget { background-color: #121212; color: #EDEDED; font-size: 13px; }
QLineEdit, QTextEdit { background-color: #1E1E1E; border: 1px solid #2C2C2C; padding: 6px; color: #EDEDED; }
QPushButton {
    background-color: #2A2A2A; border: 1px solid #3A3A3A; padding: 10px 12px;
    border-radius: 8px; color: #F2F2F2; font-weight: 600;
}
QPushButton:hover { background-color: #343434; }
QPushButton:pressed { background-color: #222222; }
QProgressBar { border: 1px solid #2C2C2C; border-radius: 6px; text-align: center; background: #1E1E1E; }
QProgressBar::chunk { background-color: #4B79FF; border-radius: 6px; }
QCheckBox { spacing: 10px; font-size: 14px; }
QCheckBox::indicator { width: 18px; height: 18px; }
QTabWidget::pane { border: 1px solid #2C2C2C; top: -1px; }
QTabBar::tab { background: #1E1E1E; border: 1px solid #2C2C2C; padding: 10px 14px; margin-right: 4px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #2A2A2A; border-color: #4B79FF; }
QTabBar::tab:hover { background: #242424; }
"""



def make_mp3_logo() -> QPixmap:
    pm = QPixmap(96, 96)
    pm.fill(QColor("#121212"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QColor("#EDEDED"))
    p.setBrush(QColor("#1E1E1E"))
    p.drawRoundedRect(8, 8, 80, 80, 14, 14)
    p.setPen(QColor("#EDEDED"))
    f = QFont("Arial", 18)
    f.setBold(True)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "MP3")
    p.end()
    return pm


def load_logo_pixmap(size: int = 96) -> QPixmap:
    """Load logo.svg from the portable app root. Fallback to generated MP3 logo."""
    try:
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        svg_path = os.path.join(app_root, "logo.svg")
        if os.path.exists(svg_path):
            pm = QPixmap(svg_path)
            if not pm.isNull():
                return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    except Exception:
        pass
    return make_mp3_logo()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(720)

        self._s = load_settings()

        tabs = QTabWidget(self)

        tab_general = QWidget()
        tab_lastfm = QWidget()
        tab_discogs = QWidget()
        tab_spotify = QWidget()
        tab_musicbrainz = QWidget()
        tab_acoustid = QWidget()
        tab_acousticbrainz = QWidget()
        tab_theaudiodb = QWidget()
        tab_itunes = QWidget()
        tab_rym = QWidget()

        tabs.addTab(tab_general, "Algemeen")
        tabs.addTab(tab_lastfm, "Last.fm")
        tabs.addTab(tab_discogs, "Discogs")
        tabs.addTab(tab_spotify, "Spotify")
        tabs.addTab(tab_musicbrainz, "MusicBrainz")
        tabs.addTab(tab_acoustid, "AcoustID")
        tabs.addTab(tab_acousticbrainz, "AcousticBrainz")
        tabs.addTab(tab_theaudiodb, "TheAudioDB")
        tabs.addTab(tab_itunes, "Apple iTunes")
        tabs.addTab(tab_rym, "RateYourMusic")

        # ---------- General ----------
        gform = QFormLayout(tab_general)

        self.cb_action_logging = QCheckBox("Log sorteeracties naar bestand")
        self.cb_action_logging.setToolTip(f"Logbestand: {LOG_PATH}")
        self.cb_action_logging.setChecked(bool(self._s.get("enable_action_logging", True)))
        gform.addRow(self.cb_action_logging)

        self.cb_autoclean = QCheckBox("Autoclean bestandsnamen (aanbevolen)")
        self.cb_id3 = QCheckBox("Gebruik ID3 fallback (laatste redmiddel)")
        self.cb_write_id3 = QCheckBox("Schrijf opgehaalde metadata naar ID3 (ID3v2.4)")
        self.cb_run_report = QCheckBox("Schrijf run-rapport (CSV + JSON) naar doelmap")
        self.cb_run_report.setToolTip("Maakt per run een rapport in de doelmap onder _GenreSplitter_Reports.")
        self.cb_write_id3.setToolTip(
            "Schrijft (indien beschikbaar) titel/artist/album/genre/release date/cover art naar ID3v2.4. "
            "Wordt vóór het verplaatsen toegepast."
        )

        self.cb_autoclean.setChecked(bool(self._s.get("autoclean", True)))
        self.cb_id3.setChecked(bool(self._s.get("use_id3_fallback", False)))
        self.cb_write_id3.setChecked(bool(self._s.get("write_id3_metadata", True)))
        self.cb_run_report.setChecked(bool(self._s.get("write_run_report", True)))

        # Metadata update policy
        self.cmb_meta_policy = QComboBox()
        self.cmb_meta_policy.addItem("Altijd overschrijven", "always")
        self.cmb_meta_policy.addItem("Overschrijf alleen bij hoge matchscore", "confidence")
        self.cmb_meta_policy.addItem("Alleen cover bijwerken", "cover_only")
        pol = str(self._s.get("metadata_update_policy", "always")).strip().lower()
        idx = max(0, self.cmb_meta_policy.findData(pol))
        self.cmb_meta_policy.setCurrentIndex(idx)

        self.ed_conf_thr = QLineEdit(str(self._s.get("confidence_threshold", 85)))
        self.ed_conf_thr.setPlaceholderText("0-100")

        gform.addRow(self.cb_autoclean)
        gform.addRow(self.cb_id3)
        gform.addRow(self.cb_write_id3)
        gform.addRow(self.cb_run_report)
        gform.addRow(QLabel("Metadata update"), self.cmb_meta_policy)
        gform.addRow(QLabel("Confidence drempel"), self.ed_conf_thr)

        # API reliability knobs (shared)
        self.ed_timeout = QLineEdit(str(self._s.get("api_timeout_seconds", 25)))
        self.ed_retries = QLineEdit(str(self._s.get("api_retries", 3)))
        self.ed_backoff = QLineEdit(str(self._s.get("api_backoff_seconds", 1.0)))
        self.ed_pause = QLineEdit(str(self._s.get("api_min_pause_seconds", 0.15)))
        self.ed_ab_th = QLineEdit(str(self._s.get("acousticbrainz_threshold", 0.60)))

        gform.addRow(QLabel("API betrouwbaarheid (globaal)"))
        gform.addRow("Timeout (sec)", self.ed_timeout)
        gform.addRow("Retries", self.ed_retries)
        gform.addRow("Backoff (sec)", self.ed_backoff)
        gform.addRow("Min pause (sec)", self.ed_pause)
        gform.addRow("AcousticBrainz threshold", self.ed_ab_th)

        # ---------- Helpers ----------
        def link_label(text: str, url: str) -> QLabel:
            lbl = QLabel(f'<a href="{url}">{text}</a>')
            lbl.setOpenExternalLinks(True)
            return lbl

        def tab_test_row(btn: QPushButton) -> QWidget:
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.addStretch(1)
            h.addWidget(btn)
            return w

        def mk_log() -> QTextEdit:
            te = QTextEdit()
            te.setReadOnly(True)
            te.setMinimumHeight(90)
            return te

        def append_test(log: QTextEdit, name: str, ok: bool, msg: str) -> None:
            ts = time.strftime("%H:%M:%S")
            prefix = "✔" if ok else "✖"
            log.append(f"[{ts}] {prefix} {name}: {msg}")

        # ---------- Last.fm ----------
        lf = QFormLayout(tab_lastfm)
        self.cb_lastfm = QCheckBox("Gebruik Last.fm")
        self.cb_lastfm.setChecked(bool(self._s.get("enable_lastfm", True)))
        self.ed_lastfm_key = QLineEdit(self._s.get("lastfm_api_key", ""))

        self.btn_test_lastfm = QPushButton("Test Last.fm")
        self.log_lastfm = mk_log()

        lf.addRow(self.cb_lastfm)
        lf.addRow(link_label("Vraag hier een Last.fm API key aan", "https://www.last.fm/api/account/create"))
        lf.addRow("API key", self.ed_lastfm_key)
        lf.addRow(tab_test_row(self.btn_test_lastfm))
        lf.addRow("Resultaat", self.log_lastfm)

        self.btn_test_lastfm.clicked.connect(lambda: append_test(self.log_lastfm, "Last.fm", *test_lastfm(self.ed_lastfm_key.text())))

        # ---------- Discogs ----------
        df = QFormLayout(tab_discogs)
        self.cb_discogs = QCheckBox("Gebruik Discogs")
        self.cb_discogs.setChecked(bool(self._s.get("enable_discogs", True)))
        self.ed_discogs_token = QLineEdit(self._s.get("discogs_token", ""))
        self.ed_discogs_token.setEchoMode(QLineEdit.EchoMode.Password)

        self.btn_test_discogs = QPushButton("Test Discogs")
        self.log_discogs = mk_log()

        df.addRow(self.cb_discogs)
        df.addRow(link_label("Vraag hier een Discogs user token aan", "https://www.discogs.com/settings/developers"))
        df.addRow("User token", self.ed_discogs_token)
        df.addRow(tab_test_row(self.btn_test_discogs))
        df.addRow("Resultaat", self.log_discogs)

        self.btn_test_discogs.clicked.connect(lambda: append_test(self.log_discogs, "Discogs", *test_discogs(self.ed_discogs_token.text())))

        # ---------- Spotify ----------
        sf = QFormLayout(tab_spotify)
        self.cb_spotify = QCheckBox("Gebruik Spotify")
        self.cb_spotify.setChecked(bool(self._s.get("enable_spotify", True)))
        self.ed_spotify_id = QLineEdit(self._s.get("spotify_client_id", ""))
        self.ed_spotify_secret = QLineEdit(self._s.get("spotify_client_secret", ""))
        self.ed_spotify_secret.setEchoMode(QLineEdit.EchoMode.Password)

        self.btn_test_spotify = QPushButton("Test Spotify")
        self.log_spotify = mk_log()

        sf.addRow(self.cb_spotify)
        sf.addRow(link_label("Open Spotify Developer Dashboard", "https://developer.spotify.com/dashboard"))
        sf.addRow("Client ID", self.ed_spotify_id)
        sf.addRow("Client Secret", self.ed_spotify_secret)
        sf.addRow(tab_test_row(self.btn_test_spotify))
        sf.addRow("Resultaat", self.log_spotify)

        self.btn_test_spotify.clicked.connect(lambda: append_test(self.log_spotify, "Spotify", *test_spotify(self.ed_spotify_id.text(), self.ed_spotify_secret.text())))

        # ---------- MusicBrainz ----------
        mbf = QFormLayout(tab_musicbrainz)
        self.cb_musicbrainz = QCheckBox("Gebruik MusicBrainz")
        self.cb_musicbrainz.setChecked(bool(self._s.get("enable_musicbrainz", True)))

        self.btn_test_musicbrainz = QPushButton("Test MusicBrainz")
        self.log_musicbrainz = mk_log()

        mbf.addRow(self.cb_musicbrainz)
        mbf.addRow(link_label("MusicBrainz API documentatie (geen API key nodig)", "https://musicbrainz.org/doc/MusicBrainz_API"))
        mbf.addRow(tab_test_row(self.btn_test_musicbrainz))
        mbf.addRow("Resultaat", self.log_musicbrainz)

        self.btn_test_musicbrainz.clicked.connect(lambda: append_test(self.log_musicbrainz, "MusicBrainz", *test_musicbrainz()))

        
        # ---------- AcoustID ----------
        self.cb_acoustid = QCheckBox("Gebruik AcoustID fingerprint lookup (requires fpcalc)")
        self.cb_acoustid.setChecked(bool(self._s.get("enable_acoustid", False)))

        self.ed_acoustid_key = QLineEdit()
        self.ed_acoustid_key.setPlaceholderText("AcoustID API key")
        self.ed_acoustid_key.setText(self._s.get("acoustid_api_key", ""))
        self.ed_acoustid_key.setEchoMode(QLineEdit.EchoMode.Password)

        self.ed_acoustid_min_score = QLineEdit()
        self.ed_acoustid_min_score.setPlaceholderText("0.6")
        self.ed_acoustid_min_score.setText(str(self._s.get("acoustid_min_score", 0.6)))

        af = QFormLayout(tab_acoustid)
        af.addRow(self.cb_acoustid)
        af.addRow("AcoustID API key", self.ed_acoustid_key)
        af.addRow("Minimum score", self.ed_acoustid_min_score)

        self.btn_test_fpcalc = QPushButton("Test fpcalc")
        self.btn_test_acoustid = QPushButton("Test AcoustID")
        self.log_acoustid = mk_log()

        af.addRow(tab_test_row(self.btn_test_fpcalc))
        af.addRow(tab_test_row(self.btn_test_acoustid))
        af.addRow("Resultaat", self.log_acoustid)

        self.btn_test_fpcalc.clicked.connect(self._test_fpcalc)
        self.btn_test_acoustid.clicked.connect(
            lambda: append_test(self.log_acoustid, "AcoustID", *test_acoustid(self.ed_acoustid_key.text()))
        )

        lbl_fp = QLabel("If fpcalc is missing, GenreSplitter can download it from the official Chromaprint page on first use.")
        lbl_fp.setWordWrap(True)
        af.addRow(lbl_fp)

        # ---------- AcousticBrainz ----------
        abf = QFormLayout(tab_acousticbrainz)
        self.cb_acousticbrainz = QCheckBox("Gebruik AcousticBrainz (Essentia) [probabilistisch]")
        self.cb_acousticbrainz.setChecked(bool(self._s.get("enable_acousticbrainz", False)))

        self.btn_info_acousticbrainz = QPushButton("Info")
        self.log_acousticbrainz = mk_log()

        abf.addRow(self.cb_acousticbrainz)
        abf.addRow(link_label("AcousticBrainz docs", "https://acousticbrainz.readthedocs.io/api.html"))
        abf.addRow(tab_test_row(self.btn_info_acousticbrainz))
        abf.addRow("Resultaat", self.log_acousticbrainz)

        self.btn_info_acousticbrainz.clicked.connect(lambda: append_test(self.log_acousticbrainz, "AcousticBrainz", *info_acousticbrainz()))

        # ---------- TheAudioDB ----------
        tdf = QFormLayout(tab_theaudiodb)
        self.cb_theaudiodb = QCheckBox("Gebruik TheAudioDB")
        self.cb_theaudiodb.setChecked(bool(self._s.get("enable_theaudiodb", False)))
        self.ed_theaudiodb_key = QLineEdit(self._s.get("theaudiodb_api_key", ""))

        self.btn_test_theaudiodb = QPushButton("Test TheAudioDB")
        self.log_theaudiodb = mk_log()

        tdf.addRow(self.cb_theaudiodb)
        tdf.addRow(link_label("Vraag hier een TheAudioDB API key aan", "https://www.theaudiodb.com/api_apply.php"))
        tdf.addRow("API key", self.ed_theaudiodb_key)
        tdf.addRow(tab_test_row(self.btn_test_theaudiodb))
        tdf.addRow("Resultaat", self.log_theaudiodb)

        self.btn_test_theaudiodb.clicked.connect(lambda: append_test(self.log_theaudiodb, "TheAudioDB", *test_theaudiodb(self.ed_theaudiodb_key.text())))

        # ---------- Apple iTunes ----------
        itf = QFormLayout(tab_itunes)
        self.cb_itunes = QCheckBox("Gebruik Apple iTunes Search")
        self.cb_itunes.setChecked(bool(self._s.get("enable_itunes", True)))

        self.btn_test_itunes = QPushButton("Test iTunes Search")
        self.log_itunes = mk_log()

        itf.addRow(self.cb_itunes)
        itf.addRow(link_label("Apple iTunes Search API (geen API key nodig)", "https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/"))
        itf.addRow(tab_test_row(self.btn_test_itunes))
        itf.addRow("Resultaat", self.log_itunes)

        self.btn_test_itunes.clicked.connect(lambda: append_test(self.log_itunes, "iTunes", *test_itunes()))

        # ---------- RateYourMusic ----------
        ryf = QFormLayout(tab_rym)
        self.cb_rym = QCheckBox("Gebruik RateYourMusic (experimenteel)")
        self.cb_rym.setChecked(bool(self._s.get("enable_rateyourmusic", False)))
        self.ed_rym_cookie = QLineEdit(self._s.get("rateyourmusic_cookie", ""))
        self.ed_rym_cookie.setEchoMode(QLineEdit.EchoMode.Password)

        self.btn_test_rym = QPushButton("Test RateYourMusic")
        self.log_rym = mk_log()

        ryf.addRow(self.cb_rym)
        ryf.addRow(QLabel("Let op: RateYourMusic heeft geen officiële publieke API. Dit is best-effort en kan breken."))
        ryf.addRow(link_label("RateYourMusic website", "https://rateyourmusic.com"))
        ryf.addRow("Cookie/token", self.ed_rym_cookie)
        ryf.addRow(tab_test_row(self.btn_test_rym))
        ryf.addRow("Resultaat", self.log_rym)

        self.btn_test_rym.clicked.connect(lambda: append_test(self.log_rym, "RateYourMusic", *test_rateyourmusic(self.ed_rym_cookie.text())))

        # ---------- Buttons ----------
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addWidget(tabs)
        root.addWidget(buttons)

    def _test_fpcalc(self):
        """Diagnostic helper for Chromaprint fpcalc."""
        fp = find_fpcalc()
        if not fp:
            QMessageBox.warning(
                self,
                "fpcalc not found",
                "Chromaprint fpcalc was not found.\n\n"
                "If it is installed, ensure it is in PATH or set GENRESPLITTER_FPCALC to the full path of fpcalc.exe."
            )
            return
    
        try:
            cp = subprocess.run([fp, "-version"], capture_output=True, text=True, timeout=5)
            out = (cp.stdout or "").strip()
            err = (cp.stderr or "").strip()
            msg = f"fpcalc path:\n{fp}\n\nExit code: {cp.returncode}\n\n"
            if out:
                msg += f"Output:\n{out}\n\n"
            if err:
                msg += f"Errors:\n{err}\n\n"
            QMessageBox.information(self, "fpcalc test result", msg)
        except Exception as e:
            QMessageBox.critical(self, "fpcalc test failed", f"fpcalc path:\n{fp}\n\nError:\n{e}")
    
    
    
    def accept(self):
        # Persist settings
        s = dict(self._s)

        s["autoclean"] = bool(self.cb_autoclean.isChecked())
        s["use_id3_fallback"] = bool(self.cb_id3.isChecked())
        s["write_id3_metadata"] = bool(self.cb_write_id3.isChecked())
        s["write_run_report"] = bool(getattr(self, "cb_run_report", QCheckBox()).isChecked())

        # metadata update policy
        s["metadata_update_policy"] = str(getattr(self, "cmb_meta_policy", QComboBox()).currentData() or "always").strip().lower()
        try:
            s["confidence_threshold"] = int(str(getattr(self, "ed_conf_thr", QLineEdit("85")).text()).strip() or "85")
        except Exception:
            s["confidence_threshold"] = 85
        s["enable_action_logging"] = bool(self.cb_action_logging.isChecked())

        # enable flags
        s["enable_lastfm"] = bool(self.cb_lastfm.isChecked())
        s["enable_discogs"] = bool(self.cb_discogs.isChecked())
        s["enable_spotify"] = bool(self.cb_spotify.isChecked())
        s["enable_musicbrainz"] = bool(self.cb_musicbrainz.isChecked())
        s["enable_acousticbrainz"] = bool(self.cb_acousticbrainz.isChecked())
        s["enable_theaudiodb"] = bool(self.cb_theaudiodb.isChecked())
        s["enable_itunes"] = bool(self.cb_itunes.isChecked())
        s["enable_acoustid"] = bool(getattr(self, "cb_acoustid", QCheckBox()).isChecked())
        s["enable_rateyourmusic"] = bool(self.cb_rym.isChecked())

        # credentials
        s["lastfm_api_key"] = self.ed_lastfm_key.text().strip()
        s["discogs_token"] = self.ed_discogs_token.text().strip()
        s["spotify_client_id"] = self.ed_spotify_id.text().strip()
        s["spotify_client_secret"] = self.ed_spotify_secret.text().strip()
        s["theaudiodb_api_key"] = self.ed_theaudiodb_key.text().strip()
        s["rateyourmusic_cookie"] = self.ed_rym_cookie.text().strip()
        s["acoustid_api_key"] = getattr(self, "ed_acoustid_key", QLineEdit()).text().strip()
        try:
            s["acoustid_min_score"] = float(getattr(self, "ed_acoustid_min_score", QLineEdit()).text().strip() or "0.6")
        except Exception:
            s["acoustid_min_score"] = 0.6

        # reliability knobs
        def _int(x, d): 
            try: return int(str(x).strip())
            except: return d
        def _float(x, d):
            try: return float(str(x).strip())
            except: return d

        s["api_timeout_seconds"] = _int(self.ed_timeout.text(), 25)
        s["api_retries"] = _int(self.ed_retries.text(), 3)
        s["api_backoff_seconds"] = _float(self.ed_backoff.text(), 1.0)
        s["api_min_pause_seconds"] = _float(self.ed_pause.text(), 0.15)
        s["acousticbrainz_threshold"] = _float(self.ed_ab_th.text(), 0.60)

        save_settings(s)
        super().accept()



class SplashScreen(QWidget):
    """
    Simple interactive splash screen with:
    - logo + text header aligned on a grid
    - status line + progress bar (updates live)
    """
    def __init__(self, title: str = "GenreSplitter", subtitle: str = "Beta", logo_path: str = "logo.svg"):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        self.setObjectName("SplashScreen")
        self.setFixedSize(780, 390)  # ~50% larger than previous default

        # Outer layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 32)
        outer.setSpacing(18)

        # Header row: logo + text column
        header_row = QHBoxLayout()
        header_row.setSpacing(24)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(160, 160)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_logo(logo_path)

        header_row.addWidget(self.logo_label, 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("SplashTitle")
        self.title_label.setWordWrap(True)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("SplashSubtitle")
        self.subtitle_label.setWordWrap(True)

        self.copyright_label = QLabel("Copyright © 2025 R. Snijder. All rights reserved.")
        self.copyright_label.setObjectName("SplashCopyright")
        self.copyright_label.setWordWrap(True)

        text_col.addWidget(self.title_label)
        text_col.addWidget(self.subtitle_label)
        text_col.addSpacing(8)
        text_col.addWidget(self.copyright_label)
        text_col.addStretch(1)

        header_row.addLayout(text_col, 1)

        outer.addLayout(header_row)
        outer.addStretch(1)

        # Status + progress
        self.status_label = QLabel("Initialiseren…")
        self.status_label.setObjectName("SplashStatus")
        self.status_label.setWordWrap(True)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)

        outer.addWidget(self.status_label)
        outer.addWidget(self.progress)

        self.setStyleSheet(self._qss())

    def _set_logo(self, logo_path: str):
        # Prefer SVG if available via QtSvg; fall back to QPixmap
        try:
            from PyQt6.QtSvgWidgets import QSvgWidget  # noqa: F401
            # render SVG to pixmap via QSvgRenderer for QLabel
            from PyQt6.QtSvg import QSvgRenderer
            from PyQt6.QtGui import QImage, QPainter
            renderer = QSvgRenderer(logo_path)
            img = QImage(self.logo_label.width(), self.logo_label.height(), QImage.Format.Format_ARGB32)
            img.fill(Qt.GlobalColor.transparent)
            p = QPainter(img)
            renderer.render(p)
            p.end()
            self.logo_label.setPixmap(QPixmap.fromImage(img))
        except Exception:
            pm = QPixmap(logo_path)
            if not pm.isNull():
                self.logo_label.setPixmap(pm.scaled(
                    self.logo_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))

    def set_status(self, text: str, progress: int | None = None):
        self.status_label.setText(text)
        if progress is not None:
            self.progress.setValue(int(progress))
        QApplication.processEvents()

    def _qss(self) -> str:
        # Keep it self-contained; relies on dark background already used in app
        return """
        QWidget#SplashScreen {
            background: #111;
            border: 1px solid #2a2a2a;
        }
        QLabel#SplashTitle {
            color: #f3f3f3;
            font-size: 22px;
            font-weight: 700;
        }
        QLabel#SplashSubtitle {
            color: #cfcfcf;
            font-size: 14px;
        }
        QLabel#SplashCopyright {
            color: #9a9a9a;
            font-size: 12px;
        }
        QLabel#SplashStatus {
            color: #e6e6e6;
            font-size: 13px;
        }
        QProgressBar {
            height: 18px;
            border-radius: 9px;
            border: 1px solid #2a2a2a;
            background: #1b1b1b;
        }
        QProgressBar::chunk {
            background: #3d73ff;
            border-radius: 9px;
        }
        """


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(820, 540)

        self.source_dir: Optional[str] = None
        self.target_dir: Optional[str] = None
        self.worker: Optional[SortWorker] = None

        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # header
        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(load_logo_pixmap(144))
        header.addWidget(logo)
        title = QLabel(f"<b>{APP_NAME}</b>  v{APP_VERSION}  ({APP_DATE})")
        title.setTextFormat(Qt.TextFormat.RichText)
        header.addWidget(title)
        header.addStretch(1)
        btn_settings = QPushButton("Settings")
        btn_settings.clicked.connect(self.open_settings)
        header.addWidget(btn_settings)
        root.addLayout(header)

        subtitle = QLabel(APP_RELEASE_NOTES)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #cfcfcf; font-size: 12px;")
        root.addWidget(subtitle)

        # source/target
        row1 = QHBoxLayout()
        self.ed_source = QLineEdit()
        self.ed_source.setPlaceholderText("Bronmap...")
        btn_browse_source = QPushButton("Kies bron")
        btn_browse_source.clicked.connect(self.browse_source)
        row1.addWidget(self.ed_source)
        row1.addWidget(btn_browse_source)
        root.addLayout(row1)

        row2 = QHBoxLayout()
        self.ed_target = QLineEdit()
        self.ed_target.setPlaceholderText("Doelmap...")
        btn_browse_target = QPushButton("Kies doel")
        btn_browse_target.clicked.connect(self.browse_target)
        row2.addWidget(self.ed_target)
        row2.addWidget(btn_browse_target)
        root.addLayout(row2)

        row3 = QHBoxLayout()
        self.cb_dry = QCheckBox("Dry-run (niet verplaatsen)")
        row3.addWidget(self.cb_dry)
        row3.addStretch(1)
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self.start_sort)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stop_sort)
        self.btn_stop.setEnabled(False)
        row3.addWidget(self.btn_start)
        row3.addWidget(self.btn_stop)
        root.addLayout(row3)

        self.progress = QProgressBar()
        root.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        root.addWidget(self.log, 1)

        footer = QLabel(APP_COPYRIGHT)
        footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(footer)

        # load last paths from settings if present
        s = load_settings()
        if s.get("last_source_dir"):
            self.ed_source.setText(s.get("last_source_dir"))
        if s.get("last_target_dir"):
            self.ed_target.setText(s.get("last_target_dir"))

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def browse_source(self):
        d = QFileDialog.getExistingDirectory(self, "Kies bronmap")
        if d:
            self.ed_source.setText(d)

    def browse_target(self):
        d = QFileDialog.getExistingDirectory(self, "Kies doelmap")
        if d:
            self.ed_target.setText(d)

    def _append_log(self, line: str, *, action: bool = False) -> None:
        self.log.append(line)
        # Auto-scroll: always follow the newest record
        try:
            self.log.moveCursor(QTextCursor.MoveOperation.End)
            sb = self.log.verticalScrollBar()
            sb.setValue(sb.maximum())
        except Exception:
            pass

        # Optional file logging for *sorteeracties* only
        if action:
            try:
                s = load_settings()
                if bool(s.get("enable_action_logging", True)):
                    os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
                    with open(LOG_PATH, "a", encoding="utf-8", buffering=1) as f:
                        f.write(line + "\n")
                        f.flush()
            except Exception:
                pass

    def start_sort(self):
        source = self.ed_source.text().strip()
        target = self.ed_target.text().strip()
        if not source or not os.path.isdir(source):
            QMessageBox.warning(self, "Fout", "Selecteer een geldige bronmap")
            return
        if not target:
            QMessageBox.warning(self, "Fout", "Selecteer een doelmap")
            return

        s = load_settings()
        s["last_source_dir"] = source
        s["last_target_dir"] = target
        save_settings(s)

        self.progress.setValue(0)
        self.log.clear()
        self._append_log(f"{APP_NAME} v{APP_VERSION}")
        self._append_log(f"Start: bron={source} doel={target}", action=True)

        cfg = ApiConfig(
            lastfm_key=s.get("lastfm_api_key", ""),
            spotify_client_id=s.get("spotify_client_id", ""),
            spotify_client_secret=s.get("spotify_client_secret", ""),
            discogs_token=s.get("discogs_token", ""),
            theaudiodb_api_key=s.get("theaudiodb_api_key", ""),
            rateyourmusic_cookie=s.get("rateyourmusic_cookie", ""),
            enable_lastfm=bool(s.get("enable_lastfm", True)),
            enable_discogs=bool(s.get("enable_discogs", True)),
            enable_spotify=bool(s.get("enable_spotify", True)),
            enable_musicbrainz=bool(s.get("enable_musicbrainz", True)),
            enable_acousticbrainz=bool(s.get("enable_acousticbrainz", False)),
            enable_theaudiodb=bool(s.get("enable_theaudiodb", False)),
            enable_itunes=bool(s.get("enable_itunes", True)),
            enable_rateyourmusic=bool(s.get("enable_rateyourmusic", False)),
            timeout_seconds=int(s.get("api_timeout_seconds", 25)),
            retries=int(s.get("api_retries", 3)),
            backoff_seconds=float(s.get("api_backoff_seconds", 1.0)),
            min_pause_seconds=float(s.get("api_min_pause_seconds", 0.15)),
            acousticbrainz_threshold=float(s.get("acousticbrainz_threshold", 0.60)),
        )

        resolver = GenreResolver(cfg, self._append_log)
        self.worker = SortWorker(
            source_dir=source,
            target_dir=target,
            resolver=resolver,
            use_id3_fallback=bool(s.get("use_id3_fallback", False)),
            dry_run=bool(self.cb_dry.isChecked()),
            write_id3_metadata=bool(s.get("write_id3_metadata", True)),
            write_run_report=bool(s.get("write_run_report", True)),
            metadata_update_policy=str(s.get("metadata_update_policy", "always")).strip().lower(),
            confidence_threshold=int(s.get("confidence_threshold", 85)),
        )

        self.worker.message.connect(lambda m: self._append_log(m, action=True))
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_done_ok)
        self.worker.finished_err.connect(self._on_done_err)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.worker.start()

    def stop_sort(self):
        if self.worker:
            self.worker.stop()
            self._append_log("Stop requested...", action=True)

    def _on_progress(self, done: int, total: int) -> None:
        if total <= 0:
            self.progress.setValue(0)
            return
        pct = int((done / total) * 100)
        self.progress.setValue(pct)

    def _on_done_ok(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._append_log("Klaar.", action=True)

    def _on_done_err(self, msg: str):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        QMessageBox.critical(self, "Fout", msg)
        self._append_log(f"ERROR: {msg}", action=True)