---
name: verification-gates-and-diff-discipline
description: Enforce small, reviewable diffs and a verification-first workflow (targeted tests -> full gates -> report). Use after any code change or when a diff starts to grow. Stop-and-fix on failures. Not for designing new test suites or defining repo-specific commands (this skill finds and follows the repo's existing gate list).
metadata:
  version: "2.0.0"
  updated: "2026-03-04"
  owners:
    - "@codex"
    - "@akaehler"
  notes: Review LOC thresholds and decision rules to fit your repo's norms. Ensure you have access to the repo's gate documentation before using.
---

# Verification Gates + Diff Discipline (Portable)

## Scope and intent

This skill is a **portable "work contract"** for making changes safely:
- keep diffs small and scoped,
- run the **smallest relevant verification first**,
- escalate to **full repo gates** before calling work done,
- use a strict **stop-and-fix loop** when anything fails.

**Non-goals**
- Defining what your repo's gates *are* (this skill discovers them).
- Replacing project policy files like `AGENTS.md` / `CONTRIBUTING.md`.
- Performing big-bang rewrites or combining refactors with feature changes.

## When to use

Use this skill when:
- you changed code (even "small" edits),
- the diff is growing,
- you touched behavior-critical surfaces (APIs, config/CLI, auth, data migration, build tooling),
- you're refactoring and must preserve behavior.

Do NOT use when:
- you are only writing a plan (use your planning skill/runbook),
- you are defining new CI pipelines or inventing new gate commands from scratch.

## Inputs and preconditions

You need:
- a clean understanding of **what files changed** and **why**,
- the ability to run at least some verification locally or via CI,
- access to the repo's canonical gate list (this skill will locate it).

## Tools and permissions

Allowed actions:
- read files, run repo commands/tests, edit code/tests/docs.

Safety rules:
- If a command is destructive (writes, migrations, deployments), do NOT run it automatically.
- Do not exfiltrate secrets or print sensitive env vars in logs.

## Workflow

### 1) State the diff intent (required, before running anything)
Produce 3–7 bullets:
- what changed (behavior vs refactor),
- where (paths/modules),
- why (user-visible need / bug / safety / cleanup),
- expected blast radius.

**If you cannot say this clearly, stop.** Your scope isn't tight enough.

---

### 2) Check diff size + scope and decide whether to slice
Compute (roughly is fine):
- changed files count,
- approximate changed lines (or `git diff --stat`),
- net new LOC (exclude tests/docs if you can).

**Decision rules**
- If the change is **one objective** and reviewable: continue.
- If the change mixes objectives ("while I'm here…"): split it.
- If you are both refactoring and changing behavior: split it unless explicitly required.

**Suggested thresholds (portable defaults)**
- If diff is > ~300 changed lines OR spans many directories: propose slicing into PR-sized steps.
- If net new code > ~150 LOC (excluding tests/docs): justify why it must be that large, and propose a smaller alternative.

(These are heuristics; follow repo policy if it defines stricter limits.)

---

### 3) Discover the repo's verification gates (do not guess)
Find the repo's canonical commands in **this order**:

1) `AGENTS.md` (or nested agent instructions)
2) `CONTRIBUTING.md`
3) `README.md` / `docs/` "Development" section
4) Task runners: `Makefile`, `justfile`, `package.json`, `pyproject.toml` scripts, `taskfile.yml`, etc.
5) CI config: `.github/workflows/*`, `.gitlab-ci.yml`, etc.

**Output requirement:** quote (or list) the exact commands you will run, with where you found them.

If you can't find any gate list:
- run the smallest "standard" command you can infer (e.g., unit tests), but
- explicitly say "Repo gate list not found" and recommend adding one (outside this task's scope).

---

### 4) Run the smallest relevant verification first (targeted)
Start with the narrowest checks that cover the changed area.

**Decision rules**
- If only docs changed: run repo doc checks (if any) + link checker if present.
- If tests changed: run just the impacted test module(s) first.
- If a subsystem has dedicated tests (e.g., "api", "cli", "db", "ui"): run those before the full suite.

**Stop-and-fix rule**
- If any targeted check fails: stop, fix, re-run the same targeted check until green.

Record:
- command(s),
- result (pass/fail),
- brief note if you had to fix something.

---

### 5) Run full verification gates (before declaring success)
Run the repo's full gate list (format/lint/typecheck/tests/build/etc.) exactly as defined by the repo.

**Stop-and-fix rule (again)**
- Any failure → stop → fix → rerun the failing gate(s) until green.
- Do not continue adding changes while gates are red.

If full gates are too expensive:
- run them once per "slice," and rely on targeted checks during development,
- but you still must run full gates before finalizing.

---

### 6) Produce a "How I verified" report (required output)
Include:

- **Diff intent summary** (from Step 1)
- **Scope stats**
  - files changed:
  - approximate diff size:
  - net new LOC (exclude tests/docs):
- **Verification commands run**
  - targeted:
  - full gates:
- **Results**
  - what failed (if anything) and how it was fixed
- **Behavior statement**
  - "Behavior preserved" OR "Behavior changed" (with a short description and where documented)

---

## Verification checklist (must be true to finish)
- [ ] Diff is scoped to one objective (or explicitly sliced)
- [ ] No mixed refactor + feature change (unless explicitly required)
- [ ] Targeted verification ran first and is green
- [ ] Full repo gates ran and are green (or repo policy explicitly allows CI-only)
- [ ] "How I verified" report written with exact commands and results
- [ ] Any public interface change has docs/tests updated (as required by the repo)

## Completion criteria
You may declare completion only when:
- required gates are green, and
- the "How I verified" report is included, and
- scope discipline is satisfied (or a slicing plan is provided).

## Troubleshooting

### Symptom: "I don't know what commands to run."
Likely cause: repo doesn't document gates clearly, or you didn't look in the right places.
Recovery:
- search `AGENTS.md`, `CONTRIBUTING.md`, `Makefile`, `package.json`, CI workflows.
- if still missing, run the narrowest unit tests you can, and recommend adding a canonical "Verification gates" section later.

### Symptom: Full suite is slow, I keep breaking it late.
Likely cause: skipping targeted checks or slicing too coarsely.
Recovery:
- add/identify smaller "area tests" and run them first,
- slice the change into smaller PRs with independent verification.

### Symptom: The diff keeps ballooning.
Likely cause: scope creep ("while I'm here") or refactor/feature mixing.
Recovery:
- revert unrelated edits,
- split into "prep refactor" and "behavior change" slices,
- stop when >300 lines and propose a slicing plan.

## Examples

### SHOULD trigger
- "I refactored the module—what checks should I run before I open a PR?"
- "These changes touched the API client and config defaults; verify safely and keep the diff reviewable."
- "My PR grew to 500 lines; help me slice and run gates in the right order."

### SHOULD NOT trigger
- "Explain what unit tests are."
- "Design a CI pipeline from scratch."
- "Write a brand-new test strategy for this repo." (Use a testing/QA design skill instead.)

## References and resources (repo-local)
When present, treat these as authoritative:
- `AGENTS.md` / nested `AGENTS.md` — canonical verification gates + repo rules
- `CONTRIBUTING.md` — contributor workflow and required checks
- `Makefile` / `justfile` / `taskfile.yml` / `package.json` — runnable command registry
- `.github/workflows/*` (or equivalent CI) — source of truth for what CI runs

## Changelog
- 2.0.0 (2026-03-04): Rewrite to be repo-agnostic; adds gate discovery, explicit decision rules, and a required "How I verified" report.