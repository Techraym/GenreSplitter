# GitHub Labels & Triage Strategy (Definitive)

This document defines the **official labels** and the **triage workflow** for the GenreSplitter public repository during Beta and into Final Release.

Principles:
- Reduce noise and ambiguity
- Make risk visible (data loss vs cosmetic)
- Ensure releases are blocked by the right signals
- Make decisions traceable and consistent

---

## Label taxonomy

### 1) Severity (required for all bug issues)

| Label | Meaning | Examples |
|---|---|---|
| `severity:critical` | Data loss risk, startup crash, unsafe file operations | crash on launch, overwriting files, moving wrong directories |
| `severity:high` | Core feature broken, no practical workaround | sorting can't start, target path invalid without workaround |
| `severity:medium` | Feature partially broken, workaround exists | UI misbehavior with workaround |
| `severity:low` | Cosmetic or minor UX issue | spacing, wording, minor visual glitches |

**Rule:** `severity:critical` and `severity:high` block releases.

---

### 2) Type (one required)

| Label | Use |
|---|---|
| `type:bug` | Incorrect behavior |
| `type:regression` | Worked in a previous version |
| `type:ux` | Confusing or unclear UI/flow |
| `type:performance` | Slowdowns, freezes, excessive CPU/disk |
| `type:docs` | Documentation |
| `type:build` | Packaging / auto-py-to-exe / distribution |
| `type:security` | Security-relevant behavior |

---

### 3) Status / workflow

| Label | Meaning |
|---|---|
| `status:triage` | New, not yet assessed |
| `status:accepted` | Accepted for work |
| `status:blocked` | Blocked by dependency (external or internal) |
| `status:needs-info` | Reporter must provide additional info |
| `status:duplicate` | Duplicate of another issue |
| `status:won't-fix` | Intentionally not addressed |

**Rule:** any issue without `status:*` is treated as untriaged.

---

### 4) Release targeting (milestone labels)

| Label | Meaning |
|---|---|
| `milestone:beta` | Can ship during Beta |
| `milestone:final` | Must be resolved before Final |
| `milestone:post-final` | Nice-to-have after Final |

---

### 5) Special handling (triage helpers)

| Label | Meaning |
|---|---|
| `needs-repro` | Not reproducible with provided info |
| `needs-logs` | Log file excerpt required |
| `breaking-change` | Changes user-visible behavior in a significant way |
| `withdrawn-version` | Related to a withdrawn build; document and close if not applicable |

---

## Triage workflow (step-by-step)

### Step 0: Intake
All new issues start with:
- `status:triage`
- `type:*` (template-driven)

### Step 1: Validate minimum information
A bug report must include:
- Version (e.g., 2.4.9)
- Windows version
- Steps to reproduce
- Expected vs actual behavior

If incomplete:
- apply `status:needs-info`
- apply `needs-logs` and/or `needs-repro` as appropriate

### Step 2: Risk assessment
Assign severity:
- If there is any plausible data loss, overwrite, or wrong-path move risk → `severity:critical`
- If core sorting cannot run → `severity:high`
- If only partial impact with workaround → `severity:medium`
- If cosmetic → `severity:low`

### Step 3: Release targeting
Assign milestone:
- Beta-only issues that do not block shipping → `milestone:beta`
- Anything that could impact safety, correctness, or trust → `milestone:final`
- Wishlist and non-essential polish → `milestone:post-final`

### Step 4: Decision
Choose one:
- `status:accepted` if work will be scheduled
- `status:won't-fix` with an explanation if rejected
- `status:blocked` if blocked by dependencies

### Step 5: Closure hygiene
When closing:
- reference the fix commit/release tag
- update `CHANGELOG.md` if user-visible

---

## Operating rules

### Release blocking rules
A release must not ship if:
- Any open issue has `severity:critical` or `severity:high`
- Any open issue has `type:security` without mitigation
- The build protocol fails on a clean machine

### Beta transparency rules
- Withdrawn releases remain documented (do not delete history)
- Regressions must be explicitly labeled `type:regression`

---

## Suggested GitHub label colors (optional)
You may optionally apply consistent colors:
- Severity: red spectrum
- Type: blue spectrum
- Status: gray/purple
- Milestones: green spectrum

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
