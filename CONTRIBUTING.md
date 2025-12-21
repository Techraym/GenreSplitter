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
