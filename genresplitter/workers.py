import os
import shutil
import time
import json
import csv
import logging
import faulthandler
from contextlib import contextmanager
# v2.10.0: hang.log disabled by default
ENABLE_HANG_LOG = False


from PyQt6.QtCore import QThread, pyqtSignal

from .api_resolver import GenreResolver
from .genres import (
    parse_artist_title,
    normalize_genre,
    guess_genre_from_keywords,
    is_christmas_track,
    is_piratenmuziek,
    artist_bucket,
)
from .fs_utils import (
    ensure_dir,
    sanitize_path_component,
    read_audio_genre,
    write_audio_tags,
    SUPPORTED_AUDIO_EXTS,
)


@contextmanager
def _hang_guard(log_path: str, seconds: int, header: str):
    """Dump stack traces to log_path if this block hangs for too long."""
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
    except Exception:
        pass

    f = None
    try:
        f = open(log_path, "a", encoding="utf-8", errors="replace")
    except Exception:
        f = None

    t0 = time.time()  # HANG_GUARD_DURATION

    try:
        if f:
            f.write(f"\n=== HANG GUARD START ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===\n")
            f.write(header + "\n")
            f.flush()
            faulthandler.enable(file=f, all_threads=True)
            faulthandler.dump_traceback_later(seconds, repeat=False, file=f)
        yield
    finally:
        try:
            faulthandler.cancel_dump_traceback_later()
        except Exception:
            pass
        if f:
            dur = time.time() - t0
            f.write(f"=== HANG GUARD END ({time.strftime('%Y-%m-%d %H:%M:%S')}) | duration={dur:.2f}s ===\n")
            f.flush()
            f.close()


class SortWorker(QThread):
    progress = pyqtSignal(int, int)
    message = pyqtSignal(str)
    finished_ok = pyqtSignal()
    finished_err = pyqtSignal(str)

    def __init__(self, source_dir: str, target_dir: str, resolver: GenreResolver, use_id3_fallback: bool, dry_run: bool, write_id3_metadata: bool = True, write_run_report: bool = True, metadata_update_policy: str = "always", confidence_threshold: int = 85):
        super().__init__()
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.resolver = resolver
        self.use_id3_fallback = use_id3_fallback
        self.dry_run = dry_run
        self.write_id3_metadata = write_id3_metadata
        # Always initialize to avoid stop/cleanup crashes when this flag is referenced.
        self.write_run_report = write_run_report
        self.metadata_update_policy = (metadata_update_policy or "always").strip().lower()
        self.confidence_threshold = int(confidence_threshold) if confidence_threshold is not None else 85
        self._stop = False

    def run(self):
        try:
            files = [f for f in os.listdir(self.source_dir)
                     if os.path.splitext(f)[1].lower() in SUPPORTED_AUDIO_EXTS and os.path.isfile(os.path.join(self.source_dir, f))]
            total = len(files)
            done = 0
            report_rows = []
            report_started = time.strftime('%Y-%m-%d_%H%M%S')
            report_flushed = False  # REPORT_ALWAYS_FLUSH

            def _flush_report():
                """Write CSV+JSON report for this run (best-effort)."""
                nonlocal report_flushed
                if report_flushed:
                    return
                report_flushed = True
                if not getattr(self, 'write_run_report', False):
                    return
                try:
                    reports_dir = os.path.join(self.target_dir, '_GenreSplitter_Reports')
                    ensure_dir(reports_dir)
                    base_name = f'genresplitter_report_{report_started}'
                    csv_path = os.path.join(reports_dir, base_name + '.csv')
                    json_path = os.path.join(reports_dir, base_name + '.json')
                    if report_rows:
                        fieldnames = sorted({k for r in report_rows for k in r.keys()})
                        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                            wcsv = csv.DictWriter(f, fieldnames=fieldnames)
                            wcsv.writeheader()
                            for r in report_rows:
                                rr = dict(r)
                                for lk in ('tag_written', 'tag_warnings', 'errors'):
                                    if isinstance(rr.get(lk), list):
                                        rr[lk] = ';'.join(str(x) for x in rr[lk])
                                wcsv.writerow(rr)
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(report_rows, f, ensure_ascii=False, indent=2)
                        self.message.emit(f'Report saved: {csv_path}')
                    else:
                        self.message.emit('Report: geen bestanden verwerkt.')
                except Exception as e:
                    self.message.emit(f'Report failed: {e}')

            hang_log = os.path.join(self.target_dir, '.genresplitter', 'hang.log')
            hang_seconds = 120  # dump stack if a single file stage blocks too long

            for fn in files:
                if self._stop:
                    break

                parsed = parse_artist_title(fn)
                if not parsed:
                    self.message.emit(f"Skip (naam klopt niet): {fn}")
                    done += 1
                    self.progress.emit(done, total)
                    continue

                artist, title = parsed

                file_path = os.path.join(self.source_dir, fn)
                self.message.emit(f"Resolving: {fn}")

                row = {
                    "filename": fn,
                    "src_path": file_path,
                    "ext": os.path.splitext(fn)[1].lower(),
                    "parsed_artist": artist,
                    "parsed_title": title,
                    "resolved_genre_raw": None,
                    "final_genre": None,
                    "dst_path": None,
                    "tag_write_ok": None,
                    "tag_written": [],
                    "tag_warnings": [],
                    "errors": [],
                }
                with _hang_guard(hang_log, hang_seconds, f"FILE: {fn} | STAGE: resolve"):
                    try:
                        raw_genre = self.resolver.resolve_track(file_path, artist, title) if hasattr(self.resolver, 'resolve_track') else self.resolver.resolve(artist, title)
                    except Exception as e:
                        row["errors"].append(f"resolve:{e}")
                        self.message.emit(f"Resolve failed: {fn} ({e})")
                        # Fallback: use ID3 genre or keyword guess so the run can continue
                        raw_genre = read_audio_genre(file_path) if self.use_id3_fallback else ""
                        if not raw_genre:
                            raw_genre = guess_genre_from_keywords(artist, title) or ""
                row["resolved_genre_raw"] = raw_genre
                genre = normalize_genre(raw_genre)

                # Piratenmuziek override: treat as a dedicated genre when the track matches
                # typical NL "geheime zender" / pirate radio programming.
                if is_piratenmuziek(artist, title, raw_genre=raw_genre, threshold=6):
                    if genre != "Piratenmuziek":
                        self.message.emit(f"Piratenmuziek override: {fn} -> Piratenmuziek (was: {genre})")
                    genre = "Piratenmuziek"

                if genre == "Unknown":
                    guessed = guess_genre_from_keywords(artist, title)
                    if guessed:
                        self.message.emit(f"Guessed genre: {fn} -> {guessed} (keywords)")
                        genre = guessed

                if genre == "Unknown" and self.use_id3_fallback:
                    g0 = read_audio_genre(os.path.join(self.source_dir, fn))
                    if g0:
                        genre = g0
                        self.message.emit(f"Tag fallback genre: {fn} -> {genre}")

                if is_christmas_track(artist, title, genre):
                    if genre != "Christmas":
                        self.message.emit(f"Christmas override: {fn} -> Christmas (was: {genre})")
                    genre = "Christmas"

                row["final_genre"] = genre

                # --- Optional: enrich and write metadata to tags (format-aware)
                if self.write_id3_metadata:
                    try:
                        meta = self.resolver.resolve_track_metadata(file_path, artist, title)
                        # Ensure the genre we actually decided on is written
                        if genre and genre != "Unknown":
                            meta["genre"] = genre
                        # Prefer the filename-derived artist/title if resolver didn't improve them
                        meta.setdefault("artist", artist)
                        meta.setdefault("title", title)

                        if self.dry_run:
                            # Keep log short but actionable
                            parts = []
                            for k in ("artist", "title", "album", "release_date", "genre"):
                                v = meta.get(k)
                                if v:
                                    parts.append(f"{k}={v}")
                            self.message.emit(f"[DRY] Tag update: {fn} ({', '.join(parts)})")
                            row["tag_write_ok"] = True
                            row["tag_written"] = [k for k in ("artist","title","album","album_artist","genre","track_number","disc_number","recording_date","release_date") if meta.get(k)]
                            if meta.get("cover_bytes"):
                                row["tag_written"].append("cover")
                        else:
                            policy = (self.metadata_update_policy or "always").strip().lower()
                            conf = meta.get("confidence")
                            try:
                                conf_v = float(conf) if conf is not None else 0.0
                            except Exception:
                                conf_v = 0.0

                            if policy == "cover_only":
                                meta_to_write = {}
                                if meta.get("cover_bytes"):
                                    meta_to_write["cover_bytes"] = meta["cover_bytes"]
                                overwrite = True
                                fill_only_missing = False
                            elif policy == "confidence":
                                thr = int(self.confidence_threshold or 85)
                                overwrite = conf_v >= thr
                                fill_only_missing = not overwrite
                                meta_to_write = meta
                            else:
                                overwrite = True
                                fill_only_missing = False
                                meta_to_write = meta

                            res = write_audio_tags(file_path, meta_to_write, overwrite=overwrite, fill_only_missing=fill_only_missing)
                            row["tag_write_ok"] = bool(res.get("ok"))
                            row["tag_written"] = list(res.get("written") or [])
                            row["tag_warnings"] = list(res.get("warnings") or [])
                            if res.get('warnings'):
                                for w in res['warnings']:
                                    self.message.emit(f"Tag warning: {fn} ({w})")
                            self.message.emit(f"Tags updated: {fn}")
                    except Exception as e:
                        row["tag_write_ok"] = False
                        row["errors"].append(f"tag_update:{e}")
                        self.message.emit(f"Tag update failed: {fn} ({e})")

                if genre == "Unknown":
                    bucket = artist_bucket(artist)
                    artist_safe = sanitize_path_component(artist or "Unknown")
                    dest_dir = os.path.join(self.target_dir, "Unknown", sanitize_path_component(bucket), artist_safe)
                    self.message.emit(f"Unknown fallback: {fn} -> {os.path.relpath(dest_dir, self.target_dir)}")
                else:
                    bucket = artist_bucket(artist)
                    dest_dir = os.path.join(self.target_dir, sanitize_path_component(genre), sanitize_path_component(bucket))

                ensure_dir(dest_dir)

                src = os.path.join(self.source_dir, fn)

                base, ext = os.path.splitext(fn)
                base_safe = sanitize_path_component(base)
                filename_safe = base_safe + ext if base_safe != base else fn

                dst = os.path.join(dest_dir, filename_safe)

                if filename_safe != fn:
                    self.message.emit(f"Sanitized filename: {fn} -> {os.path.relpath(dst, self.target_dir)}")

                dst_final = dst
                if os.path.exists(dst_final):
                    base2, ext2 = os.path.splitext(filename_safe)
                    i = 2
                    while os.path.exists(os.path.join(dest_dir, f"{base2} ({i}){ext2}")):
                        i += 1
                    dst_final = os.path.join(dest_dir, f"{base2} ({i}){ext2}")

                row["dst_path"] = dst_final


                try:
                    if self.dry_run:
                        self.message.emit(f"[DRY] {fn} -> {os.path.relpath(dst_final, self.target_dir)}")
                        row["status"] = "dry_run"
                    else:
                        with _hang_guard(hang_log, hang_seconds, f"FILE: {fn} | STAGE: move"):
                            shutil.move(src, dst_final)
                        self.message.emit(f"Move: {fn} -> {os.path.relpath(dst_final, self.target_dir)}")
                        row["status"] = "moved"
                except Exception as e:
                    logging.exception("Move failed for %s", fn)
                    row["status"] = "failed"
                    row["errors"].append(f"move:{e}")
                    self.message.emit(f"Move failed: {fn} ({e})")
                report_rows.append(row)

                done += 1
                self.progress.emit(done, total)
            # --- Run report (CSV + JSON) ---
            _flush_report()
            if not getattr(self, 'write_run_report', False):
                self.message.emit("Report: uitgeschakeld.")

            # HOTFIX v2.9.3.15: resolver cache is optional; never crash the worker
            if hasattr(self.resolver, 'save_cache'):
                try:
                    self.resolver.save_cache()
                except Exception:
                    logging.exception('Failed to save resolver cache')

            self.finished_ok.emit()
        except Exception as e:
            logging.exception("SortWorker crashed")
            self.finished_err.emit(str(e))
        finally:
            # Ensure report is written even on crash/stop (best-effort)
            try:
                if '_flush_report' in locals():
                    _flush_report()
            except Exception:
                pass

    def stop(self):
        self._stop = True
