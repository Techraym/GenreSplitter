# GenreSplitter – User Guide


## Instellingen en API-tokens (opslaglocatie)

GenreSplitter slaat **jouw instellingen en API-tokens lokaal per gebruiker** op in:

- Windows: `%APPDATA%\GenreSplitter\settings.json`

In de projectmap meegeleverd `settings.json` / `genresplitter_settings.example.json` zijn **voorbeelden** en bevatten in deze clean release **geen tokens**.

**Versie:** v2.3.2  
**Datum:** 13-december-2025

## Basisgebruik

1. Kies bronmap
2. Kies doelmap
3. (Optioneel) Dry-run
4. Start sorteren

## Bestandsnaam

```
ARTIEST - TITEL.mp3
```

## Dry-run

Dry-run is veilig: er worden geen bestanden verplaatst.

## Genrelogica (samengevat)

1. Online bronnen (optioneel, schakelbaar):
   - Last.fm, Discogs, Spotify, MusicBrainz, AcousticBrainz (Essentia)
2. Keyword-heuristiek
3. ID3 (alleen als expliciet aangezet; laatste fallback)

## Unknown-indeling

Unknown wordt gesorteerd als:

```
Unknown/<Bucket>/<Artist>/
```

Dit houdt Unknown beheersbaar bij grote libraries.

## AcousticBrainz threshold

AcousticBrainz is probabilistisch. Alleen resultaten boven de threshold (default 0.60) worden geaccepteerd.


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
