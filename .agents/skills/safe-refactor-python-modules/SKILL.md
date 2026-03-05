---
name: safe-refactor-python-modules
description: Refactor Python code incrementally while preserving observable behavior. Use when splitting files, extracting helpers, reorganizing modules/packages, or untangling responsibilities without changing user-facing behavior. Not for feature work or behavior changes. Includes test-first safety nets, slicing rules, verification gates, and stop conditions to prevent big-bang rewrites.
metadata:
  version: "2.0.0"
  updated: "2026-03-04"
  owners:
    - "@codex"
    - "@alexkahler"
compatibility: Assumes a Python repo with a runnable test command (pytest/unittest/nox/tox/etc.) and git. Works best when you can run focused tests locally. Network access is not required.
---

# Safe Refactoring for Python Modules (Incremental, Behavior-Preserving)

## Scope and intent

A refactor is a **structural change without observable behavior change**.  
This skill is a runbook for doing that safely in real repos—especially when code is large, coupled, or lightly tested.

### Don't use this skill when
- You intend to change outputs, side effects, CLI/API behavior, or defaults (do that as a **separate** change/PR).
- You cannot define any verification path (tests, checks, or a reproducible manual script).
- You're doing a rewrite "for clarity".

---

## Inputs and preconditions

Before editing code, you MUST identify:

1) **Target and motivation**
- Which module(s) or package(s) are being refactored?
- Why now? (size, coupling, testability, architecture boundary, readability, performance risk mitigation)

2) **Observable behavior ("public surface")**
Pick the relevant surfaces:
- Public Python API: exported functions/classes, stable module paths, documented behavior
- CLI flags/commands (if any)
- External integration behavior (HTTP calls, filesystem writes, DB mutations)
- Output formats (JSON schema, image bytes, logs-as-contract, etc.)
- Error behavior: exception types/messages (only if relied upon), exit codes

3) **Verification command(s)**
At minimum:
- A fast, repeatable test/check command you can run after each slice
- A fuller "gate" command to run before declaring done

> If you can't name these commands, STOP and switch to a planning skill/work item (plan + gates + rollback).

---

## Tools and safety posture

### Safety rules
- Treat refactoring like surgery: **one slice at a time**, verify after each slice.
- Avoid broad formatting churn (it hides semantic changes and complicates review).
- Prefer mechanical changes that are easy to validate (move/extract/rename in small steps).

### Security note
Refactors can accidentally broaden permissions or tool use (e.g., new filesystem writes or new network paths).  
If your refactor touches I/O boundaries, add explicit tests around those boundaries first.

---

## Workflow (do this in order)

### 1) Map the surface and invariants (no edits yet)
**Goal:** write down what must not change.

- List entry points (functions/classes/modules) and key side effects.
- List invariants (examples):
  - "Function X returns a dict with keys A/B/C"
  - "Module Y never writes to disk unless `dry_run=False`"
  - "HTTP POST is never retried"
- Identify coupling hotspots (imports, circular deps, high fan-in/out).

**Expected output:** a short bullet list you can paste into the PR description as "Behavior preserved".

---

### 2) Lock behavior with tests (test-first safety net)
**Goal:** create an oracle so you can prove behavior didn't change.

Decision rule:
- If behavior is clear and unit-testable → write/extend unit tests.
- If behavior is unclear/legacy/implicit → add **characterization tests** (golden master / approval style).

**Guidelines for characterization tests**
- Prefer asserting stable properties over full byte-for-byte snapshots.
- Stabilize non-determinism (timestamps, random IDs, ordering) before snapshotting.

**Expected output:** tests that fail if behavior changes unintentionally.

---

### 3) Choose a refactor strategy (pick one)
Pick the smallest strategy that works:

A) **Pure extraction** (lowest risk)  
- Extract helper functions/classes without changing call behavior.

B) **Module split** (medium risk)  
- Split one module into multiple files but keep the public import paths stable via re-exports.

C) **Boundary fencing (adapter/abstraction)** (higher risk, best for large changes)  
- Introduce an interface/adapter so old and new structures can coexist.
- This is aligned with "Branch by Abstraction" for gradual, releasable change.

D) **Strangler-style migration** (system-level refactor)  
- Gradually route calls to new code while legacy shrinks (often needs a façade/router).

**Decision rule:** If you are touching many callers or package boundaries, prefer C or D.

---

### 4) Execute in slices (one objective per slice)
A "slice" is a single mechanical step you can verify quickly.

**Slice rules**
- One extraction/move per slice (e.g., "extract helper", "move type to new module", "introduce adapter").
- No mixing with drive-by cleanup (rename variables later; delete dead code later).
- Keep signatures stable when possible; if not, add adapters instead of changing all callers at once.

**After each slice**
1) Run the smallest relevant verification command(s).
2) If it fails: STOP, fix, re-run until green.
3) Commit (or at least checkpoint) before the next slice.

**Expected output:** a sequence of small, reviewable diffs that stay green.

---

### 5) Preserve import stability (Python-specific hazards)
Refactors often break consumers via import path changes.

Use these patterns:
- Keep original module path exporting the same symbols (re-export from new modules).
- If renaming/moving modules, update __init__.py carefully and add tests that import the public surface.
- Avoid creating circular imports; if you hit one, resolve via:
  - local imports (only when safe),
  - dependency inversion (interfaces),
  - extracting shared types to a neutral module.

---

### 6) Cleanup (only after stable structure + green tests)
Now you can:
- Remove dead code (backed by tests).
- Do small renames to improve clarity (avoid repo-wide renames).
- Consolidate duplicated logic that the refactor exposed.

**Expected output:** reduced complexity without hidden behavior change.

---

## Verification checklist (must complete before "done")

- [ ] Public surface identified (what users/callers depend on)
- [ ] Tests exist that would catch accidental behavior change
- [ ] Each slice was verified (fast checks)
- [ ] Full repo gates run before finalizing
- [ ] No new behavior/features mixed into the refactor
- [ ] Import paths and public symbols remain stable (or migration notes exist)

---

## Completion criteria

You may declare success only when:
- All verification passes,
- The refactor objective is achieved (split/extract/untangle),
- The public surface remains behavior-identical (or explicitly documented otherwise),
- The diff remains reviewable and scoped.

---

## Stop conditions (escalate / re-scope)

Stop and re-scope if any is true:
- You cannot define verification gates.
- You discover behavior must change to proceed (split into a separate change/PR).
- The diff balloons into a "rewrite" shape.
- The refactor spans many files without a boundary-fencing strategy (adapter/abstraction).

---

## Anti-patterns (common failure modes)

❌ "Big-bang rewrite" of a module for clarity  
❌ Mixed refactor + feature work  
❌ Moving logic across responsibility boundaries without tests  
❌ Mass formatting/renaming that hides semantic changes  
❌ Introducing new dependencies "to make it cleaner"  

---

## Examples (routing)

### SHOULD trigger this skill
- "Split this 1200-line Python module into smaller files without changing behavior."
- "Extract helpers and untangle responsibilities, but keep the public API identical."
- "Reorganize the package structure while preserving import paths and tests."

### SHOULD NOT trigger this skill
- "Refactor this to support a new feature / new CLI flag / different output."
- "Rewrite this module in a new style / framework."
- "Change defaults, retries, encoding, or error semantics while refactoring."

---

## References and resources

- Refactoring definition ("no observable behavior change") — Martin Fowler.
- Characterization tests (golden master) overview.
- Branch by Abstraction (gradual large-scale change).
- Strangler Fig pattern (incremental replacement).

## Changelog
- 2026-03-04 (v2.0.0): Generalized to be repo-agnostic, added test-first oracle,
  explicit strategy selection (extraction/split/abstraction/strangler),
  slice loop with mandatory verification, import-stability guidance, and clearer stop conditions.