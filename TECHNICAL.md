# GenreSplitter – Technical Documentation

**Versie:** v2.3.2  
**Datum:** 13-december-2025

## Architectuur

- PyQt6 GUI
- Worker thread voor IO + netwerk
- Gesloten genresysteem
- JSON cache + settings

## Genrebronnen (pipeline)

1. Last.fm (track tags) – optioneel
2. Discogs (release genres/styles) – optioneel
3. Spotify (artist genres) – optioneel
4. MusicBrainz (recording genres/tags) – optioneel
5. AcousticBrainz (Essentia high-level genre) – optioneel, probabilistisch
6. Keyword heuristiek
7. ID3 fallback – alleen als expliciet aangezet

Alle outputs gaan door `normalize_genre()` zodat er geen genre-explosie ontstaat.

## Discogs

- Gebruik: `GET https://api.discogs.com/database/search`
- Auth: `Authorization: Discogs token=<USER_TOKEN>`
- Resultaten: `genre[]` (en soms `style[]`)

## AcousticBrainz

- Gebruik: `GET /api/v1/<recording_mbid>/high-level?map_classes=true`
- Vereist: MusicBrainz recording MBID
- Acceptatie: hoogste klasse met `prob >= threshold`


---

**Copyright © 2025 GenreSplitter contributors.**  
**Laatst bijgewerkt:** 13 december 2025

## Nieuwe API tabs (v2.4.0)
- Elke API heeft een eigen tabblad in Settings met enable, credential-link, test-knop en resultaat.
- Nieuwe bronnen: TheAudioDB en Apple iTunes Search.
- RateYourMusic is experimenteel (geen officiële API).

### Credential links
- Last.fm: https://www.last.fm/api/account/create
- Discogs: https://www.discogs.com/settings/developers
- Spotify: https://developer.spotify.com/dashboard
- MusicBrainz: https://musicbrainz.org/doc/MusicBrainz_API
- AcousticBrainz: https://acousticbrainz.readthedocs.io/api.html
- TheAudioDB: https://www.theaudiodb.com/api_apply.php

## v2.10.8 – UI & Documentation Update
**Release date:** 27-December-2025

### UI
- Dropdowns now show a clear ▼ arrow indicator
- Visible border when expanded
- Improved contrast, focus and hover states

### Genre system
- Vastly reduced incorrect `Other` assignments
- Added and normalized top-level genres (Dance, Indie, Trance, House, EDM, etc.)
- iTunes fallback when primary APIs return unmapped genres

### Stability
- `hang.log` disabled
- Subprocess API resolver stabilized
- Improved Unicode handling
