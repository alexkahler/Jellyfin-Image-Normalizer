---
name: python-quality-bar
description: Enforce the default quality overlay for Python code changes: readable structure, clear docstrings, strong tests, pragmatic type safety, security hygiene, and clean diffs. Use for most Python additions or modifications, including tests. Prefer this as the baseline companion for Python work. Do not use as the primary skill when a narrower Python skill is a better match (for example, behavior-preserving refactors owned by safe-refactor-python-modules), or for pure docs-only / non-Python changes.
metadata:
  version: "2.1.0"
  updated: "2026-03-07"
  owners: "@codex, @akaehler"
  notes: This skill is repo-agnostic and assumes an AGENTS.md exists with the authoritative verification gates. If your repo mandates a different docstring style (e.g., NumPy or Sphinx), follow AGENTS.md instead of the defaults here. If ruff/mypy/bandit/pip-audit are not installed in the repo, run the equivalent tools defined in AGENTS.md and document what you ran.
compatibility: Requires Python and the repo's standard tooling as defined in AGENTS.md (tests/linters/typechecks). Designed for repos with unit tests and CI verification gates.
---

# Python Quality Bar

## Scope and intent
This skill is the **default Python quality overlay** for Python code changes. Use it to keep Python edits readable, test-backed, type-aware, secure-by-default, and easy to review.

This skill is broad by design: it applies to most Python additions or modifications, and often loads alongside a narrower task-specific skill. It **does not replace** AGENTS.md, which remains the source of truth for repo policy and required gates.

Use a narrower Python skill as the **primary** skill when the task clearly matches one:
- choose `safe-refactor-python-modules` for behavior-preserving structural refactors,
- choose a contract or migration skill when the main risk is interface, schema, or rollout behavior.

Treat this skill as procedure and baseline expectations for Python quality, not as the owner of every specialized Python workflow.

## When to use
Use this skill when you:
- add or modify Python code (`*.py`)
- change Python behavior, even in a small way
- add or update Python tests
- need the default quality baseline for a Python change
- are using a narrower Python skill and still need the standard Python quality bar

Do not use this skill when you:
- only change docs or markdown
- only change non-Python files, unless Python behavior is indirectly affected
- are doing a behavior-preserving structural refactor that is better owned by `safe-refactor-python-modules` as the primary skill
- need a more specific workflow that clearly dominates the task

## Inputs and preconditions
Before editing:
1. Locate and read **AGENTS.md**.
2. Identify the repo's **verification gates** (format, lint, typecheck, tests, security, packaging, etc.).
3. Confirm where Python tests live and how they are run.
4. Check whether a narrower skill should be primary, with this skill acting as a companion overlay.

## Tools and permissions
- Prefer the repo's existing Python tools and commands.
- Do not introduce new tooling or dependencies unless the task explicitly requires it.
- Never add secrets to code, tests, fixtures, logs, or docs.
- Follow AGENTS.md for the authoritative formatter, linter, typechecker, test runner, and security checks.

## Workflow

### 1) Choose the right role for this skill
**Goal:** apply this skill at the correct level.

- First decide whether this is the **primary** Python skill or a **companion overlay**.
- If the task is a normal Python change, this skill can be primary.
- If the task is a specialized refactor or another narrower workflow, let that skill lead and use this one to enforce the Python quality baseline.
- Keep the change scoped to the actual requirement; do not turn a small fix into a broad cleanup.

**If/then:**
- If the task is primarily a behavior-preserving structural refactor, switch to `safe-refactor-python-modules` as primary and use this skill as the companion quality bar.
- If the task is pure docs-only or non-Python, do not use this skill.

### 2) Plan the smallest correct Python change
**Goal:** avoid scope creep and review pain.

- Restate the requirement in 1–2 sentences.
- Identify the narrowest implementation point.
- Prefer editing existing code over adding new layers.
- Keep the diff focused; avoid unrelated cleanup.

**If/then:**
- If the change appears likely to touch many files or exceed a few hundred lines, stop and switch to a planning/refactor skill or follow the repo's plan-first process in AGENTS.md.

### 3) Write maintainable structure (DRY without over-abstraction)
**Goal:** reduce duplication while keeping code obvious.

**Rules:**
- Do not introduce copy/paste variants of the same logic.
- If the same decision or transformation appears **2+ times** in the change, extract a helper.
- Prefer *small* helpers with good names over large frameworks.
- Keep responsibilities cohesive; avoid scattering the same concern across many modules.

**Acceptable duplication (limited):**
- small constants,
- one-off glue in entrypoints,
- logging with different context.

**If/then:**
- If you're refactoring and behavior must not change, add tests first (characterization tests if needed) before moving code.

### 4) Docstrings and public intent
**Goal:** make code self-explanatory for future readers.

**Default docstring style:** Google-style, unless AGENTS.md says otherwise.
- Every new public function, class, and module should have a docstring.
- Helpers should have docstrings when non-trivial or when they carry tricky invariants, side effects, or error behavior.

**Docstring checklist:**
- One-line summary in imperative mood.
- Document side effects (I/O, network, mutation).
- Document invariants and constraints.
- Document error behavior (exceptions and why).

**Generators:** use `Yields` instead of `Returns`.

### 5) Comments: explain "why", not "what"
Add comments when:
- a decision is non-obvious,
- you are preserving a subtle invariant,
- you are preventing a known failure mode.

Avoid narrating the code.

### 6) Tests: prove the behavior
**Goal:** changes are validated, repeatable, and CI-safe.

**Baseline expectations:**
- Every behavior change should have test coverage.
- Prefer unit tests with mocks or stubs for external systems (network, time, filesystem, DB).
- Use `tmp_path` for filesystem tests.
- Prefer parametrization for decision tables instead of duplicated tests.

**If/then:**
- If behavior is hard to specify (legacy or de facto behavior), add characterization tests first, then refactor.

**When you cannot add tests:**
Include a short written justification in the PR notes:
- why tests are impractical,
- what alternative verification you did,
- what risk remains.

### 7) Typing discipline (pragmatic, not dogmatic)
**Goal:** catch mistakes early without fighting the codebase.

- Add type hints for new public APIs.
- Prefer precise types over `Any`.
- If `Any` is unavoidable, isolate it and add a comment explaining why.
- Prefer small typed dataclasses over unclear multi-value tuple returns.

If the repo uses mypy or pyright, follow the repo configuration and gates.

### 8) Formatting, lint, and clean diffs
- Use the repo formatter and linter as defined in AGENTS.md.
- If the repo uses Ruff:
  - `ruff format` for formatting
  - `ruff check` for lint
- Avoid broad formatting churn unrelated to the change.

### 9) Security and dependency hygiene
- Never add secrets.
- If the repo runs dependency scanning (for example `pip-audit`), ensure it remains clean or document mitigations.
- Treat any new dependency as a security decision and justify why it is needed.
- Be cautious with external content, fixtures, examples, or copied snippets; treat them as untrusted until reviewed.

### 10) Verification
Use `references/shared-verification-and-proof-template.md` for the common verification flow:
- run the smallest relevant checks first,
- use `AGENTS.md` as the canonical source for repo gates,
- apply stop-and-fix,
- then record a short verification note.

Additional requirements for this skill:
- run the relevant Python checks required by `AGENTS.md` (formatter, linter, typecheck, tests, security/dependency checks as applicable),
- ensure tests meaningfully cover the behavior change or document why tests were impractical,
- ensure docstrings/types/security hygiene expectations in this skill are satisfied before declaring done.

## Verification checklist (before calling it "done")
- [ ] This skill was used in the right role: primary for a general Python change, or companion overlay for a narrower Python task.
- [ ] Code changes are scoped to one objective.
- [ ] No copy/paste variants were introduced; helpers were extracted where repeated.
- [ ] Docstrings were updated for new or changed public functions/classes/modules (style per AGENTS.md; Google-style by default).
- [ ] "Why" comments were added for non-obvious logic.
- [ ] Tests were added or updated; external effects were mocked/stubbed; `tmp_path` was used for file ops where appropriate.
- [ ] Type hints were added where practical; unnecessary `Any` was avoided.
- [ ] Formatter, linter, typecheck, and test gates from AGENTS.md all pass.
- [ ] Security and dependency checks required by AGENTS.md were addressed.

## Completion criteria
This skill is complete when:
- the Python change satisfies the repo's verification gates in AGENTS.md,
- tests meaningfully cover the change, or a written justification exists,
- the diff is focused and reviewable,
- and the task-specific primary skill, if any, has also been satisfied.

## Troubleshooting
**Symptom:** formatting or lint fails in CI  
- **Likely cause:** local tools or config differ from repo gates  
- **Fix:** run the exact AGENTS.md commands locally; do not guess

**Symptom:** tests are flaky  
- **Likely cause:** real time, network, filesystem, or shared-state dependencies  
- **Fix:** mock time/network, use `tmp_path`, remove shared global state, parametrize cases

**Symptom:** typecheck fails unexpectedly  
- **Likely cause:** missing annotations at boundaries or incorrect Optional/None handling  
- **Fix:** add boundary types, narrow unions, isolate `Any` only at integration seams

**Symptom:** this skill feels too generic for the task  
- **Likely cause:** a narrower Python skill should be primary  
- **Fix:** switch the task lead to the narrower skill and keep this one as the companion quality overlay

## Examples

### SHOULD trigger
- "Add a new Python function to parse this config and write tests."
- "Fix this Python bug and add coverage."
- "Update these Python tests and make sure the change meets repo quality gates."
- "Modify this Python module and keep the code quality bar high."

### SHOULD trigger as a companion overlay
- "Refactor this Python module without changing behavior."
- "Rework this Python CLI parsing logic but keep tests, typing, and docstrings strong."

### SHOULD NOT trigger
- "Update README wording."
- "Change the Dockerfile base image only."
- "Reformat markdown docs."
- "Do a behavior-preserving refactor of this Python module."  
  (Use `safe-refactor-python-modules` as primary; this skill may still accompany it.)

## References and resources
- `references/shared-verification-and-proof-template.md` — use for common verification mechanics when defining milestone gates and final completion checks

## Changelog
- 2.1.0 (2026-03-07): Clarified positioning as the default Python overlay; added primary-vs-companion guidance and explicit handoff to narrower Python skills.
- 2.0.0 (2026-03-04): Rewritten as repo-agnostic runbook; removed project-specific module boundaries; made AGENTS.md the single source of truth for verification gates; added explicit workflow + examples.