
# Final Release Documentation Checklist

This checklist must be completed before declaring a Final Release.

---

## Documentation
- [ ] README reviewed and up to date
- [ ] USER_GUIDE validated against current UI
- [ ] TECHNICAL documentation reviewed
- [ ] FAQ includes common Beta issues
- [ ] CHANGELOG complete and accurate
- [ ] ROADMAP updated

---

## Quality & Stability
- [ ] No withdrawn builds pending
- [ ] No critical open bugs
- [ ] Sorting logic validated on large libraries
- [ ] Logging verified on clean Windows machine

---

## Packaging
- [ ] auto-py-to-exe build successful
- [ ] Assets included (logo, icons)
- [ ] AppData paths verified
- [ ] EXE tested without Python installed

---

## Release
- [ ] Final version tagged
- [ ] Release notes published
- [ ] Beta label removed

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
