import time
import base64
from dataclasses import dataclass
from typing import Optional, Dict, Any

import requests

from .meta import APP_NAME, APP_VERSION
from .storage import CACHE_PATH, safe_load_json, safe_write_json
from .genres import normalize_genre

@dataclass
class ApiConfig:
    lastfm_key: str
    spotify_client_id: str
    spotify_client_secret: str
    discogs_token: str
    theaudiodb_api_key: str = ""
    rateyourmusic_cookie: str = ""
    acoustid_api_key: str = ""

    enable_lastfm: bool = True
    enable_discogs: bool = True
    enable_spotify: bool = True
    enable_musicbrainz: bool = True
    enable_acousticbrainz: bool = False
    enable_theaudiodb: bool = False
    enable_itunes: bool = True
    enable_rateyourmusic: bool = False
    enable_acoustid: bool = False

    timeout_seconds: int = 25
    retries: int = 3
    backoff_seconds: float = 1.0
    min_pause_seconds: float = 0.15

    acoustid_min_score: float = 0.6
    acousticbrainz_threshold: float = 0.60

    user_agent: str = f"{APP_NAME}/{APP_VERSION} (portable)"

class GenreResolver:
    def __init__(self, cfg: ApiConfig, log_fn):
        self.cfg = cfg
        self.log = log_fn
        self.cache: Dict[str, str] = safe_load_json(CACHE_PATH)

        # Normalize existing cache values
        for k, v in list(self.cache.items()):
            self.cache[k] = normalize_genre(v)

        self.spotify_token: Optional[str] = None
        self.spotify_token_exp: float = 0.0

        # Per-run in-memory cache for richer metadata lookups (separate from the genre cache on disk)
        self._meta_cache: Dict[str, Dict[str, Any]] = {}

        self.http = requests.Session()
        self.http.headers.update({"User-Agent": self.cfg.user_agent})
        self._last_call_ts: float = 0.0

    def resolve(self, artist: str, title: str) -> str:
        return self._resolve_impl(artist, title)

    def resolve_track(self, file_path: str, artist: str, title: str) -> str:
        """Resolve genre for a file (optionally using AcoustID first), then resolve by metadata."""
        a = (artist or "").strip()
        t = (title or "").strip()
    
        # 1) Optional AcoustID fingerprinting to improve artist/title
        acoustid_enabled = bool(getattr(self.cfg, "enable_acoustid", False))
        acoustid_key = (getattr(self.cfg, "acoustid_api_key", "") or "").strip()
    
        if acoustid_enabled and acoustid_key:
            try:
                from .acoustid_fingerprint import match_file
    
                m = match_file(
                    file_path=file_path,
                    api_key=acoustid_key,
                    min_score=getattr(self.cfg, "acoustid_min_score", 0.6),
                    allow_download_fpcalc=True,
                )
                if m:
                    a = (m.artist or a).strip()
                    t = (m.title or t).strip()
            except Exception:
                # Fingerprinting is best-effort; fall back to original tags
                pass
    
        # 2) Temporary MusicBrainz fallback (do not persistently change user setting)
        user_enabled_musicbrainz = bool(getattr(self.cfg, "enable_musicbrainz", False))
        allow_temp_musicbrainz = (not user_enabled_musicbrainz) and acoustid_enabled and bool(acoustid_key)
    
        if allow_temp_musicbrainz:
            try:
                setattr(self.cfg, "enable_musicbrainz", True)
                return self.resolve(a, t)
            finally:
                setattr(self.cfg, "enable_musicbrainz", user_enabled_musicbrainz)
    
        return self.resolve(a, t)

    def resolve_track_metadata(self, file_path: str, artist: str, title: str) -> Dict[str, Any]:
        """Resolve best-effort track metadata for ID3 tagging.

        Returned dict keys are aligned with fs_utils.write_id3_tags_mp3():
          title, artist, album, album_artist, genre, track_number, disc_number,
          release_date, recording_date, cover_bytes

        Notes:
        - This is intentionally "best-effort"; missing fields are simply omitted.
        - We reuse AcoustID (if enabled) to improve artist/title, similar to resolve_track().
        """
        a = (artist or "").strip()
        t = (title or "").strip()

        acoustid_enabled = bool(getattr(self.cfg, "enable_acoustid", False))
        acoustid_key = (getattr(self.cfg, "acoustid_api_key", "") or "").strip()

        if acoustid_enabled and acoustid_key:
            try:
                from .acoustid_fingerprint import match_file

                m = match_file(
                    file_path=file_path,
                    api_key=acoustid_key,
                    min_score=getattr(self.cfg, "acoustid_min_score", 0.6),
                    allow_download_fpcalc=True,
                )
                if m:
                    a = (m.artist or a).strip()
                    t = (m.title or t).strip()
            except Exception:
                pass

        key = self.cache_key(a, t)
        if key in self._meta_cache:
            return dict(self._meta_cache[key])

        meta: Dict[str, Any] = {"artist": a, "title": t}

        # Source priority for rich metadata:
        # 1) iTunes (often provides album + artwork + releaseDate)
        if bool(getattr(self.cfg, "enable_itunes", True)):
            it = self._itunes_lookup(a, t)
            if it:
                meta.update(self._meta_from_itunes(it))

        # 2) MusicBrainz (optional): release title + date; cover art is best-effort
        if bool(getattr(self.cfg, "enable_musicbrainz", False)):
            try:
                mb = self._musicbrainz_trackmeta(a, t)
                if mb:
                    # Only fill blanks; do not overwrite iTunes fields unless iTunes is missing
                    for k, v in mb.items():
                        if v and not meta.get(k):
                            meta[k] = v
            except Exception:
                pass

        # Ensure we always have a genre if we can resolve one
        try:
            g = self._resolve_impl(a, t)
            if g and g != "Unknown":
                meta["genre"] = normalize_genre(g)
        except Exception:
            pass

        self._meta_cache[key] = dict(meta)
        return meta
    
    def save_cache(self) -> None:
        safe_write_json(CACHE_PATH, self.cache)

    def cache_key(self, artist: str, title: str) -> str:
        return f"{artist.lower()}||{title.lower()}"

    def _pacing(self) -> None:
        min_pause = float(self.cfg.min_pause_seconds or 0.0)
        if min_pause <= 0:
            return
        now = time.time()
        dt = now - self._last_call_ts
        if dt < min_pause:
            time.sleep(min_pause - dt)
        self._last_call_ts = time.time()

    def _request_json(self, method: str, url: str, *, params: dict | None = None, headers: dict | None = None, data: dict | None = None, timeout: int | None = None) -> tuple[int, Optional[dict], str]:
        timeout = int(timeout or self.cfg.timeout_seconds)
        retries = int(self.cfg.retries)
        backoff = float(self.cfg.backoff_seconds)

        last_err = ""
        for attempt in range(0, retries + 1):
            try:
                self._pacing()
                r = self.http.request(method, url, params=params, headers=headers, data=data, timeout=timeout)
                status = r.status_code
                txt = r.text or ""
                if status in (429, 500, 502, 503, 504):
                    last_err = f"HTTP {status}: {txt[:160]}"
                    if attempt < retries:
                        time.sleep(backoff * (attempt + 1))
                        continue
                if status != 200:
                    return status, None, txt
                try:
                    return status, r.json(), txt
                except Exception:
                    return status, None, txt
            except Exception as e:
                last_err = str(e)
                if attempt < retries:
                    time.sleep(backoff * (attempt + 1))
                    continue
                return 0, None, last_err
        return 0, None, last_err

    def _resolve_impl(self, artist: str, title: str) -> str:
        key = self.cache_key(artist, title)
        if key in self.cache:
            return self.cache[key]

        # 1) Last.fm
        if self.cfg.enable_lastfm:
            g = self._from_lastfm(artist, title)
            if g and g != "Unknown":
                self.cache[key] = normalize_genre(g)
                return self.cache[key]

        # 2) Discogs
        if self.cfg.enable_discogs:
            g = self._from_discogs(artist, title)
            if g and g != "Unknown":
                self.cache[key] = normalize_genre(g)
                return self.cache[key]

        # 3) TheAudioDB (artist metadata)
        if self.cfg.enable_theaudiodb and (self.cfg.theaudiodb_api_key or "").strip():
            g = self._from_theaudiodb(artist)
            if g and g != "Unknown":
                self.cache[key] = normalize_genre(g)
                return self.cache[key]

        # 4) Apple iTunes Search (track metadata)
        if self.cfg.enable_itunes:
            g = self._from_itunes(artist, title)
            if g and g != "Unknown":
                self.cache[key] = normalize_genre(g)
                return self.cache[key]

        # 5) RateYourMusic (experimental)
        if self.cfg.enable_rateyourmusic and (self.cfg.rateyourmusic_cookie or "").strip():
            g = self._from_rateyourmusic(artist, title)
            if g and g != "Unknown":
                self.cache[key] = normalize_genre(g)
                return self.cache[key]

        # 6) Spotify
        if self.cfg.enable_spotify:
            g = self._from_spotify_artist(artist)
            if g and g != "Unknown":
                self.cache[key] = normalize_genre(g)
                return self.cache[key]

        # 4) MusicBrainz
        mbid: Optional[str] = None
        user_enabled_musicbrainz = bool(getattr(self.cfg, "enable_musicbrainz", False))
        if user_enabled_musicbrainz:
            g, mbid = self._from_musicbrainz(artist, title, want_mbid=True)
            if g and g != "Unknown":
                self.cache[key] = normalize_genre(g)
                return self.cache[key]

        # 5) AcousticBrainz (requires MBID)
        if self.cfg.enable_acousticbrainz:
            if not mbid and user_enabled_musicbrainz:
                _, mbid = self._from_musicbrainz(artist, title, want_mbid=True)
            if not mbid:
                self.log("AcousticBrainz: SKIP (geen MusicBrainz recording id beschikbaar; zet MusicBrainz aan).")
            else:
                g = self._from_acousticbrainz(mbid)
                if g and g != "Unknown":
                    self.cache[key] = normalize_genre(g)
                    return self.cache[key]

        self.cache[key] = "Unknown"
        return "Unknown"

    def _from_lastfm(self, artist: str, title: str) -> str:
        if not self.cfg.lastfm_key:
            return "Unknown"
        url = "https://ws.audioscrobbler.com/2.0/"
        params = {"method": "track.getInfo", "api_key": self.cfg.lastfm_key, "artist": artist, "track": title, "format": "json", "autocorrect": 1}
        status, data, raw = self._request_json("GET", url, params=params)
        if status != 200 or not data:
            if status:
                self.log(f"Last.fm: FAIL ({status}) voor {artist} - {title}")
            else:
                self.log(f"Last.fm: FAIL ({raw}) voor {artist} - {title}")
            return "Unknown"
        track = data.get("track") or {}
        toptags = (track.get("toptags") or {}).get("tag") or []
        if isinstance(toptags, dict):
            toptags = [toptags]
        if toptags:
            return (toptags[0].get("name") or "").strip() or "Unknown"
        return "Unknown"

    def _spotify_get_token(self) -> Optional[str]:
        if not self.cfg.enable_spotify:
            return None
        if not (self.cfg.spotify_client_id and self.cfg.spotify_client_secret):
            return None
        now = time.time()
        if self.spotify_token and now < self.spotify_token_exp - 30:
            return self.spotify_token

        auth = base64.b64encode(f"{self.cfg.spotify_client_id}:{self.cfg.spotify_client_secret}".encode("utf-8")).decode("utf-8")
        headers = {"Authorization": f"Basic {auth}"}
        data = {"grant_type": "client_credentials"}
        status, j, raw = self._request_json("POST", "https://accounts.spotify.com/api/token", headers=headers, data=data)
        if status != 200 or not j:
            self.log(f"Spotify token: FAIL ({status}) {raw[:160]}")
            return None
        token = j.get("access_token")
        exp = j.get("expires_in", 3600)
        if not token:
            return None
        self.spotify_token = token
        self.spotify_token_exp = now + float(exp)
        return token

    def _from_spotify_artist(self, artist: str) -> str:
        token = self._spotify_get_token()
        if not token:
            return "Unknown"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": artist, "type": "artist", "limit": 1}
        status, j, _ = self._request_json("GET", "https://api.spotify.com/v1/search", headers=headers, params=params)
        if status != 200 or not j:
            self.log(f"Spotify search: FAIL ({status}) artist={artist}")
            return "Unknown"
        items = (((j or {}).get("artists") or {}).get("items")) or []
        if not items:
            return "Unknown"
        genres = items[0].get("genres") or []
        return genres[0] if genres else "Unknown"

    def _from_musicbrainz(self, artist: str, title: str, want_mbid: bool = False) -> tuple[str, Optional[str]]:
        query = f'recording:"{title}" AND artist:"{artist}"'
        params = {"query": query, "fmt": "json", "limit": 1}
        status, j, _ = self._request_json("GET", "https://musicbrainz.org/ws/2/recording/", params=params, timeout=max(20, self.cfg.timeout_seconds))
        if status != 200 or not j:
            self.log(f"MusicBrainz search: FAIL ({status}) {artist} - {title}")
            return "Unknown", None
        recs = (j or {}).get("recordings") or []
        if not recs:
            return "Unknown", None
        rid = recs[0].get("id")
        if not rid:
            return "Unknown", None

        params2 = {"inc": "genres+tags+artist-credits", "fmt": "json"}
        status2, j2, _ = self._request_json("GET", f"https://musicbrainz.org/ws/2/recording/{rid}", params=params2, timeout=max(20, self.cfg.timeout_seconds))
        if status2 != 200 or not j2:
            self.log(f"MusicBrainz detail: FAIL ({status2}) rid={rid}")
            return "Unknown", rid if want_mbid else None

        genres = (j2 or {}).get("genres") or []
        if genres:
            return (genres[0].get("name") or "Unknown"), rid if want_mbid else None
        tags = (j2 or {}).get("tags") or []
        if tags:
            return (tags[0].get("name") or "Unknown"), rid if want_mbid else None
        return "Unknown", rid if want_mbid else None

    def _from_discogs(self, artist: str, title: str) -> str:
        token = (self.cfg.discogs_token or "").strip()
        if not token:
            return "Unknown"

        url = "https://api.discogs.com/database/search"
        params = {"artist": artist, "track": title, "type": "release", "per_page": 10}
        headers = {"Authorization": f"Discogs token={token}", "User-Agent": self.cfg.user_agent}

        status, j, _ = self._request_json("GET", url, params=params, headers=headers)
        if status != 200 or not j:
            if status:
                self.log(f"Discogs: FAIL ({status}) voor {artist} - {title}")
            return "Unknown"

        results = (j or {}).get("results") or []
        if not results:
            return "Unknown"

        # First-pass: first usable non-Other/Unknown candidate found
        for r0 in results[:8]:
            for g in (r0.get("genre") or []):
                if normalize_genre(str(g)) not in ("Unknown", "Other"):
                    return str(g)
            for s in (r0.get("style") or []):
                if normalize_genre(str(s)) not in ("Unknown", "Other"):
                    return str(s)

        # Other-repair vote across candidates
        votes: dict[str, int] = {}
        for r0 in results[:8]:
            for g in (r0.get("genre") or []):
                ng = normalize_genre(str(g))
                if ng not in ("Unknown", "Other"):
                    votes[ng] = votes.get(ng, 0) + 1
            for s in (r0.get("style") or []):
                ns = normalize_genre(str(s))
                if ns not in ("Unknown", "Other"):
                    votes[ns] = votes.get(ns, 0) + 1

        if votes:
            best_genre, score = max(votes.items(), key=lambda x: x[1])
            if score >= 2:
                self.log(f"Discogs repair: {artist} - {title} -> {best_genre} (votes={score})")
                return best_genre

        return "Unknown"

    def _from_acousticbrainz(self, recording_mbid: str) -> str:
        url = f"https://acousticbrainz.org/api/v1/{recording_mbid}/high-level"
        params = {"map_classes": "true"}
        status, j, _ = self._request_json("GET", url, params=params, timeout=max(25, self.cfg.timeout_seconds))
        if status != 200 or not j:
            if status:
                self.log(f"AcousticBrainz: FAIL ({status}) rid={recording_mbid}")
            return "Unknown"

        threshold = float(self.cfg.acousticbrainz_threshold or 0.60)

        def extract_top(d: dict) -> tuple[Optional[str], float]:
            value = (d or {}).get("value")
            if not isinstance(value, dict):
                return None, 0.0
            top_label, top_score = None, 0.0
            for k, v in value.items():
                if isinstance(v, dict):
                    score = float(v.get("probability", 0.0))
                else:
                    try:
                        score = float(v)
                    except Exception:
                        score = 0.0
                if score > top_score:
                    top_label, top_score = k, score
            return top_label, top_score

        high = j.get("highlevel") or {}
        candidates = []
        for key in ("genre_rosamerica", "genre_tzanetakis", "genre_dortmund", "genre_electronic"):
            if key in high and isinstance(high.get(key), dict):
                candidates.append(high[key])

        if not candidates:
            for k, block in high.items():
                if "genre" in k and isinstance(block, dict) and isinstance(block.get("value"), dict):
                    candidates.append(block)

        best_label, best_score = None, 0.0
        for block in candidates:
            label, score = extract_top(block)
            if score > best_score:
                best_label, best_score = label, score

        if best_label and best_score >= threshold:
            self.log(f"AcousticBrainz: OK {best_label} ({best_score:.2f})")
            return best_label
        return "Unknown"


    # --- Additional metadata sources (v2.4.x)
    def _from_theaudiodb(self, artist: str) -> str:
        """Resolve genre via TheAudioDB artist lookup.
        Returns a raw genre/style string; caller normalizes to closed set.
        """
        key = (self.cfg.theaudiodb_api_key or "").strip()
        if not key:
            self.log("TheAudioDB: SKIP (no API key)")
            return "Unknown"

        url = f"https://theaudiodb.com/api/v1/json/{key}/search.php"
        params = {"s": artist}
        status, j, _ = self._request_json("GET", url, params=params)
        if status != 200 or not j:
            if status:
                self.log(f"TheAudioDB: FAIL ({status}) artist={artist}")
            return "Unknown"

        artists = j.get("artists") or []
        if not artists:
            self.log(f"TheAudioDB: MISS artist={artist}")
            return "Unknown"

        a0 = artists[0] or {}
        g = (a0.get("strGenre") or "").strip()
        s = (a0.get("strStyle") or "").strip()

        raw = ", ".join([x for x in [g, s] if x])
        if raw:
            self.log(f"TheAudioDB: OK {raw}")
            return raw
        self.log(f"TheAudioDB: MISS (no genre/style) artist={artist}")
        return "Unknown"

    def _from_itunes(self, artist: str, title: str) -> str:
        """Resolve genre via Apple iTunes Search (no API key)."""
        r0 = self._itunes_lookup(artist, title)
        if not r0:
            return "Unknown"
        g = (r0.get("primaryGenreName") or "").strip()
        if g:
            self.log(f"iTunes: OK {g}")
            return g
        self.log(f"iTunes: MISS (no primaryGenreName) term={artist} {title}")
        return "Unknown"

    def _itunes_lookup(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Return the best iTunes Search hit (raw result object) for artist+title.

        Rationale
        ---------
        The iTunes Search API may return multiple results for a given term. To avoid
        unstable behaviour (and to ensure a single definitive destination folder),
        we request multiple hits and deterministically select the best match using
        a lightweight similarity score on artist + title.
        """
        term = f"{artist} {title}".strip()
        if not term:
            return None

        # In-memory cache to avoid duplicate calls in the same run
        ck = f"itunes||{term.lower()}"
        if ck in self._meta_cache:
            return dict(self._meta_cache[ck])

        url = "https://itunes.apple.com/search"
        # Ask for multiple hits; we will pick a single winner.
        params = {"term": term, "media": "music", "limit": 10}
        status, j, _ = self._request_json("GET", url, params=params)
        if status != 200 or not j:
            if status:
                self.log(f"iTunes: FAIL ({status}) term={term}")
            return None

        results = j.get("results") or []
        if not results:
            self.log(f"iTunes: MISS term={term}")
            return None

        # --- pick best match ---
        try:
            import re
            from difflib import SequenceMatcher

            def _n(s: str) -> str:
                s = (s or "").lower()
                s = re.sub(r"[^a-z0-9]+", " ", s)
                return re.sub(r"\s+", " ", s).strip()

            a0 = _n(artist)
            t0 = _n(title)

            scored = []
            for i, r in enumerate(results):
                r = r or {}
                ra = _n(str(r.get("artistName") or ""))
                rt = _n(str(r.get("trackName") or ""))

                # Similarity ratios in [0,1]; scale to [0,100]
                ar = SequenceMatcher(None, a0, ra).ratio() if (a0 and ra) else 0.0
                tr = SequenceMatcher(None, t0, rt).ratio() if (t0 and rt) else 0.0

                # Weight title higher than artist to reduce false positives.
                score = (40.0 * ar) + (60.0 * tr)

                # Small bonus if normalized strings contain each other.
                if a0 and ra and (a0 in ra or ra in a0):
                    score += 5.0
                if t0 and rt and (t0 in rt or rt in t0):
                    score += 10.0

                scored.append((score, -i, r))

            scored.sort(reverse=True)
            best_score, _, best = scored[0]
            try:
                best["_gs_confidence"] = float(best_score)
            except Exception:
                pass
            self.log(f"iTunes: SELECT best_score={best_score:.1f} hits={len(results)} term={term}")
            r0 = best
        except Exception:
            # Fallback: behave like legacy implementation.
            r0 = results[0] or {}
            try:
                r0["_gs_confidence"] = 0.0
            except Exception:
                pass

        self._meta_cache[ck] = dict(r0)
        return r0

    def _meta_from_itunes(self, r0: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Track metadata from iTunes Search result."""
        out: Dict[str, Any] = {}
        out["title"] = (r0.get("trackName") or "").strip() or None
        out["artist"] = (r0.get("artistName") or "").strip() or None
        out["album"] = (r0.get("collectionName") or "").strip() or None
        out["album_artist"] = (r0.get("collectionArtistName") or "").strip() or None
        out["track_number"] = r0.get("trackNumber")
        out["disc_number"] = r0.get("discNumber")
        out["genre"] = normalize_genre((r0.get("primaryGenreName") or "").strip() or "Unknown")
        try:
            out["confidence"] = float(r0.get("_gs_confidence")) if r0.get("_gs_confidence") is not None else None
        except Exception:
            out["confidence"] = None

        # releaseDate is ISO 8601, e.g. 2012-05-21T07:00:00Z
        rd = (r0.get("releaseDate") or "").strip()
        if rd:
            out["release_date"] = rd[:10]

        # Artwork: try higher-res variant where possible
        art_url = (r0.get("artworkUrl600") or r0.get("artworkUrl100") or "").strip()
        if art_url and "artworkUrl100" in art_url:
            art_url = art_url.replace("100x100", "600x600")
        if art_url:
            try:
                self._pacing()
                rr = self.http.get(art_url, timeout=max(15, self.cfg.timeout_seconds))
                if rr.status_code == 200 and rr.content:
                    out["cover_bytes"] = rr.content
            except Exception:
                pass

        return {k: v for k, v in out.items() if v not in (None, "")}

    def _musicbrainz_trackmeta(self, artist: str, title: str) -> Dict[str, Any]:
        """Best-effort MusicBrainz lookup for release title/date and (optionally) cover art."""
        query = f'recording:"{title}" AND artist:"{artist}"'
        params = {"query": query, "fmt": "json", "limit": 1}
        status, j, _ = self._request_json(
            "GET",
            "https://musicbrainz.org/ws/2/recording/",
            params=params,
            timeout=max(20, self.cfg.timeout_seconds),
        )
        if status != 200 or not j:
            return {}
        recs = (j or {}).get("recordings") or []
        if not recs:
            return {}

        rid = recs[0].get("id")
        if not rid:
            return {}

        params2 = {"inc": "artist-credits+releases", "fmt": "json"}
        status2, j2, _ = self._request_json(
            "GET",
            f"https://musicbrainz.org/ws/2/recording/{rid}",
            params=params2,
            timeout=max(20, self.cfg.timeout_seconds),
        )
        if status2 != 200 or not j2:
            return {}

        out: Dict[str, Any] = {}
        releases = (j2 or {}).get("releases") or []
        if releases:
            r0 = releases[0] or {}
            out["album"] = (r0.get("title") or "").strip() or None
            date = (r0.get("date") or "").strip()
            if date:
                # MB dates can be YYYY, YYYY-MM, or YYYY-MM-DD
                out["release_date"] = date

            # Cover art: best-effort via Cover Art Archive if we have a release id
            rel_id = (r0.get("id") or "").strip()
            if rel_id:
                try:
                    caa_url = f"https://coverartarchive.org/release/{rel_id}/front"
                    self._pacing()
                    rr = self.http.get(caa_url, timeout=max(15, self.cfg.timeout_seconds), headers={"Accept": "image/*"})
                    if rr.status_code == 200 and rr.content:
                        out["cover_bytes"] = rr.content
                except Exception:
                    pass

        return {k: v for k, v in out.items() if v not in (None, "")}

    def _from_rateyourmusic(self, artist: str, title: str) -> str:
        """RateYourMusic is experimental: no official public API.
        We do not scrape by default. If enabled, this method currently acts as a safe stub.
        """
        cookie = (self.cfg.rateyourmusic_cookie or "").strip()
        if not cookie:
            self.log("RYM: SKIP (no cookie/token configured)")
            return "Unknown"
        # Best-effort placeholder (safe): do not scrape content.
        self.log("RYM: SKIP (experimental source not implemented)")
        return "Unknown"

# -----------------------------
# Worker thread
# -----------------------------
