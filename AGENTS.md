# AGENTS.md — JFIN (Jellyfin Image Normalizer)

> This file is **for coding agents and contributors** working inside this repository. It defines how to set up the dev environment, how to run quality gates, where the important code lives, and what “done” means for changes in this repo.  
> AGENTS.md is intended to be a repo-local “instructions for agents” file.

---

## Project snapshot

**JFIN** is a Python CLI that talks to the **Jellyfin HTTP API** to download artwork, normalize it with Pillow (in-memory), and upload it back safely (dry-run-first, optional backups/restores).

**Primary entrypoint**
- CLI: `python -m jfin` (implemented in `src/jfin/cli.py`).

**Core behavior**
- Modes: `logo`, `thumb`, `backdrop`, `profile`.
- Safe-by-default: generated config defaults to `dry_run = true`; POST/DELETE are blocked while dry-run is enabled.
- Backups/restores exist but are **not** “real Jellyfin backups” (UUID caveats apply).

---

## Repository layout (high-signal map)

- `src/jfin/` — main package:
  - `cli.py` — CLI parsing + dispatch.
  - `config.py` — TOML config loading/merging + runtime settings.
  - `client.py` — `JellyfinClient` HTTP layer, retry/backoff, dry-run write gates, upload/download.
  - `discovery.py` — library/item discovery via `/Library/MediaFolders` and `/Items`. 
  - `imaging.py` — resize planning + mode-specific image builders/encoders + EXIF handling.
  - `pipeline.py` — orchestration: discovery runs, single item/user runs, restore flows.
  - `backup.py` — backup path/content-type helpers and backup-mode rules.
  - `logging_utils.py`, `state.py` — logging and run stats/failure tracking.
- `tests/` — unit tests (mocked; no live Jellyfin required).
- `docs/` — deeper documentation (feature tour, cron/docker notes, backups caveats).

---

## Agent skills & internal docs

When you need API details or patterns:
- Jellyfin API skill: `.agents/skills/jellyfin-api/`
- Jellyfin API documentation: `.agents/skills/jellyfin-api/docs/`

Use these as **implementation references** (preferred over guessing endpoints/params).

---

## Environment & setup (required)

### Python + venv
- This repo uses a `.venv` environment (**required**).

From repo root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
````

### Dependencies

This repo currently documents installing dependencies via `requirements.txt`. 

```bash
python -m pip install -r requirements.txt
```

### Running locally

The docs assume module imports via `PYTHONPATH=src`. 

```bash
export PYTHONPATH=src
python -m jfin --help
```

---

## Coding standards (must-follow)

### Engineering quality bar (MUST)
- **Google Python Style Guide** required.
- **All functions MUST have docstrings.**
- **All non-trivial / complex code MUST be commented** (explain *why*, not just *what*).
- **All changes MUST include unit tests** (or a documented reason why a unit test is impossible and what alternative coverage is added).
- **All code MUST pass**:
  - `bandit` (security static analysis)
  - `pip-audit` (dependency vulnerability audit)
  - `ruff` (linter)
  - `mypy` (type check)
  - the repo’s formatter/linter/type checks (see below)
- **All code MUST have CI integration** (no “works locally only” changes).

### DiskGuard product principles (MUST)
- **Tag-truth model:** qBittorrent tags are the source of truth; **no local state file**.
- **No destructive behavior:** never delete torrents/files; never move data; never orchestrate *arr workflows.
- **Idempotent + concurrency-safe:** `/on-add` may race with the poll loop; actions must be safe under repetition.
- **Respect user overrides:** `forcedDL` is excluded from “downloading-ish” enforcement in v1.

### PRINCIPLES
- **Clarity over cleverness**: Write code that is easy to understand
- **Modularity**: Break down complex problems into smaller, manageable pieces
- **Documentation**: Always comment your code and explain your reasoning. Use Google Python Style Guide
- **Testing**: Consider testability in your solutions
- **Performance**: Write efficient code, but prioritize readability first

### CODE STYLE
- Use consistent naming conventions
- Keep functions small and focused
- Use meaningful variable and function names
- Add comments for complex logic

### BEST PRACTICES
- **DRY (Don't Repeat Yourself)**: Avoid code duplication
- **SOLID Principles**: Follow object-oriented design principles
- **Error Handling**: Always handle potential errors gracefully
- **Security**: Strongly and thoroughly consider security implications in your code
- **Version Control**: Write clear commit messages

### Type hints

* Add type hints for all public functions and non-trivial internal functions.
* Types must pass **mypy** (see “Quality gates”).

### Error handling & logs

* This CLI is operational tooling; failures must be actionable:

  * raise/exit with clear messages for invalid config/CLI combos
  * log enough context to debug (IDs, mode, image type), but **never** log secrets

---

## Safety rules (repo-specific)

### Dry-run and write gates

* Preserve the invariant: **no POST/DELETE when dry-run is enabled**.
* Any change that touches `client.py` write gating or pipeline upload/delete sequencing needs tests.

This is a core safety property of JFIN. 

### Backups are not disaster recovery

* Do not frame or implement JFIN backups as complete Jellyfin backups.
* UUID mismatch after rebuild is expected and must be documented if relevant.

See the explicit limitations doc. 

### API-only interaction

* JFIN’s intent is API-only discovery and operations (no “direct filesystem poking” as a primary mechanism).  

---

## Quality gates (mandatory before marking work complete)

All changes MUST pass:

### Formatting & lint

```bash
python -m ruff format .
python -m ruff check .
```

### Type checking

```bash
python -m mypy src
```

### Tests

```bash
export PYTHONPATH=src
python -m pytest
```

### Security scanning

```bash
python -m bandit -r src
python -m pip_audit
```

Notes:

* If the repo uses a config file for any of these tools (e.g., `config.toml`), follow it.
* If a tool isn’t currently configured in the repo, add configuration + CI wiring as part of the change that introduces the gate.

---

## CI requirements (mandatory for repo changes)

All code MUST have:

* CI integration that runs the quality gates above on every PR
* Unit tests for:

  * new behavior
  * bug fixes (regression tests)
  * any safety gating changes (dry-run/write gates, restore/delete logic)

Minimum CI jobs (expected):

* ruff (format/check)
* mypy
* pytest
* bandit
* pip-audit

---

## Testing rules of thumb (JFIN-specific)

Prefer **unit tests with mocks**:

* No live Jellyfin calls in unit tests; tests should mock `JellyfinClient` and/or HTTP calls. 
* Add tests when modifying:

  * resize planning decisions (`SCALE_UP` / `SCALE_DOWN` / `NO_SCALE`) 
  * logo padding modes (`add` / `remove` / `none`) 
  * backdrop multi-phase flow (stage → normalize → delete → re-upload → finalize) 
  * restore logic and backup path inference 

---

## Where to add things

* New CLI flags: `src/jfin/cli.py` + config merge/validation in `config.py`. 
* New modes:

  * update constants/mappings and mode wiring (see “Config Migration Notes” / “When adding a new image mode…”). 
  * implement imaging builder/encoder in `imaging.py` 
  * implement pipeline branch in `pipeline.py` 
  * add unit tests

---

## Definition of done

A change is “done” only when:

* Code follows Google Python Style Guide (docstrings + comments where needed)
* `ruff`, `mypy`, `pytest`, `bandit`, and `pip-audit` pass locally
* CI runs and passes all gates
* Tests cover the change (and include regressions for bug fixes)
* Any behavior change is reflected in docs if user-visible (README/docs)

---

## Reference docs (in-repo)

* Technical internals: `docs/TECHNICAL_NOTES.md` 
* Feature overview: `docs/feature-tour.md` 
* Cron & Docker notes: `docs/docker-and-cron.md` 
* Backup/UUID caveats: `docs/backups-and-uuids.md` 
* Advanced CLI patterns: `docs/advanced-usage.md` 
