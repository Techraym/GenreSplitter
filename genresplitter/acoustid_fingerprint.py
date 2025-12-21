from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .fpcalc_manager import ensure_fpcalc, fpcalc_available


@dataclass
class AcoustIdMatch:
    artist: str
    title: str
    score: float
    mbid: Optional[str] = None


def match_file(file_path: str, api_key: str, min_score: float = 0.6, allow_download_fpcalc: bool = True) -> Optional[AcoustIdMatch]:
    """Identify a track via AcoustID using Chromaprint fpcalc. Returns best match or None."""
    api_key = (api_key or "").strip()
    if not api_key:
        return None

    if not fpcalc_available():
        res = ensure_fpcalc(download_if_missing=allow_download_fpcalc)
        if not res.ok:
            return None

    try:
        import acoustid  # pyacoustid
    except Exception:
        return None

    try:
        score, mbid, title, artist = acoustid.match(api_key, file_path)
        if score is None:
            return None
        score = float(score)
        if score < float(min_score):
            return None
        return AcoustIdMatch(artist=str(artist or "").strip(), title=str(title or "").strip(), score=score, mbid=mbid)
    except Exception:
        return None
