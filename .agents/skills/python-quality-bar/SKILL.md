---
name: python-quality-bar
description: Enforce a high, consistent quality bar for any Python code change: clear docstrings, maintainable structure (no copy/paste logic), strong tests, type-safety, security hygiene, and clean diffs. Use when adding/modifying Python code or tests. Don't use for pure docs-only PRs or non-Python changes. Includes a JFIN addendum (module boundaries + imaging/Jellyfin invariants) when working in that repo.
metadata:
  version: "2.1.0"
  updated: "2026-03-04"
  owners:
    - "@codex"
    - "@alexkahler"
  notes: AGENTS.md is the authoritative source of repo verification gates. This skill is the procedure to meet that bar. If your repo mandates a different docstring style (e.g., NumPy or Sphinx), follow AGENTS.md instead of the defaults here. If ruff/mypy/bandit/pip-audit are not installed in the repo, run the equivalent tools defined in AGENTS.md and document what you ran.
compatibility: Requires Python and the repo's standard tooling as defined in AGENTS.md (tests/linters/typechecks). Designed for repos with unit tests and CI verification gates.
---

# Python Quality Bar

## Scope and intent
This skill is a **repeatable runbook** for producing Python changes that are:
- readable and reviewable,
- correct and tested,
- type-safe where practical,
- secure by default,
- consistent with repo gates and CI.

This skill **does not replace** AGENTS.md. Treat AGENTS.md as policy ("must pass gates"),
and this skill as procedure ("how to meet the bar").

## When to use
Use this skill when you:
- add or modify Python code (`*.py`)
- change behavior (even small behavior)
- refactor Python code
- add or update tests

Do not use when you:
- only change docs/markdown
- only change non-Python files (unless Python behavior is indirectly affected)

## Inputs and preconditions
Before editing:
1) Locate and read **AGENTS.md**.
2) Identify the repo's **verification gates** (format/lint/typecheck/test/security, etc.).
3) Confirm where tests live and how they're run.
4) If this is the **JFIN** repo, read the **JFIN addendum** in this document and follow its module boundaries and invariants.

## Tools and permissions
- Prefer the repo's existing tools and commands.
- Do not introduce new tooling or dependencies unless the task explicitly requires it.
- Never add secrets to code, tests, fixtures, logs, or docs.

## Workflow

### 1) Plan the smallest correct change
**Goal:** avoid scope creep and review pain.

- Restate the requirement in 1–2 sentences.
- Identify the narrowest implementation point (prefer editing existing code over new layers).
- Keep the diff focused: no "while I'm here" refactors.

**If/then:**
- If the change looks like it will touch many files or exceed a few hundred lines, stop and switch to a planning/refactor skill (or follow the repo's "plan first" process in AGENTS.md).

### 2) Write maintainable structure (DRY without over-abstraction)
**Goal:** reduce duplication while keeping code obvious.

**Rules:**
- Do not introduce copy/paste variants of the same logic.
- If the same decision/transformation appears **2+ times** in the change, extract a helper.
- Prefer *small* helpers with good names over big frameworks.
- Keep responsibilities cohesive: avoid scattering the same concern across many modules.

**Acceptable duplication (limited):**
- small constants,
- one-off glue in entrypoints,
- logging with different context.

**If/then:**
- If you're refactoring and behavior must not change, add tests first (characterization tests if needed) before moving code.

### 3) Docstrings and public intent
**Goal:** make code self-explanatory for future readers.

**Default docstring style:** Google-style (unless AGENTS.md specifies otherwise).
- Every new public function/class/module should have a docstring.
- Helpers: docstring if non-trivial or if it has tricky invariants/side effects.

**Docstring checklist:**
- One-line summary (imperative mood).
- Document side effects (I/O, network, mutation).
- Document invariants and constraints (especially safety/compatibility rules).
- Document error behavior (exceptions and why).

**Generators:** use `Yields` instead of `Returns`.

**If/then:**
- If this is **JFIN**, docstrings are stricter: **every function must have a docstring**, including helpers (see JFIN addendum).

### 4) Comments: explain "why", not "what"
Add comments when:
- a decision is non-obvious,
- you're preserving a subtle invariant,
- you're preventing a known failure mode.

Avoid narrating the code.

### 5) Tests: prove the behavior
**Goal:** changes are validated, repeatable, and CI-safe.

**Baseline expectations:**
- Every behavior change should have test coverage.
- Prefer unit tests with mocks/stubs for external systems (network, time, filesystem, DB).
- Use `tmp_path` for filesystem tests.
- Prefer parametrization for decision tables instead of duplicated tests.

**If/then:**
- If behavior is hard to specify (legacy / de facto behavior), add characterization tests first, then refactor.

**When you cannot add tests:**
- Include a short written justification in the PR notes:
  - why tests are impractical,
  - what alternative verification you did (commands, targeted manual checks),
  - what risk remains.

### 6) Typing discipline (pragmatic, not dogmatic)
**Goal:** catch mistakes early without fighting the codebase.

- Add type hints for new public APIs.
- Prefer precise types over `Any`.
- If `Any` is unavoidable, isolate it and add a comment explaining why.
- Prefer small typed dataclasses over "tuple soup" for multi-value returns.

(If the repo uses mypy/pyright, follow the repo configuration and gates.)

### 7) Formatting, lint, and clean diffs
- Use the repo formatter and linter as defined in AGENTS.md.
- If the repo uses Ruff:
  - `ruff format` for formatting.
  - `ruff check` for lint.
- Avoid broad formatting churn unrelated to the change.

### 8) Security and dependency hygiene
- Never add secrets.
- If the repo runs dependency scanning (e.g., pip-audit), ensure it remains clean or document mitigations.
- Treat any new dependency as a security decision: justify why it's needed.

### 9) Verification (must match AGENTS.md)
**Run the smallest relevant checks first**, then the full verification gates listed in **AGENTS.md**.
Do not invent a new gate list in this skill—AGENTS.md is the source of truth.

**Stop-and-fix rule:**
- If any gate fails, fix it before continuing.

## JFIN addendum: repo-specific invariants (apply only in JFIN)

### A) Module responsibility boundaries (do not duplicate concerns)
These boundaries exist to prevent subtle regressions and repeated logic.

- HTTP request semantics belong in `client.py` (do not scatter HTTP logic across pipeline/CLI).
- Resize planning/transform logic belongs in `resize.py` (do not reimplement resize decisions elsewhere).
- CLI parsing belongs in `cli.py`; config schema/validation belongs in `config.py`.

**If/then:**
- If your change appears to cross these boundaries, refactor so the *owning module* provides the helper/API, then call it from the other layer.

### B) DRY and extraction rules (JFIN strict)
- If the same transformation/decision appears **2+ times** in your change, extract a helper.
- Avoid "DRY by framework": prefer small helpers and clear names.
- Avoid re-implementing resize logic or validation in multiple modules.

**Extract a helper when:**
- the same conditional or transformation appears more than once,
- the same decision logic appears in multiple branches,
- a block exceeds ~20–30 lines and mixes concerns,
- tests require duplicated setup.

**Refactoring rule (JFIN):**
- Preserve function signatures when possible.
- Add tests before moving behavior (characterization tests if behavior is hard to specify).
- Do not mix extraction with unrelated changes.

### C) Docstrings (JFIN strict Google-style)
In JFIN:
- **Every function must have a docstring** (including helpers).
- Docstrings must mention side effects, invariants (especially dry-run write gating), and error behavior.

**Template:**
```python
def foo(bar: str, *, dry_run: bool) -> int:
    """One-line summary in imperative mood.

    More details if needed. Include invariants and edge cases.

    Args:
        bar: What it is and valid forms.
        dry_run: True means no write operations will occur.

    Returns:
        What the function returns.

    Raises:
        ValueError: When input is invalid.
    """
```

**Generators:** use `Yields` instead of `Returns`.

### D) Comments: preserve safety decisions
Add "why" comments for:
- Jellyfin API behavior quirks,
- retry and idempotency decisions,
- image format/mode constraints,
- any safety gate (dry-run, write gating, destructive actions).

Example:
```python
# We intentionally avoid retrying POST/DELETE to prevent duplicate writes if the
# connection drops after the server has processed the request.
```

### E) Tests (JFIN): unit-first, mock-first
- Unit tests must not require a live Jellyfin server.
- Mock the client layer (e.g., `JellyfinClient`) or the underlying HTTP transport.
- Use `tmp_path` for file I/O.
- Prefer parametrized decision tables for mode/shape/size cases.

**Characterization tests for imaging changes**
If behavior is "de facto spec" and hard to articulate, lock it in with characterization tests:
- assert dimensions,
- assert format/mode,
- assert the scale decision (`SCALE_UP` / `SCALE_DOWN` / `NO_SCALE`),
- avoid byte-for-byte snapshots unless encoding is deterministic.

**Minimum tests to add when changing…**
- Resize logic: decision coverage for each branch.
- Logo padding: `add` / `remove` / `none` cases.
- Backdrop pipeline: multi-phase flow remains safe and idempotent.
- Dry-run/write gating: POST/DELETE never happen in dry-run.

### F) Typing (JFIN): keep integration seams explicit
- Type hints required for new functions and public APIs.
- Prefer precise return types; avoid `Any` unless unavoidable.
- If you must use `Any`, isolate it at integration seams and document why.
- Prefer small typed dataclasses for multi-value returns.

### G) Formatting/lint/security (JFIN expectations, unless AGENTS.md says otherwise)
- Prefer Ruff for format (`ruff format`) and lint (`ruff check`) if present.
- Run security/dependency checks defined in AGENTS.md. Common JFIN expectations are:
  - `bandit` for static security checks,
  - `pip-audit` for dependency vulnerabilities.
If these tools are not in the repo, do not add them unless required—follow AGENTS.md.

## Verification checklist (before calling it "done")
- [ ] Code changes are scoped to one objective.
- [ ] No copy/paste variants introduced; helpers extracted where repeated.
- [ ] Docstrings updated for new/changed public functions/classes (style per AGENTS.md; Google-style by default; **JFIN: every function**).
- [ ] "Why" comments added for non-obvious logic and safety decisions.
- [ ] Tests added/updated; external effects mocked/stubbed; `tmp_path` used for file ops.
- [ ] Type hints added where practical; no unnecessary `Any`.
- [ ] Formatter/linter/typecheck/test gates from AGENTS.md all pass.
- [ ] Security/dependency checks (if present in AGENTS.md) are addressed.
- [ ] **JFIN only:** module boundaries respected (`client.py`/`resize.py`/`cli.py`/`config.py`) and dry-run invariant preserved.

## Completion criteria
This skill is complete when:
- the PR satisfies the repo's verification gates (AGENTS.md),
- tests meaningfully cover the change (or a justification exists),
- the diff is reviewable and focused.

## Troubleshooting
**Symptom:** formatting/lint fails in CI
- Likely cause: local tools/config differ from repo gates.
- Fix: run the exact AGENTS.md commands locally; don't guess.

**Symptom:** tests are flaky
- Likely cause: real time/network/filesystem dependencies.
- Fix: mock time/network; use `tmp_path`; remove global shared state; parametrize cases.

**Symptom:** typecheck fails unexpectedly
- Likely cause: missing annotations at boundary or incorrect Optional/None handling.
- Fix: add boundary types; narrow unions; isolate `Any` only at integration seams.

**Symptom (JFIN): imaging test is brittle**
- Likely cause: asserting exact bytes for encoded images.
- Fix: assert invariants (dimensions/mode/decision) instead of bytes unless encoding is deterministic.

## Examples

### SHOULD trigger
- "Add a new function to parse this config and write tests."
- "Refactor this module to remove duplication without changing behavior."
- "Fix this bug and add coverage."
- (JFIN) "Change resize planning and add decision-table tests for each branch."

### SHOULD NOT trigger
- "Update README wording."
- "Change Dockerfile base image only."
- "Reformat markdown docs."

## Changelog
- 2.1.0 (2026-03-04): Added JFIN addendum (module boundaries, strict docstrings, mock-first Jellyfin tests, imaging characterization guidance, dry-run/write-gating invariants) while preserving repo-agnostic workflow and AGENTS.md-as-policy structure.
- 2.0.0 (2026-03-04): Rewritten as repo-agnostic runbook; removed project-specific module boundaries; made AGENTS.md the single source of truth for verification gates; added explicit workflow + examples.

## References (non-normative; follow AGENTS.md when it conflicts)
```text
Google Python Style Guide (docstrings and conventions)
pytest tmp_path documentation
Ruff formatter documentation
Python typing documentation
mypy documentation
```
