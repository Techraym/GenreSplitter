"""Headless batch runner for GenreSplitter.

Designed for servers and large unattended collections without Qt/UI startup.
Settings are loaded from the normal per-user GenreSplitter settings file unless
--settings points at an explicit JSON file.

Examples:
  python batch_sort.py --source /srv/music/in --target /srv/music/out --dry-run
  python batch_sort.py --source /srv/music/in --target /srv/music/out --settings /etc/genresplitter/settings.json
"""
from __future__ import annotations

import argparse
import faulthandler
import json
import os
import shutil
from dataclasses import fields
from typing import Any

from genresplitter.api_resolver import ApiConfig
from genresplitter.process_resolver import ProcessGenreResolver
from genresplitter.genres import parse_artist_title, normalize_genre, guess_genre_from_keywords
from genresplitter.fs_utils import (
    SUPPORTED_AUDIO_EXTS,
    ensure_dir,
    read_audio_genre,
    sanitize_path_component,
    write_audio_tags,
)
from genresplitter.storage import load_settings


def _load_settings(path: str | None) -> dict[str, Any]:
    if not path:
        return load_settings()
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("settings JSON must contain an object")
    return data


def build_api_config(settings: dict[str, Any]) -> ApiConfig:
    """Translate persisted UI settings into the ApiConfig used by resolvers."""
    values: dict[str, Any] = {
        "lastfm_key": settings.get("lastfm_api_key", ""),
        "spotify_client_id": settings.get("spotify_client_id", ""),
        "spotify_client_secret": settings.get("spotify_client_secret", ""),
        "discogs_token": settings.get("discogs_token", ""),
        "theaudiodb_api_key": settings.get("theaudiodb_api_key", ""),
        "rateyourmusic_cookie": settings.get("rateyourmusic_cookie", ""),
        "acoustid_api_key": settings.get("acoustid_api_key", ""),
        "fetch_cover_art": bool(settings.get("fetch_cover_art", False)),
        "enable_lastfm": bool(settings.get("enable_lastfm", True)),
        "enable_discogs": bool(settings.get("enable_discogs", True)),
        "enable_spotify": bool(settings.get("enable_spotify", False)),
        "enable_musicbrainz": bool(settings.get("enable_musicbrainz", True)),
        "enable_acousticbrainz": bool(settings.get("enable_acousticbrainz", False)),
        "enable_theaudiodb": bool(settings.get("enable_theaudiodb", False)),
        "enable_itunes": bool(settings.get("enable_itunes", True)),
        "enable_rateyourmusic": bool(settings.get("enable_rateyourmusic", False)),
        "enable_acoustid": bool(settings.get("enable_acoustid", False)),
        "timeout_seconds": int(settings.get("api_timeout_seconds", 25)),
        "retries": int(settings.get("api_retries", 3)),
        "backoff_seconds": float(settings.get("api_backoff_seconds", 1.0)),
        "min_pause_seconds": float(settings.get("api_min_pause_seconds", 0.3)),
        "acoustid_min_score": float(settings.get("acoustid_min_score", 0.6)),
        "acousticbrainz_threshold": float(settings.get("acousticbrainz_threshold", 0.6)),
    }
    # Keep this resilient if ApiConfig gains/removes optional fields later.
    allowed = {f.name for f in fields(ApiConfig)}
    return ApiConfig(**{k: v for k, v in values.items() if k in allowed})


def _audio_files(source: str) -> list[str]:
    result: list[str] = []
    for root, _dirs, names in os.walk(source):
        for name in names:
            path = os.path.join(root, name)
            if os.path.splitext(name)[1].lower() in SUPPORTED_AUDIO_EXTS and os.path.isfile(path):
                result.append(path)
    result.sort(key=str.casefold)
    return result


def _genre_for_file(
    resolver: ProcessGenreResolver,
    src: str,
    filename: str,
    use_id3_fallback: bool,
) -> str:
    parsed = parse_artist_title(filename)
    artist = parsed.get("artist", "")
    title = parsed.get("title", "")

    raw_genre = ""
    try:
        raw_genre = resolver.resolve_track(src, artist, title) or ""
    except Exception as exc:
        print(f"[resolver] {filename}: {exc}", flush=True)

    genre = normalize_genre(raw_genre) if raw_genre else ""
    if not genre and use_id3_fallback:
        existing = read_audio_genre(src)
        if existing:
            genre = normalize_genre(existing)
    if not genre:
        genre = guess_genre_from_keywords(artist, title) or "Unknown"

    # 'Other' is not a destination category in the current sorting rules.
    if str(genre).strip().casefold() == "other":
        genre = "Unknown"
    return genre or "Unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description="GenreSplitter headless batch sorter")
    ap.add_argument("--source", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--settings", help="Explicit settings JSON; defaults to the normal per-user settings")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--copy", action="store_true", help="Copy instead of move; existing destination leaves source intact")
    ap.add_argument("--api-timeout", type=int, default=None, help="Per-file API subprocess timeout in seconds")
    ap.add_argument("--use-id3-fallback", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--write-id3", action="store_true", default=False)
    ap.add_argument("--hang-seconds", type=int, default=120)
    args = ap.parse_args()

    source = os.path.abspath(args.source)
    target = os.path.abspath(args.target)
    if not os.path.isdir(source):
        ap.error(f"source is not a directory: {source}")
    ensure_dir(target)

    settings = _load_settings(args.settings)
    cfg = build_api_config(settings)
    process_timeout = args.api_timeout
    if process_timeout is None:
        process_timeout = int(settings.get("api_process_timeout_sec", 45))
    resolver = ProcessGenreResolver(cfg, log_fn=lambda s: print(s, flush=True), timeout_sec=process_timeout)

    files = _audio_files(source)
    total = len(files)
    state_dir = os.path.join(target, ".genresplitter")
    ensure_dir(state_dir)
    hang_log = os.path.join(state_dir, "hang.log")

    moved = copied = existing = failed = 0
    with open(hang_log, "a", encoding="utf-8", errors="replace") as f:
        faulthandler.enable(file=f, all_threads=True)

    for idx, src in enumerate(files, start=1):
        filename = os.path.basename(src)
        with open(hang_log, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"\nFILE {idx}/{total}: {src}\n")
            f.flush()
            faulthandler.dump_traceback_later(max(5, args.hang_seconds), repeat=False, file=f)

        try:
            genre = _genre_for_file(resolver, src, filename, args.use_id3_fallback)
            dest_dir = os.path.join(target, sanitize_path_component(genre))
            dst = os.path.join(dest_dir, filename)

            if os.path.exists(dst):
                existing += 1
                action = "would keep source" if args.copy or args.dry_run else "remove source"
                print(f"[{idx}/{total}] EXISTS {filename} -> {genre} ({action})", flush=True)
                if not args.dry_run and not args.copy and os.path.abspath(src) != os.path.abspath(dst):
                    os.remove(src)
                continue

            print(f"[{idx}/{total}] {filename} -> {genre}", flush=True)
            if args.dry_run:
                continue

            ensure_dir(dest_dir)
            if args.write_id3:
                tag_result = write_audio_tags(src, {"genre": genre})
                if not tag_result.get("ok", False):
                    raise RuntimeError(f"tag update failed: {tag_result}")

            if args.copy:
                shutil.copy2(src, dst)
                copied += 1
            else:
                shutil.move(src, dst)
                moved += 1
        except Exception as exc:
            failed += 1
            print(f"[{idx}/{total}] ERROR {filename}: {exc}", flush=True)
        finally:
            try:
                faulthandler.cancel_dump_traceback_later()
            except Exception:
                pass

    resolver.save_cache()
    print(
        f"DONE total={total} moved={moved} copied={copied} existing={existing} failed={failed} dry_run={args.dry_run}",
        flush=True,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
