import json
import os
from typing import Any, Dict, Optional

APP_NAME = "GenreSplitter"


def _user_data_dir() -> str:
    """
    Returns a writable per-user data directory.
    Windows: %APPDATA%\\GenreSplitter
    Other:   ~/.config/GenreSplitter
    """
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, APP_NAME)

    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    return os.path.join(base, APP_NAME)


DATA_DIR = _user_data_dir()
os.makedirs(DATA_DIR, exist_ok=True)

SETTINGS_PATH = os.path.join(DATA_DIR, "genresplitter_settings.json")
CACHE_PATH = os.path.join(DATA_DIR, "genresplitter_cache.json")
LOG_PATH = os.path.join(DATA_DIR, "genresplitter.log")


def safe_load_json(path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if default is None:
        default = {}
    if not os.path.exists(path):
        return dict(default)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else dict(default)
    except Exception:
        return dict(default)


def safe_write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass


def load_settings() -> Dict[str, Any]:
    return safe_load_json(SETTINGS_PATH, {})


def save_settings(data: Dict[str, Any]) -> None:
    if isinstance(data, dict):
        safe_write_json(SETTINGS_PATH, data)


def load_cache() -> Dict[str, Any]:
    return safe_load_json(CACHE_PATH, {})


def save_cache(data: Dict[str, Any]) -> None:
    if isinstance(data, dict):
        safe_write_json(CACHE_PATH, data)
