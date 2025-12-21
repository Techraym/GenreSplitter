## [2.9.0-hotfix5] - 2025-12-21
### Added
- Metadata update policies:
  - `confidence`: overschrijf tags alleen bij hoge matchscore (drempel instelbaar); anders alleen lege tags vullen.
  - `cover_only`: update alleen artwork; teksttags blijven ongewijzigd.
### Changed
- iTunes-matchscore (`confidence`) wordt nu meegegeven aan de tagger en rapportage.
### Fixed
- Voorkomt onbedoeld overschrijven van bestaande tags bij lage matchconfidence (indien policy `confidence` actief).

## [2.9.0-hotfix4] - 2025-12-21
### Fixed
- Cover art wordt nu altijd in een breed ondersteund formaat opgeslagen: WEBP/GIF/unknown wordt geconverteerd naar JPEG/PNG (waar mogelijk via Pillow).
- Bestaande artwork wordt consistent overschreven (MP3/WAV/AIFF: verwijdert alle APIC frames; FLAC: `clear_pictures()`; MP4: vervangt `covr`; OGG/OPUS: vervangt `METADATA_BLOCK_PICTURE`).

## [2.9.0-hotfix3] - 2025-12-21
### Fixed
- Stoppen/annuleren crash: `SortWorker.write_run_report` wordt nu altijd geïnitialiseerd, waardoor het stoppen geen AttributeError meer geeft.

## [2.9.0-hotfix2] - 2025-12-21
### Fixed
- iTunes selectie: bij meerdere iTunes-hits wordt nu deterministisch één “beste match” gekozen op basis van artist/titel-similarity.
  Dit voorkomt dat één track in meerdere mappen terechtkomt; er wordt altijd één keer verplaatst naar de beste match.

## [2.9.0-hotfix1] - 2025-12-21
### Fixed
- Python 3.13 compatibiliteit: vervangt `imghdr` (verwijderd in 3.13) door Pillow voor cover-art type detectie.

## [2.9.0] - 2025-12-21
### Added
- Multi-format metadata schrijven: MP3 (ID3v2.4), FLAC, M4A/MP4, WAV/AIFF, OGG/OPUS.
- Best-effort meta enrichment: artist, title, album, album artist, track/disc, release date + albumcover (waar beschikbaar).
- Run-rapportage per sessie: CSV + JSON in `<doelmap>/_GenreSplitter_Reports/`.

### Changed
- Bestandsfilter uitgebreid: naast MP3 ook FLAC/M4A/WAV en gangbare containers (AIFF/OGG/OPUS).

### Notes
- Metadata wordt alleen gezet waar beschikbaar; geen “Unknown” overschrijvingen.

## [2.8.11] (Final clean) - 2025-12-16
### Changed
- AcoustID mag MusicBrainz tijdelijk gebruiken als fallback wanneer AcoustID geen genre kan vinden, zonder de gebruikersinstelling permanent te wijzigen.

## [2.8.10] - 2025-12-16
### Fixed
- Fix: SortWorker pad-afhandeling en corrupte regels in workers.py.

### Docs
- Toegevoegd: uitleg over iTunes/Apple Music-instellingen die duplicaten veroorzaken bij extern verplaatsen.

## [2.8.9] - 2025-12-16
### Fixed
- Fixed crash: NameError ('path' not defined) tijdens track verwerking.

## [2.8.8] - 2025-12-16
### Fixed
- Fix: AcoustID health-check string parsing (startup SyntaxError).
- Fix: Package folder name in zip consistent gemaakt.

## [2.8.4] – Hotfix
### Fixed
- Fix: crash in Settings → AcoustID door ontbrekende SettingsDialog._test_fpcalc binding (AttributeError).

## [2.8.3] – Hotfix
### Fixed
- Fix: fpcalc autodetectie uitgebreid voor WinGet Packages/Links (zoals WinGet package installpad) en betrouwbaarder PATH-resolutie.
### Added
- UI: Release notes in hoofdscherm + testknoppen op tabblad AcoustID (fpcalc + AcoustID key) voor snelle diagnose.
## [2.8.2] – UX
### Added
- Add: 'Test fpcalc' button on AcoustID settings tab to verify Chromaprint detection and version

## [2.8.1] – Hotfix
### Fixed
- Fix: Improve fpcalc detection (PATH + common Windows locations + override via GENRESPLITTER_FPCALC)

## [2.8.0] – Restore full functionality + AcoustID Fingerprinting
### Added
- Optional AcoustID fingerprinting using pyacoustid + Chromaprint fpcalc
- Automatic fpcalc bootstrap on Windows (downloads official fpcalc ZIP into %APPDATA%\\GenreSplitter\\bin)
- New Settings tab: AcoustID (enable, API key, minimum score)
### Changed
- Worker uses resolver.resolve_track() when available for file-based identification
### Notes
- On macOS/Linux, install fpcalc via brew/apt/pacman; AcoustID gracefully falls back if missing.

## [2.5.7] – Hotfix
### Fixed
- Fix: Missing QtWidgets imports (e.g., QLineEdit) causing startup crash
- Refactor: Normalize PyQt6.QtWidgets import list for stability

## [2.5.6] – Hotfix
### Fixed
- Fix: Missing QDialog import causing startup crash

## [2.5.5] – Hotfix
### Fixed
- Fix: Invalid PyQt6.QtWidgets import syntax causing startup crash
- Fix: Normalize QApplication import for SplashScreen status updates

## [2.5.4] – Hotfix
### Fixed
- Fix: NameError in SplashScreen.set_status (QApplication not imported)

## [2.5.3] – Hotfix
### Fixed
- Fix: SplashScreen initialization mismatch (app.py now passes title/subtitle/logo_path; SplashScreen has safe defaults)
- Fix: Remove Windows escape-sequence warning in storage docstring

## 2.4.9
- UX: splashscreen layout cleaned up (grid-aligned logo/text)
- UX: interactive splash with live status + progress updates
- UX: splash stays visible 5s after reaching 100% and closes before main window shows
- Branding: new logo.svg used everywhere

## 2.4.8
- UX: splashscreen 50% groter en blijft 5s zichtbaar
- UX: hoofdvenster verschijnt pas nadat splash sluit (sequentiële handoff)
- UX: startup acties worden getoond in splash status

## 2.4.7
- Fix: IndentationError in genresplitter/storage.py (clean rewrite)
- Fix: restore full storage API without syntax or indent issues


## 2.4.6
- Fix: restore storage API (CACHE_PATH, safe_load_json) required by api_resolver
- Fix: remove invalid escape sequence warning in storage docstring
## 2.4.5
- Fix: startup crash (stray quote in ui.py logging write)
- Note: requires PyQt6 installed via requirements.txt


## 2.4.4
- Fix: startup crash (SyntaxError in ui.py)
- Fix: startup crash (IndentationError in storage.py)
- Fix: settings/log storage moved to per-user writable directory (AppData)
# Changelog

## 2.4.1 – Hotfix (2025-12-15)
- Fix: implement iTunes/TheAudioDB/RYM resolver methods (prevents crash on missing _from_itunes)

## 2.4.0 – API Tabs & API uitbreidingen (2025-12-15)
- Feature: aparte Settings-tab per API (toggle, credential link, test + resultaat)
- Feature: TheAudioDB (artist genre/style) toegevoegd
- Feature: Apple iTunes Search (primaryGenreName) toegevoegd
- Feature: RateYourMusic tab toegevoegd (experimenteel; geen officiële API)
- Fix: MusicBrainz API test gebruikt nu geldige `query` (voorkomt HTTP 400)
- Docs: GitHub-conforme projectdocumentatie uitgebreid

## 2.3.2 – Modularization + API Test Fix (2025-12-13)
- Fix: Settings "Test" is weer een echte API-connectiviteitstest per bron (geen artiest/titel nodig)
- Improvement: app opgesplitst in een modulair `genresplitter/` package (beter onderhoudbaar)
- Improvement: uitgebreide genre-normalisatie met multi-value parsing (komma's, slashes, koppeltekens)

## 2.2.8 – Reliability (2025-12-13)
- Verbetering: meer kans van slagen bij genre-resolutie door hogere timeouts, retries en backoff per API-call
- Verbetering: zachte pacing tussen requests om rate limits te verminderen bij grote batches
- Docs/UI: copyright en ‘last updated’ toegevoegd (13-december-2025)


## 2.2.7
- Feature: Discogs bron toegevoegd (curated genres/styles)
- Feature: AcousticBrainz (Essentia) bron toegevoegd (opt-in, threshold)
- Feature: API toggles per bron + links in Settings
- Fix: ID3 default UIT en bij uitschakelen volledig uit
- Improvement: agressievere genre folding (minder subcategorieën)
- Fix: Unknown indeling naar `Unknown/<Bucket>/<Artist>/`
- Fix: cache-waarden altijd normaliseren om legacy genres te vermijden

## 2.2.2
- Projectstructuur gereorganiseerd
- Portable-first layout