"""Batch (no-GUI) runner for GenreSplitter.

This is intended for stress testing large collections and collecting a hang dump
without any Qt UI involvement.

Example:
  python batch_sort.py --source "D:\\Music\\In" --target "D:\\Music\\Out" --dry-run
"""
import argparse, os, shutil, time, faulthandler
from genresplitter.process_resolver import ProcessGenreResolver
from genresplitter.genres import parse_artist_title, normalize_genre, guess_genre_from_keywords
from genresplitter.fs_utils import ensure_dir, sanitize_path_component, read_audio_genre, write_audio_tags, SUPPORTED_AUDIO_EXTS

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--api-timeout", type=int, default=45, help="Per-file API subprocess timeout (seconds)")
    ap.add_argument("--use-id3-fallback", action="store_true", default=True)
    ap.add_argument("--write-id3", action="store_true", default=False)
    ap.add_argument("--hang-seconds", type=int, default=120)
    args = ap.parse_args()

    resolver = ProcessGenreResolver(cfg, log_fn=lambda s: print(s, flush=True))

    files = [f for f in os.listdir(args.source)
             if os.path.splitext(f)[1].lower() in SUPPORTED_AUDIO_EXTS
             and os.path.isfile(os.path.join(args.source, f))]
    total = len(files)

    os.makedirs(os.path.join(args.target, '.genresplitter'), exist_ok=True)
    hang_log = os.path.join(args.target, '.genresplitter', 'hang.log')

    with open(hang_log, 'a', encoding='utf-8', errors='replace') as f:
        faulthandler.enable(file=f, all_threads=True)

    for idx, fn in enumerate(files, start=1):
        src = os.path.join(args.source, fn)

        with open(hang_log, 'a', encoding='utf-8', errors='replace') as f:
            f.write(f"\nFILE {idx}/{total}: {fn}\n")
            f.flush()
            faulthandler.dump_traceback_later(args.hang_seconds, repeat=False, file=f)

        try:
            parsed = parse_artist_title(fn)
            artist = parsed.get("artist", "")
            title = parsed.get("title", "")

            raw_genre, meta = resolver.resolve(artist, title)

            genre = normalize_genre(raw_genre) if raw_genre else ""
            if not genre and args.use_id3_fallback:
                g = read_audio_genre(src)
                if g:
                    genre = normalize_genre(g)
            if not genre:
                genre = guess_genre_from_keywords(artist, title) or "Unknown"

            dest_dir = os.path.join(args.target, sanitize_path_component(genre))
            ensure_dir(dest_dir)
            dst = os.path.join(dest_dir, fn)

            if args.write_id3:
                write_audio_tags(src, genre=genre)

            if not args.dry_run:
                shutil.move(src, dst)

            print(f"[{idx}/{total}] {fn} -> {genre}", flush=True)

        finally:
            try:
                faulthandler.cancel_dump_traceback_later()
            except Exception:
                pass

if __name__ == '__main__':
    main()
