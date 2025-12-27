# Contributing

Dank voor je bijdrage.

## Scope
GenreSplitter is bewust **geen** “alles kan”-tagger. We houden vast aan:
- Gesloten genre-set
- Deterministische output
- Geen map-explosie

## Pull requests
- Hou PR’s klein en gericht.
- Voeg voor nieuwe API’s altijd toe:
  - Settings-tab + credential link (indien van toepassing)
  - `api_health` testfunctie
  - Observability logging (korte, duidelijke regels)
  - Fallback-gedrag dat nooit nieuwe genres introduceert

## Code style
- Python: eenvoudige, expliciete code
- Geen ongecontroleerde exceptions in UI-thread

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
