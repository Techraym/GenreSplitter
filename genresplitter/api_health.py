"""Connectivity checks for individual APIs.

These tests validate credentials and basic availability without requiring a
specific artist/title lookup.
"""

from __future__ import annotations

import base64
from typing import Tuple

import requests

from .meta import APP_NAME, APP_VERSION


def _ua() -> str:
    return f"{APP_NAME}/{APP_VERSION} (portable)"


def test_lastfm(api_key: str, timeout: int = 8) -> Tuple[bool, str]:
    if not (api_key or "").strip():
        return False, "Last.fm API key ontbreekt"
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {"method": "chart.getTopArtists", "api_key": api_key.strip(), "format": "json", "limit": 1}
    try:
        r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": _ua()})
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:160]}"
        j = r.json() if r.text else {}
        artists = ((j or {}).get("artists") or {}).get("artist")
        if artists:
            name = artists[0].get("name") if isinstance(artists, list) else None
            return True, f"OK (top artist: {name})" if name else "OK"
        return True, "OK"
    except Exception as e:
        return False, str(e)


def test_discogs(token: str, timeout: int = 8) -> Tuple[bool, str]:
    if not (token or "").strip():
        return False, "Discogs user token ontbreekt"
    url = "https://api.discogs.com/oauth/identity"
    headers = {"User-Agent": _ua(), "Authorization": f"Discogs token={token.strip()}"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:160]}"
        j = r.json() if r.text else {}
        return True, f"OK (user: {j.get('username')})" if j.get("username") else "OK"
    except Exception as e:
        return False, str(e)


def test_spotify(client_id: str, client_secret: str, timeout: int = 8) -> Tuple[bool, str]:
    if not (client_id or "").strip() or not (client_secret or "").strip():
        return False, "Spotify client id/secret ontbreekt"
    url = "https://accounts.spotify.com/api/token"
    basic = base64.b64encode(f"{client_id.strip()}:{client_secret.strip()}".encode("utf-8")).decode("utf-8")
    headers = {"Authorization": f"Basic {basic}", "User-Agent": _ua()}
    data = {"grant_type": "client_credentials"}
    try:
        r = requests.post(url, headers=headers, data=data, timeout=timeout)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:160]}"
        j = r.json() if r.text else {}
        tok = j.get("access_token")
        return (True, "OK (token ontvangen)") if tok else (False, "Geen access_token in response")
    except Exception as e:
        return False, str(e)


def test_musicbrainz(timeout: int = 8) -> Tuple[bool, str]:
    url = "https://musicbrainz.org/ws/2/artist"
    params = {"query": "artist:radiohead", "limit": 1, "fmt": "json"}
    try:
        r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": _ua()})
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:160]}"
        return True, "OK"
    except Exception as e:
        return False, str(e)


def info_acousticbrainz() -> Tuple[bool, str]:
    # AcousticBrainz requires a MusicBrainz recording MBID; no standalone credential test.
    return True, "Info: AcousticBrainz heeft een recording MBID nodig; geen standalone API-test mogelijk"


def test_theaudiodb(api_key: str, timeout: int = 8) -> Tuple[bool, str]:
    """Test TheAudioDB by looking up a well-known artist."""
    if not (api_key or "").strip():
        return False, "TheAudioDB API key ontbreekt"
    url = f"https://theaudiodb.com/api/v1/json/{api_key.strip()}/search.php"
    params = {"s": "Radiohead"}
    try:
        r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": _ua()})
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:160]}"
        j = r.json() if r.text else {}
        artists = j.get("artists") or []
        if not artists:
            return False, "Geen artist results (key geldig?)"
        g = (artists[0].get("strGenre") or "").strip()
        return True, f"OK (genre: {g})" if g else "OK"
    except Exception as e:
        return False, str(e)


def test_itunes(timeout: int = 8) -> Tuple[bool, str]:
    """Test Apple iTunes Search API (no key required)."""
    url = "https://itunes.apple.com/search"
    params = {"term": "Radiohead Creep", "media": "music", "limit": 1}
    try:
        r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": _ua()})
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:160]}"
        j = r.json() if r.text else {}
        results = j.get("results") or []
        if not results:
            return False, "Geen results"
        g = (results[0].get("primaryGenreName") or "").strip()
        return True, f"OK (primaryGenreName: {g})" if g else "OK"
    except Exception as e:
        return False, str(e)



def test_acoustid(client_key: str, timeout: int = 8) -> Tuple[bool, str]:
    """Validate AcoustID client API key by calling lookup-by-trackid on a known public track id."""
    key = (client_key or "").strip()
    if not key:
        return False, "API key ontbreekt"
    url = "https://api.acoustid.org/v2/lookup"
    params = {
        "client": key,
        "meta": "recordingids",
        # Example trackid from official docs
        "trackid": "9ff43b6a-4f16-427c-93c2-92307ca505e0",
        "format": "json",
    }
    headers = {"User-Agent": _ua()}
    try:
        r = requests.get(url, params=params, timeout=timeout, headers=headers)
        if r.status_code != 200:
            # Try to extract a useful error message from the response (AcoustID often returns JSON even on errors)
            msg = ""
            try:
                j = r.json()
                if isinstance(j, dict):
                    err = j.get("error") or {}
                    if isinstance(err, dict):
                        em = err.get("message")
                        ec = err.get("code")
                        if em:
                            msg = str(em) + (f" (code {ec})" if ec is not None else "")
            except Exception:
                pass
            if not msg:
                body = (r.text or "").strip().replace("\n", " ")
                if len(body) > 200:
                    body = body[:200] + "…"
                msg = body
            return False, f"HTTP {r.status_code}" + (f": {msg}" if msg else "")
        data = r.json()
        if (data.get("status") or "").lower() != "ok":
            err = data.get("error") or {}
            msg = err.get("message") or str(err) or "Onbekende fout"
            code = err.get("code")
            return False, f"{msg}" + (f" (code {code})" if code is not None else "")
        results = data.get("results") or []
        if not results:
            return True, "OK (key geldig; geen resultaten voor test-ID)"
        return True, "OK"
    except Exception as e:
        return False, str(e)



def test_rateyourmusic(cookie: str, timeout: int = 8) -> Tuple[bool, str]:
    """Experimental: RateYourMusic has no official public API. This checks basic reachability and optional auth cookie."""
    if not (cookie or "").strip():
        return False, "Cookie/token ontbreekt (RYM heeft geen officiële API)"
    url = "https://rateyourmusic.com"
    headers = {"User-Agent": _ua(), "Cookie": cookie.strip()}
    try:
        r = requests.get(url, timeout=timeout, headers=headers)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        return True, "OK (homepage bereikbaar; API is experimenteel)"
    except Exception as e:
        return False, str(e)
