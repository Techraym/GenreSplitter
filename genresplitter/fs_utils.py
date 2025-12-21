import os
import re
import io

from typing import Optional, Dict, Any

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    Image = None  # type: ignore

from mutagen.id3 import (
    ID3,
    ID3NoHeaderError,
    TIT2,
    TPE1,
    TPE2,
    TALB,
    TCON,
    TDRC,
    TDRL,
    TRCK,
    TPOS,
    APIC,
)

from .genres import normalize_genre


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def sanitize_path_component(name: str) -> str:
    """Windows-safe path component sanitizer."""
    if not name:
        return "Unknown"
    name = re.sub(r"[\x00-\x1f]", "", name)
    forbidden = '<>:"/\\|?*'
    sanitized = "".join((c if c not in forbidden else "_") for c in name).strip()
    while sanitized.endswith("."):
        sanitized = sanitized[:-1]
    up = sanitized.upper()
    if up in ("CON", "PRN", "AUX", "NUL") or re.match(r"^(COM|LPT)[0-9]+$", up):
        sanitized = "_" + sanitized
    return sanitized or "Unknown"


def read_id3_genre(path: str) -> Optional[str]:
    """Read ID3 TCON and normalize it into the closed output set."""
    try:
        tags = ID3(path)
        if "TCON" in tags:
            val = str(tags["TCON"])
            if val:
                return normalize_genre(val)
    except ID3NoHeaderError:
        return None
    except Exception:
        return None
    return None


def _guess_mime(image_bytes: bytes) -> str:
    """Best-effort mime type inference for common cover art formats.

    Python 3.13 removed the stdlib `imghdr` module, so we use Pillow when
    available, and a conservative header-based fallback otherwise.
    """
    # Prefer Pillow (robust, supports more formats)
    if Image is not None:
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                fmt = (img.format or "").upper()
            mapping = {
                "JPEG": "image/jpeg",
                "JPG": "image/jpeg",
                "PNG": "image/png",
                "GIF": "image/gif",
                "WEBP": "image/webp",
            }
            if fmt in mapping:
                return mapping[fmt]
        except Exception:
            pass

    # Header-based fallback (no external deps)
    b = image_bytes[:16]
    # JPEG
    if len(b) >= 3 and b[0:3] == b"\xFF\xD8\xFF":
        return "image/jpeg"
    # PNG
    if len(b) >= 8 and b[0:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    # GIF
    if len(b) >= 6 and (b[0:6] == b"GIF87a" or b[0:6] == b"GIF89a"):
        return "image/gif"
    # WEBP: RIFF....WEBP
    if len(b) >= 12 and b[0:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "image/webp"

    # Fallback: many clients assume jpeg
    return "image/jpeg"


def _prepare_cover_bytes(image_bytes: bytes) -> tuple[bytes, str]:
    """Normalize cover art bytes to a player-friendly format.

    - Keeps JPEG/PNG as-is.
    - Converts WEBP/GIF/unknown to JPEG or PNG (if transparency) when Pillow is available.
    - Falls back to the original bytes + best-effort mime detection.

    Returns (bytes, mime).
    """
    if not image_bytes:
        return b"", "image/jpeg"

    mime = _guess_mime(image_bytes)
    if mime in ("image/jpeg", "image/png"):
        return image_bytes, mime

    # If Pillow is available, convert to a widely supported format.
    if Image is not None:
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Decide output format based on transparency.
                has_alpha = (img.mode in ("RGBA", "LA")) or (
                    img.mode == "P" and "transparency" in (img.info or {})
                )
                if has_alpha:
                    out = io.BytesIO()
                    img = img.convert("RGBA")
                    img.save(out, format="PNG", optimize=True)
                    return out.getvalue(), "image/png"
                else:
                    out = io.BytesIO()
                    img = img.convert("RGB")
                    img.save(out, format="JPEG", quality=92, optimize=True)
                    return out.getvalue(), "image/jpeg"
        except Exception:
            pass

    # Fallback: return as-is with best-effort mime.
    return image_bytes, mime


def write_id3_tags_mp3(path: str, fields: Dict[str, Any]) -> None:
    """Write/update ID3v2.4 tags for an MP3 file.

    The caller passes a dict with (optional) keys:
      - title, artist, album, album_artist
      - genre (already normalized if desired)
      - track_number, disc_number
      - recording_date (e.g., YYYY-MM-DD)
      - release_date (e.g., YYYY-MM-DD)
      - cover_bytes (bytes)

    All frames are written as ID3v2.4 on save.
    """
    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        tags = ID3()

    enc = 3  # UTF-8

    def _set_text(frame_id: str, frame_obj) -> None:
        tags.delall(frame_id)
        tags.add(frame_obj)

    title = (fields.get("title") or "").strip()
    if title:
        _set_text("TIT2", TIT2(encoding=enc, text=title))

    artist = (fields.get("artist") or "").strip()
    if artist:
        _set_text("TPE1", TPE1(encoding=enc, text=artist))

    album = (fields.get("album") or "").strip()
    if album:
        _set_text("TALB", TALB(encoding=enc, text=album))

    album_artist = (fields.get("album_artist") or "").strip()
    if album_artist:
        _set_text("TPE2", TPE2(encoding=enc, text=album_artist))

    genre = (fields.get("genre") or "").strip()
    if genre:
        _set_text("TCON", TCON(encoding=enc, text=genre))

    trk = fields.get("track_number")
    if trk is not None and str(trk).strip():
        _set_text("TRCK", TRCK(encoding=enc, text=str(trk).strip()))

    disc = fields.get("disc_number")
    if disc is not None and str(disc).strip():
        _set_text("TPOS", TPOS(encoding=enc, text=str(disc).strip()))

    # Dates: prefer ID3v2.4 date frames
    rec_date = (fields.get("recording_date") or "").strip()
    if rec_date:
        _set_text("TDRC", TDRC(encoding=enc, text=rec_date))

    rel_date = (fields.get("release_date") or "").strip()
    if rel_date:
        _set_text("TDRL", TDRL(encoding=enc, text=rel_date))
        # Pragmatic compatibility: many players key off TDRC
        if not rec_date:
            _set_text("TDRC", TDRC(encoding=enc, text=rel_date))

    cover_bytes = fields.get("cover_bytes")
    if isinstance(cover_bytes, (bytes, bytearray)) and len(cover_bytes) > 0:
        cov_bytes, cov_mime = _prepare_cover_bytes(bytes(cover_bytes))
        tags.delall("APIC")
        tags.add(
            APIC(
                encoding=enc,
                mime=cov_mime,
                type=3,  # front cover
                desc="Cover",
                data=cov_bytes,
            )
        )

    # Force v2.4 on save
    tags.save(path, v2_version=4)





# --- Multi-format tagging (MP3/ID3, FLAC/Vorbis, MP4/M4A, WAV/AIFF, OGG/OPUS) -----------------

import base64
from mutagen import File as MutagenFile
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus
from mutagen.aiff import AIFF
from mutagen.wave import WAVE


SUPPORTED_AUDIO_EXTS = {
    ".mp3",
    ".flac",
    ".m4a",
    ".mp4",
    ".wav",
    ".aiff",
    ".aif",
    ".ogg",
    ".opus",
}


def is_supported_audio_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in SUPPORTED_AUDIO_EXTS


def _norm_str(x: Any) -> str:
    return str(x).strip() if x is not None else ""


def _split_year(date_str: str) -> str:
    # Accept YYYY or YYYY-MM-DD; return YYYY when possible.
    m = re.match(r"^(\d{4})", (date_str or "").strip())
    return m.group(1) if m else (date_str or "").strip()


def read_audio_genre(path: str) -> Optional[str]:
    """Best-effort genre reader for supported formats."""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in (".mp3", ".wav", ".aiff", ".aif"):
            return read_id3_genre(path)

        mf = MutagenFile(path, easy=True)
        if not mf or not getattr(mf, "tags", None):
            return None

        tags = mf.tags
        # Easy tag keys across formats tend to include 'genre'
        g = None
        if isinstance(tags, dict):
            v = tags.get("genre")
            if isinstance(v, list) and v:
                g = v[0]
            elif isinstance(v, str):
                g = v
        return normalize_genre(g) if g else None
    except Exception:
        return None


def write_audio_tags(path: str, fields: Dict[str, Any], *, overwrite: bool = True, fill_only_missing: bool = False) -> Dict[str, Any]:
    """Write metadata to common audio formats.

    Supported: MP3(ID3v2.4), FLAC(Vorbis), M4A/MP4(MP4 atoms), WAV/AIFF(ID3), OGG/OPUS(Vorbis comments).
    Returns a dict with keys: ok(bool), written(list[str]), warnings(list[str]).
    """
    ext = os.path.splitext(path)[1].lower()
    written = []
    warnings = []

    # Normalize some inputs
    title = _norm_str(fields.get("title"))
    artist = _norm_str(fields.get("artist"))
    album = _norm_str(fields.get("album"))
    album_artist = _norm_str(fields.get("album_artist"))
    genre = _norm_str(fields.get("genre"))
    track_number = _norm_str(fields.get("track_number"))
    disc_number = _norm_str(fields.get("disc_number"))
    recording_date = _norm_str(fields.get("recording_date"))
    release_date = _norm_str(fields.get("release_date"))
    cover_bytes = fields.get("cover_bytes")
    if not isinstance(cover_bytes, (bytes, bytearray)):
        cover_bytes = None
    if cover_bytes:
        # Convert WEBP/GIF/etc to a widely supported format (JPEG/PNG) where possible.
        cover_bytes, _ = _prepare_cover_bytes(bytes(cover_bytes))

    def _maybe_set(cur_val: Any, new_val: Any) -> bool:
        if not new_val:
            return False
        if fill_only_missing and cur_val:
            return False
        return overwrite or (not cur_val)

    # --- ID3-backed containers (MP3/WAV/AIFF)
    if ext in (".mp3", ".wav", ".aiff", ".aif"):
        # We reuse the ID3 writer for all ID3-capable containers. Mutagen will embed ID3 in WAV/AIFF if possible.
        write_id3_tags_mp3(path, {
            "title": title,
            "artist": artist,
            "album": album,
            "album_artist": album_artist,
            "genre": genre,
            "track_number": track_number,
            "disc_number": disc_number,
            "recording_date": recording_date,
            "release_date": release_date,
            "cover_bytes": cover_bytes,
        })
        for k in ("title", "artist", "album", "album_artist", "genre", "track_number", "disc_number", "recording_date", "release_date"):
            if _norm_str(fields.get(k)):
                written.append(k)
        if cover_bytes:
            written.append("cover")
        return {"ok": True, "written": written, "warnings": warnings}

    # --- FLAC (Vorbis comments + pictures)
    if ext == ".flac":
        audio = FLAC(path)
        # Vorbis comment keys
        def set_v(key: str, val: str):
            if not val:
                return
            cur = audio.tags.get(key) if audio.tags else None
            cur0 = cur[0] if isinstance(cur, list) and cur else (cur or "")
            if _maybe_set(cur0, val):
                audio[key] = [val]
                written.append(key)

        set_v("title", title)
        set_v("artist", artist)
        set_v("album", album)
        set_v("albumartist", album_artist)
        set_v("genre", genre)
        set_v("tracknumber", track_number)
        set_v("discnumber", disc_number)

        # Prefer 'date' (commonly used). Keep 'originaldate' if recording_date provided separately.
        if release_date:
            set_v("date", release_date)
        if recording_date and recording_date != release_date:
            set_v("originaldate", recording_date)

        if cover_bytes:
            try:
                pic = Picture()
                pic.data = bytes(cover_bytes)
                pic.type = 3  # front cover
                pic.mime = _guess_mime(bytes(cover_bytes))
                pic.desc = "Cover"
                audio.clear_pictures()
                audio.add_picture(pic)
                written.append("cover")
            except Exception as e:
                warnings.append(f"FLAC cover art failed: {e}")

        audio.save()
        return {"ok": True, "written": written, "warnings": warnings}

    # --- MP4/M4A (atoms)
    if ext in (".m4a", ".mp4"):
        audio = MP4(path)
        tags = audio.tags
        if tags is None:
            audio.add_tags()
            tags = audio.tags

        def set_atom(key: str, val: Any):
            if val is None or val == "" or val == []:
                return
            cur = tags.get(key)
            cur0 = cur[0] if isinstance(cur, list) and cur else (cur or "")
            if _maybe_set(cur0, val):
                tags[key] = [val] if not isinstance(val, list) else val
                written.append(key)

        set_atom("\xa9nam", title)
        set_atom("\xa9ART", artist)
        set_atom("aART", album_artist)
        set_atom("\xa9alb", album)
        set_atom("\xa9gen", genre)

        if release_date:
            # MP4 uses ©day as free text (often YYYY or YYYY-MM-DD)
            set_atom("\xa9day", release_date)

        # Track/disc are tuples: [(track, total)]
        if track_number:
            try:
                trk_int = int(re.findall(r"\d+", track_number)[0])
                cur = tags.get("trkn")
                total = cur[0][1] if cur and isinstance(cur, list) and cur and isinstance(cur[0], tuple) else 0
                if _maybe_set(cur, trk_int):
                    tags["trkn"] = [(trk_int, total)]
                    written.append("trkn")
            except Exception:
                warnings.append(f"MP4 track number parse failed: {track_number}")

        if disc_number:
            try:
                d_int = int(re.findall(r"\d+", disc_number)[0])
                cur = tags.get("disk")
                total = cur[0][1] if cur and isinstance(cur, list) and cur and isinstance(cur[0], tuple) else 0
                if _maybe_set(cur, d_int):
                    tags["disk"] = [(d_int, total)]
                    written.append("disk")
            except Exception:
                warnings.append(f"MP4 disc number parse failed: {disc_number}")

        if cover_bytes:
            try:
                mime = _guess_mime(bytes(cover_bytes))
                fmt = MP4Cover.FORMAT_JPEG if mime == "image/jpeg" else MP4Cover.FORMAT_PNG
                tags["covr"] = [MP4Cover(bytes(cover_bytes), imageformat=fmt)]
                written.append("covr")
            except Exception as e:
                warnings.append(f"MP4 cover art failed: {e}")

        audio.save()
        return {"ok": True, "written": written, "warnings": warnings}

    # --- OGG/OPUS (Vorbis comments; optional cover in METADATA_BLOCK_PICTURE)
    if ext in (".ogg", ".opus"):
        audio = OggOpus(path) if ext == ".opus" else OggVorbis(path)

        def set_vc(key: str, val: str):
            if not val:
                return
            cur = audio.tags.get(key) if audio.tags else None
            cur0 = cur[0] if isinstance(cur, list) and cur else (cur or "")
            if _maybe_set(cur0, val):
                audio[key] = [val]
                written.append(key)

        set_vc("title", title)
        set_vc("artist", artist)
        set_vc("album", album)
        set_vc("albumartist", album_artist)
        set_vc("genre", genre)
        set_vc("tracknumber", track_number)
        set_vc("discnumber", disc_number)

        if release_date:
            set_vc("date", release_date)
        if recording_date and recording_date != release_date:
            set_vc("originaldate", recording_date)

        if cover_bytes:
            try:
                pic = Picture()
                pic.data = bytes(cover_bytes)
                pic.type = 3
                pic.mime = _guess_mime(bytes(cover_bytes))
                pic.desc = "Cover"
                b64 = base64.b64encode(pic.write()).decode("ascii")
                # Recommended tag key for Vorbis-based containers
                audio["METADATA_BLOCK_PICTURE"] = [b64]
                written.append("METADATA_BLOCK_PICTURE")
            except Exception as e:
                warnings.append(f"OGG/OPUS cover art failed: {e}")

        audio.save()
        return {"ok": True, "written": written, "warnings": warnings}

    return {"ok": False, "written": [], "warnings": [f"Unsupported extension: {ext}"]}

