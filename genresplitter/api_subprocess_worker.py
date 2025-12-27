import os
import base64  # HOTFIX v2.9.3.15
import argparse
import json
import sys
import traceback
from typing import Any, Dict

# HOTFIX v2.9.3.24 PACKAGE_FIX:
# When running this worker as a script (python api_subprocess_worker.py),
# relative imports break. Ensure the project root is on sys.path and force package context.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if __package__ in (None, ""):
    __package__ = "genresplitter"


# HOTFIX v2.9.3.23 sys.path: allow running as a script from any cwd
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PKG_ROOT = os.path.dirname(_THIS_DIR)
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)



# HOTFIX v2.9.3.15: recursively sanitize objects for JSON transport (bytes -> base64 marker dict)
def _json_sanitize(obj):
    if isinstance(obj, (bytes, bytearray)):
        return {"__bytes_b64__": base64.b64encode(bytes(obj)).decode("ascii")}
    if isinstance(obj, dict):
        return {str(k): _json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_sanitize(v) for v in obj]
    return obj

from genresplitter.api_resolver import ApiConfig, GenreResolver


def _cfg_from_json(s: str) -> ApiConfig:
    d = json.loads(s) if s else {}
    return ApiConfig(**d)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True, choices=["resolve", "resolve_track", "resolve_track_metadata"])
    ap.add_argument("--cfg", required=True, help="JSON encoded ApiConfig dict")
    ap.add_argument("--artist", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--file_path", default="")
    args = ap.parse_args()

    try:
        cfg = _cfg_from_json(args.cfg)

        # Subprocess must not touch UI; provide no-op logger.
        def _log(_msg: str) -> None:
            return

        resolver = GenreResolver(cfg, _log)

        if args.method == "resolve":
            out = resolver.resolve(args.artist, args.title)
        elif args.method == "resolve_track":
            out = resolver.resolve_track(args.file_path, args.artist, args.title)
        else:
            out = resolver.resolve_track_metadata(args.file_path, args.artist, args.title)

        payload: Dict[str, Any] = {"ok": True, "result": _json_sanitize(out)}
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        return 0

    except Exception as e:
        payload = {"ok": False, "error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()}
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
