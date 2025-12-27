# Security Policy

## Supported Versions
Alleen de laatste minor (2.4.x) wordt actief ondersteund.

## Reporting
Rapporteer security issues via een GitHub issue met label **security** of neem contact op met de maintainer.

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
