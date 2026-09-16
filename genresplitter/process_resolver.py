import base64
import json
import os
import subprocess
import sys
from dataclasses import asdict
from typing import Any, Dict, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
API_WORKER_SCRIPT = os.path.join(_HERE, "api_subprocess_worker.py")
project_root = os.path.dirname(_HERE)


def _json_desanitize(obj):
    if isinstance(obj, dict) and set(obj.keys()) == {"__bytes_b64__"}:
        try:
            return base64.b64decode(obj["__bytes_b64__"])
        except Exception:
            return b""
    if isinstance(obj, dict):
        return {k: _json_desanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_desanitize(v) for v in obj]
    return obj


from .api_resolver import ApiConfig
from .meta import APP_NAME


class ProcessGenreResolver:
    """Resolve genres/metadata in a killable subprocess per request."""

    def __init__(self, cfg: ApiConfig, log_fn, timeout_sec: int = 45):
        self.cfg = cfg
        self.log = log_fn
        self.timeout_sec = max(5, int(timeout_sec))

    def _call(
        self,
        method: str,
        artist: str = "",
        title: str = "",
        file_path: str = "",
        timeout_sec: Optional[int] = None,
    ) -> Any:
        cfg_json = json.dumps(asdict(self.cfg), ensure_ascii=False)
        cmd = [
            sys.executable,
            API_WORKER_SCRIPT,
            "--method",
            method,
            "--cfg",
            cfg_json,
            "--artist",
            artist or "",
            "--title",
            title or "",
            "--file_path",
            file_path or "",
        ]

        tsec = self.timeout_sec if timeout_sec is None else max(5, int(timeout_sec))
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")

        try:
            cp = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=tsec,
                check=False,
            )
        except subprocess.TimeoutExpired:
            self.log(f"[{APP_NAME}] TIMEOUT({tsec}s) in subprocess method={method} for {artist} - {title}")
            raise TimeoutError(f"subprocess timeout: {method} ({tsec}s)")

        stdout = (cp.stdout or "").strip()
        if not stdout:
            err = (cp.stderr or "").strip()
            raise RuntimeError(f"subprocess empty output (rc={cp.returncode}): {err[:500]}")

        try:
            payload: Dict[str, Any] = json.loads(stdout)
        except Exception:
            err = (cp.stderr or "").strip()
            raise RuntimeError(
                f"subprocess returned non-json output (rc={cp.returncode}): "
                f"{stdout[:500]} | stderr: {err[:300]}"
            )

        if not payload.get("ok", False):
            raise RuntimeError(payload.get("error", "unknown error"))
        return _json_desanitize(payload.get("result"))

    def resolve(self, artist: str, title: str) -> str:
        return self._call("resolve", artist=artist, title=title)

    def resolve_track(self, file_path: str, artist: str, title: str) -> str:
        return self._call("resolve_track", artist=artist, title=title, file_path=file_path)

    def resolve_track_metadata(self, file_path: str, artist: str, title: str) -> Dict[str, Any]:
        return self._call("resolve_track_metadata", artist=artist, title=title, file_path=file_path)

    def save_cache(self) -> None:
        """Compatibility no-op for callers shared with the in-process resolver.

        Each subprocess owns its resolver lifecycle and persists any cache changes
        before it exits; the parent process therefore has no in-memory cache to save.
        """
        return None
