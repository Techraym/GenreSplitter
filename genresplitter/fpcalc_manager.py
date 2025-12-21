from __future__ import annotations

import os
import glob
import shutil

def _candidate_paths() -> list[str]:
    # Common Windows install locations (best-effort)
    cand: list[str] = []
    pf = os.environ.get("ProgramFiles", r"C:\\Program Files")
    pfx86 = os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)")
    lad = os.environ.get("LOCALAPPDATA", "")
    ad = os.environ.get("APPDATA", "")
    # Typical Chromaprint installs
    cand += [
        os.path.join(pf, "Chromaprint", "fpcalc.exe"),
        os.path.join(pfx86, "Chromaprint", "fpcalc.exe"),
        os.path.join(lad, "Chromaprint", "fpcalc.exe"),
        os.path.join(lad, "Programs", "Chromaprint", "fpcalc.exe"),
        os.path.join(lad, "Microsoft", "WinGet", "Links", "fpcalc.exe"),
    ]

    # WinGet installs may place fpcalc under Packages (PowerShell can resolve it even if PATH does not include it).
    if os.name == "nt" and lad:
        pkg_root = os.path.join(lad, "Microsoft", "WinGet", "Packages")
        # Typical layout: ...\Packages\<PackageId>\<Version>\<payload>\fpcalc.exe
        cand += glob.glob(os.path.join(pkg_root, "*", "*", "*", "fpcalc.exe"))
        # Some packages nest the payload one level differently
        cand += glob.glob(os.path.join(pkg_root, "*", "*", "chromaprint-fpcalc-*", "fpcalc.exe"))
        # Some WinGet packages omit a version folder and place payload directly under the package id
        cand += glob.glob(os.path.join(pkg_root, "*", "chromaprint-fpcalc-*", "fpcalc.exe"))
        cand += glob.glob(os.path.join(pkg_root, "*", "*", "fpcalc.exe"))
        # Last resort: recursive search (bounded to WinGet Packages subtree).
        # This is more expensive but makes detection resilient to layout changes.
        cand += glob.glob(os.path.join(pkg_root, "**", "fpcalc.exe"), recursive=True)
    # Chocolatey puts shims in its bin directory
    cand += [
        os.path.join(os.environ.get("ChocolateyInstall", r"C:\\ProgramData\\chocolatey"), "bin", "fpcalc.exe"),
    ]
    # GenreSplitter-managed location
    cand += [
        os.path.join(ad, "GenreSplitter", "bin", "fpcalc.exe"),
    ]
    # De-duplicate while preserving order
    seen = set()
    out: list[str] = []
    for c in cand:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def find_fpcalc():
    import os, shutil, glob

    env = os.environ.get("GENRESPLITTER_FPCALC")
    if env and os.path.isfile(env):
        return env

    path = shutil.which("fpcalc")
    if path:
        return path

    local = os.environ.get("LOCALAPPDATA", "")
    winget_links = os.path.join(local, "Microsoft", "WinGet", "Links", "fpcalc.exe")
    if os.path.isfile(winget_links):
        return winget_links

    pattern = os.path.join(
        local, "Microsoft", "WinGet", "Packages", "**", "chromaprint-fpcalc-*", "fpcalc.exe"
    )
    matches = glob.glob(pattern, recursive=True)
    if matches:
        return matches[0]

    return None

import re
import shutil
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import Optional

from .storage import DATA_DIR

FPCALC_DIR = os.path.join(DATA_DIR, "bin")


def fpcalc_exe_name() -> str:
    return "fpcalc.exe" if os.name == "nt" else "fpcalc"


def fpcalc_path() -> str:
    return os.path.join(FPCALC_DIR, fpcalc_exe_name())


def fpcalc_available() -> bool:
    # Prefer bundled copy in AppData, then PATH.
    return os.path.exists(fpcalc_path()) or (shutil.which(fpcalc_exe_name()) is not None)


def prepend_to_path(path: str) -> None:
    cur = os.environ.get("PATH", "")
    parts = cur.split(os.pathsep) if cur else []
    if path and path not in parts:
        os.environ["PATH"] = path + os.pathsep + cur


def _download_text(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "GenreSplitter/2.x"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _download_file(url: str, dest: str, timeout: int = 30) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "GenreSplitter/2.x"})
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)


def _resolve_latest_windows_zip_url() -> Optional[str]:
    """Resolve the latest Chromaprint fpcalc Windows x86_64 zip from the official download page."""
    try:
        html = _download_text("https://acoustid.org/chromaprint", timeout=15)
    except Exception:
        return None

    m = re.search(r'href="([^"]*windows-x86_64\.zip)"', html, flags=re.IGNORECASE)
    if not m:
        return None

    href = m.group(1)
    if href.startswith("http"):
        return href
    return "https://acoustid.org" + href if href.startswith("/") else "https://acoustid.org/" + href


@dataclass
class EnsureResult:
    ok: bool
    installed_path: Optional[str] = None
    message: str = ""


def ensure_fpcalc(download_if_missing: bool = True) -> EnsureResult:
    """Ensure fpcalc is available (Windows can auto-download)."""
    os.makedirs(FPCALC_DIR, exist_ok=True)

    if os.path.exists(fpcalc_path()):
        prepend_to_path(FPCALC_DIR)
        return EnsureResult(True, fpcalc_path(), "fpcalc found in AppData bin")

    found = shutil.which(fpcalc_exe_name())
    if found:
        return EnsureResult(True, found, "fpcalc found in PATH")

    if not download_if_missing:
        return EnsureResult(False, None, "fpcalc not found")

    if os.name != "nt":
        return EnsureResult(
            False,
            None,
            "fpcalc not found. Install Chromaprint (fpcalc) via your package manager (brew/apt/pacman).",
        )

    url = _resolve_latest_windows_zip_url()
    if not url:
        return EnsureResult(
            False,
            None,
            "fpcalc not found and could not resolve a download URL. Visit https://acoustid.org/chromaprint to download fpcalc.",
        )

    tmpdir = tempfile.mkdtemp(prefix="genresplitter_fpcalc_")
    zip_path = os.path.join(tmpdir, "chromaprint-fpcalc.zip")
    try:
        _download_file(url, zip_path, timeout=45)
        with zipfile.ZipFile(zip_path) as zf:
            member = None
            for n in zf.namelist():
                if n.lower().endswith("fpcalc.exe"):
                    member = n
                    break
            if not member:
                return EnsureResult(False, None, "Downloaded archive did not contain fpcalc.exe")

            with zf.open(member) as src, open(fpcalc_path(), "wb") as dst:
                shutil.copyfileobj(src, dst)

        prepend_to_path(FPCALC_DIR)
        return EnsureResult(True, fpcalc_path(), f"fpcalc installed to {fpcalc_path()}")
    except Exception as e:
        return EnsureResult(False, None, f"Failed to download/install fpcalc: {e}")
    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass