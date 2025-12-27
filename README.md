# GenreSplitter 🎵


## Instellingen en API-tokens (opslaglocatie)

GenreSplitter slaat **jouw instellingen en API-tokens lokaal per gebruiker** op in:

- Windows: `%APPDATA%\GenreSplitter\settings.json`

In de projectmap meegeleverd `settings.json` / `genresplitter_settings.example.json` zijn **voorbeelden** en bevatten in deze clean release **geen tokens**.

**Versie:** 2.9.0  
**Datum:** 16-december-2025  
**Release notes:** 2.9.0: Multi-format metadata tagging (MP3/ID3v2.4, FLAC, M4A/MP4, WAV/AIFF, OGG/OPUS) incl. cover art + uitgebreide run-rapportage (CSV + JSON).
**Licentie:** MIT (zie `LICENSE`)

GenreSplitter is een **portable desktop-app** die MP3-bestanden sorteert in een **voorspelbare mappenstructuur** op basis van **(basis)genre** en **artiest-bucket**.  
Het ontwerpdoel is: **minder mapvervuiling, minder tag-chaos, minder “Other”**.

## Kernprincipes
- **Gesloten genresysteem:** geen onbeperkte subgenre-explosie.
- **Deterministisch:** dezelfde input geeft dezelfde output.
- **Bronnen zijn optioneel:** elke API is per tab aan/uit te zetten.
- **Observability:** in de log zie je welke bron(s) zijn gebruikt en waarom.

## Installatie
1. Installeer Python 3.11+ (Windows)
2. Installeer dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start:
   ```bash
   python main.py
   ```

## Gebruik
1. Kies **bronmap** (met MP3’s)
2. Kies **doelmap**
3. (Optioneel) **Dry-run**
4. Start sorteren

Bestandsnaamformaat dat wordt verwerkt:
```
ARTIEST - TITEL.mp3
```

## Doelstructuur
```
Doelmap/
  <Genre>/
    0-9/
    A/
    ...
    Z/
    !-?/
      ARTIEST - TITEL.mp3
```

## APIs (per tab in Settings)
Elke API heeft in Settings een eigen tab met:
- Enable toggle
- Link om credentials aan te vragen (indien nodig)
- Test-knop + resultaatvenster

### Credential-links
- Last.fm API key: https://www.last.fm/api/account/create
- Discogs token: https://www.discogs.com/settings/developers
- Spotify dashboard: https://developer.spotify.com/dashboard
- MusicBrainz API: https://musicbrainz.org/doc/MusicBrainz_API (geen key)
- AcousticBrainz docs: https://acousticbrainz.readthedocs.io/api.html (geen key, wél MBID nodig)
- TheAudioDB API key: https://www.theaudiodb.com/api_apply.php
- Apple iTunes Search API: geen key (docs link in Settings)
- RateYourMusic: **geen officiële publieke API** (experimenteel)

## Pipeline (hoog niveau)
1. Last.fm
2. Discogs
3. TheAudioDB
4. Apple iTunes Search
5. RateYourMusic (experimenteel, optioneel)
6. Spotify
7. MusicBrainz
8. AcousticBrainz (vereist MusicBrainz recording MBID)
9. Keywords
10. ID3 fallback (alleen indien ingeschakeld)

Alle resultaten gaan door `normalize_genre()` zodat output binnen een gesloten set blijft.

## Troubleshooting
- **AcousticBrainz: SKIP (geen MusicBrainz recording id)**  
  Zet **MusicBrainz aan**. AcousticBrainz heeft een recording MBID nodig.
- **Discogs 429 rate limit**  
  Verhoog `Min pause (sec)` en/of `Backoff (sec)` in Settings → Algemeen.

## Development
- Code is modulair in `genresplitter/`
- PR’s: zie `CONTRIBUTING.md`

## License
MIT – zie `LICENSE`.

## v2.10.8

- App icon set to `Logo.ico` (application + main window).
- hang.log disabled by default.
- Genre system enhancements (top-level genres, normalization, iTunes safety-net) from the 2.9.3 hotfix series.
- UI: higher-contrast checkboxes on dark theme.
