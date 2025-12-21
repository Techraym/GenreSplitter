# Release Notes Templates (Beta → Final)

These templates are used for GitHub Releases to ensure consistency, transparency, and auditability.

---

## Beta Release Notes Template

```markdown
## GenreSplitter vX.Y.Z (Beta)

⚠️ **Beta release**  
This version may contain breaking changes or incomplete features.
Always use Dry-run and keep backups.

---

### Highlights
- Short summary of the most important changes

---

### Added
- New features introduced in this version

---

### Changed
- Behavior changes (explicitly documented)

---

### Fixed
- Bugs fixed since last release

---

### Known Issues
- Known limitations or unresolved problems

---

### Withdrawn / Breaking Notes
- Mention withdrawn versions or regressions if applicable

---

### Upgrade Notes
- Steps users should take before or after upgrading
```

---

## Final Release Notes Template

```markdown
## GenreSplitter vX.0.0 (Final Release)

🎉 **Final Release**

This is the first stable release of GenreSplitter.
It is intended for everyday use on production music libraries.

---

### What this release guarantees
- Stable sorting behavior
- Safe file operations
- Verified logging and settings persistence
- Tested Windows `.exe` build

---

### Key Features
- Feature list (finalized)

---

### Changes since Beta
- Summary of major Beta → Final changes

---

### Breaking Changes (if any)
- Explicit list (ideally empty)

---

### Migration Notes
- Instructions for upgrading from Beta

---

### Known Limitations
- Explicitly documented, no surprises

---

### Support
- How to report issues
- Scope of support
```
