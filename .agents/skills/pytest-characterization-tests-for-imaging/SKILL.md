---
name: pytest-characterization-tests-for-imaging
description: Create or extend JFIN imaging characterization + golden tests to preserve current image behavior (scale decisions, crop/padding rules, EXIF handling, and encoding outputs) before refactoring. Use when touching src/jfin/imaging.py or any code path that changes rendered images or resize planning. Don’t use for CLI/config contracts, API safety gates, or pipeline/restore workflow behavior (separate skills/suites own those).
compatibility: Python 3.13+, pytest, Pillow. Tests are designed to run offline (no Jellyfin server).
metadata:
  version: "2.0.0"
  updated: "2026-03-04"
  owners:
    - "@codex"
    - "@alexkahler"
  notes: Optional tooling ideas (not required): pytest-regressions (image_regression), Syrupy snapshots, or ApprovalTests can improve developer UX for reviewing diffs, but JFIN’s Track 1 contracts already define a baseline+manifest approach.
---

# Pytest Characterization Tests for JFIN Imaging

## Scope and intent

This skill is a **runbook** for adding **behavior-preserving tests** around JFIN’s imaging logic so refactors can proceed safely.

In JFIN Track 1, “behavior preservation” is enforced through:
- **Parity matrix rows** (e.g., `IMG-*`) that point to
- **Characterization baselines** and
- **Golden artifacts + manifest** (with governance checks validating linkage and budgets).  
See the Track 1 blueprint and WI-003 acceptance criteria for the required shape.  

## What this skill covers

Use this skill to add or update tests in:
- `tests/characterization/imaging_contract/` (baseline-driven contract assertions)
- `tests/golden/imaging/` (golden outputs + manifest linkage)

This skill specifically targets JFIN imaging behavior such as:
- scale plan decisions (`SCALE_UP`, `SCALE_DOWN`, `NO_SCALE`)
- logo padding policy (`add` / `remove` / `none`)
- cover-scale + crop behavior (thumb/backdrop/profile)
- EXIF orientation handling and transpose rules
- encoding outputs (PNG/JPEG/WebP) and key properties (mode, alpha preservation)

## What this skill does NOT cover

Do **not** use this skill for:
- CLI/config characterization (`CLI-*`, `CFG-*`)
- API safety write gates (`API-*`, `PIPE-*`, `RST-*`)
- Pipeline transaction semantics (backdrops, restore flows)
Those have separate suites and behavior IDs.

---

## Inputs and preconditions

Before writing tests, confirm:

1) **You’re changing imaging behavior or adjacent code**
   - Typical files: `src/jfin/imaging.py` and any helper it calls.

2) **You know which behavior IDs apply**
   - Imaging IDs are `IMG-*` in `project/parity-matrix.md`.

3) **You can run the governance gates locally**
   - You should be able to run:
     - `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/imaging_contract`
     - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization`

---

## Tools and permissions

- Preferred: `pytest` + pure-Python/Pillow fixtures.
- **Hard rule:** imaging characterization tests must not import `jfin.pipeline` or `jfin.client`.
  - Keep the seam at imaging helpers only; these tests exist to prevent IO-coupled brittleness.

- Network is not required; avoid live Jellyfin calls.

---

## Workflow

### 1) Identify the contract surface you must preserve

**Goal:** decide what to lock down *before* refactoring.

Do this:
- Locate relevant parity rows for imaging:
  - `project/parity-matrix.md` `IMG-*` rows should point to
    - `tests/characterization/baselines/imaging_contract_baseline.json#IMG-...`
    - and an owner test in `tests/characterization/imaging_contract/`.
- Identify the exact behavior you might perturb:
  - scale planning thresholds
  - crop anchors / rounding rules
  - padding removal sensitivity
  - encoding parameters (quality/progressive/optimize) and alpha handling
  - EXIF orientation edge cases

**Expected output:** a short list of 1–3 `IMG-*` behaviors that your change could affect.

---

### 2) Prefer “decision + properties” over “exact bytes” (unless stabilized)

**Goal:** make tests stable across environments while still catching real regressions.

Use these assertion layers in order:

1) **Decisions (most stable)**
   - The scale decision (`SCALE_UP`, `SCALE_DOWN`, `NO_SCALE`)
   - Chosen target dimensions
   - Chosen output format (PNG/JPEG/WebP)

2) **Image properties (stable)**
   - `(width, height)`
   - mode (`RGB`, `RGBA`, `P`)
   - alpha preserved where expected
   - EXIF applied (orientation-correct result dimensions)

3) **Content-sensitive checks (use sparingly)**
   - pixel-level comparisons only with explicit tolerance strategy
   - for lossy outputs, use tolerant comparisons (or compare deterministic intermediate representations)

**Avoid:** asserting full encoded bytes for JPEG/WebP unless you have a tolerant strategy and version-aware baselines.

(Background: snapshot/approval testing is powerful, but UX and stability depend on what you snapshot and how you review diffs.) :contentReference[oaicite:4]{index=4}

---

### 3) Build a representative image corpus (synthetic + “real-ish”)

**Goal:** cover the edge cases JFIN actually sees without turning tests into a brittle zoo.

Use a hybrid corpus:
- **Synthetic fixtures**: generated in-memory with Pillow for deterministic shapes/modes:
  - RGBA logos with transparent borders
  - palette (`P`) logos
  - extreme aspect ratios (very wide, very tall)
  - tiny images below target size (to test no-upscale / upscale policy)
- **Real-ish fixtures**: curated samples stored under `tests/golden/imaging/fixtures/realish/`
  - Ensure provenance rules are followed (don’t add random scraped images without policy).

**Expected output:** fixtures that directly map to your chosen behavior IDs and their baseline entries.

---

### 4) Write (or extend) baseline-driven characterization tests

**Goal:** tests read like “this is what the system does today.”

Pattern:
- Load the baseline JSON entry for the behavior ID.
- Run the imaging function(s) under test.
- Assert:
  - the baseline’s expected decision fields
  - key properties (format/mode/dimensions)
  - the linked `golden_key` (if the baseline schema includes it)

Keep each test narrowly focused:
- one test per behavior ID (or per small cluster when explicitly justified)

**Expected output:** a failing test if the behavior drifts from baseline.

---

### 5) Add/refresh golden artifacts only where they add signal

**Goal:** keep goldens meaningful and within governance budgets.

Use goldens for:
- logo padding visual outcome
- crop framing (thumb/backdrop/profile) when decision/properties aren’t enough
- WebP/JPEG outputs where a tolerant validation is implemented

Make sure:
- `tests/golden/imaging/manifest.json` includes required metadata (python/pillow versions, generated_at)
- expected artifact paths resolve
- artifact budgets remain within governance limits

**Expected output:** golden artifacts that are reviewable and stable enough to matter.

---

### 6) Verification checklist (must pass before declaring success)

Run:

- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/imaging_contract`
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization`
- (Recommended gate) `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`

Confirm:
- No new imports from forbidden modules in imaging characterization tests
- Baseline links and parity matrix anchors resolve
- Golden manifest entries resolve and budgets pass

---

## Completion criteria

You are done when:

- The relevant `IMG-*` parity rows still report “matches-baseline / preserved”
- Imaging characterization tests pass and cover the behavior you’re about to refactor
- Governance characterization checks pass (linkage + budgets)
- The tests are stable enough that a rerun without code changes does not flap

---

## Troubleshooting

### Symptom: Golden tests fail on another machine/CI but pass locally
Likely causes:
- Pillow version differences affecting encoder output or color conversion
- platform-dependent codec behavior (especially WebP)  
Recovery:
- Ensure manifest captures versions and tests either:
  - compare normalized intermediate representations, or
  - use tolerant pixel diff logic for lossy formats
- If the harness is intended to be strict, pin Pillow (and document it)

### Symptom: “NO_SCALE” cases unexpectedly upload/encode
Likely causes:
- `force_upload_noscale` behavior in other layers bleeding into your expectations  
Recovery:
- Keep characterization here at the imaging helper seam only
- If you need write-path semantics, that’s a safety/pipeline contract, not imaging

### Symptom: Padding removal behaves like a no-op on “obvious” transparent borders
Likely causes:
- sensitivity threshold too low/high; low-alpha pixels treated as content  
Recovery:
- Add a synthetic fixture that includes near-transparent border pixels
- Characterize the threshold behavior explicitly

---

## Examples

### Prompts that SHOULD trigger this skill
- “I’m refactoring `src/jfin/imaging.py` and need goldens/characterization first.”
- “We changed logo padding rules — add tests that preserve current behavior.”
- “EXIF orientation handling might change; lock it down with imaging contracts.”

### Prompts that SHOULD NOT trigger this skill
- “The CLI flag parsing changed; add characterization for that.” (CLI/config skill)
- “Dry-run allowed a POST; add safety tests.” (safety contract skill)
- “Backdrop delete/upload transaction changed.” (pipeline/workflow characterization)

---

## References and resources (JFIN)

- `project/parity-matrix.md` — find `IMG-*` rows and owner tests.
- `tests/characterization/baselines/imaging_contract_baseline.json` — baseline source for imaging behaviors.
- `tests/characterization/imaging_contract/` — baseline-driven characterization tests.
- `tests/golden/imaging/manifest.json` — golden manifest + metadata/version capture.
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization` — linkage + budget validation.

---

## Changelog

- 2026-03-04 (v2.0.0): Rebuilt as a Track 1 runbook: baseline-driven IMG contracts + golden harness,
  explicit non-goals, verification gates, and stability guidance.
