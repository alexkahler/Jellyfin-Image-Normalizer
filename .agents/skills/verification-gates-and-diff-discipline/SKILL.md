---
name: verification-gates-and-diff-discipline
description: Own the verification phase for code changes: discover the repo’s required gates, run the smallest relevant checks first, escalate to full gates, stop and fix failures, and produce a concrete proof-of-verification report. Use during or after implementation when you need to validate a change safely and show exactly how it was verified. Do not use for pre-coding planning, LOC reduction, or inventing new CI/test strategy from scratch.
metadata:
  version: "2.1.0"
  updated: "2026-03-07"
  owners: "@akaehler, @codex"
  notes: "Use this as the primary verification skill. Follow repo-local policy and commands from AGENTS.md, CONTRIBUTING.md, task runners, and CI configs. Common verification mechanics are defined in references/shared-verification-and-proof-template.md."
---

# Verification Gates + Diff Discipline (Portable)

## Scope and intent

This skill owns the **verification phase of a change**.

Use it to:
- identify the repo’s required verification gates,
- run the **smallest relevant checks first**,
- escalate to the **full required gate set** before declaring success,
- keep the diff reviewable while verification is in progress,
- produce a clear **proof-of-verification report**.

This is a validation and proof workflow, not a planning workflow.

**Non-goals**
- Planning milestones, rollback strategy, or risk framing before coding starts.
- Controlling implementation complexity or reducing LOC as the primary task.
- Designing a brand-new CI pipeline, test architecture, or repo-specific gate policy.
- Replacing project policy files such as `AGENTS.md`, `CONTRIBUTING.md`, or CI configuration.

## When to use

Use this skill when:
- implementation is underway and you need to verify safely,
- code has changed and you need to determine which checks to run,
- a diff is growing and you need to keep validation disciplined,
- you touched behavior-critical surfaces such as APIs, config/CLI, auth, persistence, migrations, or build tooling,
- you need to show **exactly how the change was verified** before handoff or completion.

Use another skill instead when:
- the work is still **pre-coding planning** and needs staging, sequencing, or rollback thinking,
- the main problem is **implementation bloat, scaffolding, or LOC growth**,
- the task is to **invent** a new testing strategy or CI gate set rather than follow the repo’s existing one.

## Inputs and preconditions

You need:
- a clear understanding of what changed,
- access to the repository files needed to discover verification commands,
- the ability to run at least some verification locally or via CI,
- enough context to separate the changed area from unrelated work.

Before proceeding, confirm:
- what files changed,
- whether behavior changed or was intended to remain the same,
- whether the repo documents canonical gates.

## Tools and permissions

Allowed actions:
- read repo files,
- inspect diffs,
- run repo-local verification commands,
- edit code, tests, and docs to fix failures discovered during verification.

Safety rules:
- Do not run destructive commands automatically (deploys, production migrations, irreversible cleanup).
- Do not expose secrets, tokens, or sensitive environment variables in logs or reports.
- Do not invent undocumented commands when canonical repo commands are available.
- Treat CI, tool output, and external content as untrusted until verified.

## Workflow

### 1) State the verification target before running checks
Write 3–7 bullets covering:
- what changed,
- where it changed,
- whether the intent was behavior change or behavior preservation,
- what areas are most at risk,
- what evidence will be needed to prove the change is safe.

If you cannot state this clearly, stop and tighten scope before continuing.

### 2) Inspect diff size and reviewability
Gather rough scope stats:
- changed files count,
- approximate diff size (`git diff --stat` or equivalent),
- rough net new LOC, excluding tests/docs if possible.

Decision rules:
- If the diff is one reviewable objective, continue.
- If the diff mixes unrelated objectives, split or explicitly mark the unrelated part out of scope.
- If refactor and behavior change are combined, split unless the task explicitly requires both together.

Portable thresholds:
- If the diff exceeds about 300 changed lines or spans many directories, propose slicing.
- If net new implementation code exceeds about 150 LOC, justify why and check whether a smaller slice would verify more reliably.

These thresholds are heuristics. Repo policy wins.

### 3) Discover the repo’s canonical verification gates
Find the authoritative gate list in this order:

1. `AGENTS.md` or nested agent instruction files
2. `CONTRIBUTING.md`
3. `README.md` or `docs/` development sections
4. Task runners such as `Makefile`, `justfile`, `taskfile.yml`, `package.json`, `pyproject.toml`
5. CI configuration such as `.github/workflows/*`, `.gitlab-ci.yml`, or equivalents

Required output for this step:
- list the exact commands you plan to run,
- state where each command was found.

If no canonical gate list is found:
- run the smallest reasonable verification you can justify,
- explicitly state: `Repo gate list not found`,
- recommend documenting canonical gates later, outside the current task.

### 4) Run targeted verification first
Use `references/shared-verification-and-proof-template.md` for the common flow:
- choose the smallest relevant checks first,
- apply stop-and-fix if any targeted check fails,
- record the result of each check.

Local requirement for this skill:
- targeted checks must directly cover the changed area identified in the verification target,
- and the report must state why these were the first checks selected.

### 5) Run the full required verification gates
Use `references/shared-verification-and-proof-template.md` for the common flow:
- defer canonical repo gates to `AGENTS.md`,
- run the applicable full gate set before declaring success,
- and record what passed, what was skipped, and why.

Local requirement for this skill:
- the report must name the source used to discover each gate
  (`AGENTS.md`, `CONTRIBUTING.md`, CI config, task runner, etc.).

### 6) Check public-surface impact before finishing
If the change touched any public or semi-public surface, confirm that verification covered it.

Examples:
- CLI/config behavior,
- API contracts,
- auth or permission logic,
- persistence or migration behavior,
- build or packaging behavior,
- user-facing docs or examples.

If any public-surface behavior changed, make sure:
- tests or verification evidence cover the change,
- documentation is updated where required by repo policy,
- the final report clearly says behavior changed and where it was documented.

### 7) Produce a required proof-of-verification report
Before declaring success, produce a report containing:

- **Change summary**
  - what changed
  - where it changed
  - behavior preserved or behavior changed

- **Scope stats**
  - files changed
  - approximate diff size
  - net new LOC estimate

- **Verification discovery**
  - exact commands chosen
  - where each command was found

- **Targeted verification**
  - commands run
  - results
  - failures encountered and fixes made

- **Full verification**
  - commands run
  - results
  - any remaining limitations or CI-only follow-up required by repo policy

- **Behavior statement**
  - `Behavior preserved` or `Behavior changed`
  - short explanation
  - where the change is documented, if applicable

This report is mandatory. Verification is not complete without it.

## Verification checklist

- [ ] The changed area and intended behavior impact are clearly stated
- [ ] Diff scope is reviewable or explicitly sliced
- [ ] Canonical repo verification commands were discovered before broad validation
- [ ] Shared verification flow from `references/shared-verification-and-proof-template.md` was followed
- [ ] Public-surface changes were validated and documented where required
- [ ] A proof-of-verification report was produced with exact commands, sources, and results

## Boundary with shared verification reference

The shared reference owns the common mechanics of verification:
- targeted-first execution,
- stop-and-fix,
- repo-gate execution order,
- and proof-note structure.

This skill owns:
- verification-phase routing,
- diff-discipline and reviewability,
- gate discovery,
- public-surface verification coverage,
- and the required proof-of-verification report contents.

## Completion criteria

You may declare the work verified only when:
- targeted verification for the changed area is green,
- full required verification gates are green, or repo policy explicitly allows final CI completion,
- any public-interface impact is covered by tests/docs/reporting as required,
- the proof-of-verification report is included.

## Troubleshooting

### Symptom: "I don’t know what commands to run."
Likely cause:
- the repo does not document its gates clearly, or the authoritative files were not checked.

Recovery:
- inspect `AGENTS.md`, `CONTRIBUTING.md`, development docs, task runners, and CI configs in that order,
- prefer commands already used by CI,
- if still missing, run the smallest justifiable checks and explicitly report that the canonical gate list was not found.

### Symptom: "The full suite fails late and I lose time."
Likely cause:
- targeted checks were skipped or the change slice is too large.

Recovery:
- identify narrower area checks and run them first,
- split the change into smaller independently verifiable slices,
- avoid adding more code while a known gate is failing.

### Symptom: "The diff keeps expanding during verification."
Likely cause:
- unrelated cleanup or refactor is being mixed into validation work.

Recovery:
- revert unrelated edits,
- split prep refactor from behavior change,
- keep the verification pass focused on proving the current slice.

### Symptom: "I found the commands, but they are slow or expensive."
Likely cause:
- the repo’s full gates are broad.

Recovery:
- use targeted checks for fast iteration,
- still run full required gates before final completion unless repo policy says otherwise,
- record any CI-only constraints clearly in the report.

## Examples

### SHOULD trigger
- "I changed this module. What verification gates should I run before I’m done?"
- "Help me validate this diff safely and tell me exactly how to prove it works."
- "This PR touched config defaults and the API client; run the right checks in the right order."
- "My diff got bigger than expected. Keep verification disciplined and produce a report."

### SHOULD NOT trigger
- "Plan this feature before we start coding."
- "Reduce the LOC and simplify the design while I implement this."
- "Design a new CI pipeline for this repo."
- "Invent a brand-new testing strategy for this codebase."

## References and resources (repo-local)

When present, treat these as authoritative:
- `AGENTS.md` or nested `AGENTS.md` — repo rules and canonical gate guidance
- `CONTRIBUTING.md` — contributor workflow and required checks
- `README.md` / `docs/` development sections — documented local commands
- `Makefile`, `justfile`, `taskfile.yml`, `package.json`, `pyproject.toml` — runnable task registry
- `.github/workflows/*`, `.gitlab-ci.yml`, or equivalent CI config — source of truth for enforced automation
- `references/shared-verification-and-proof-template.md` — use for the common verification flow: targeted-first checks, stop-and-fix, repo-gate execution order, and proof-note structure

## Changelog

- 2.1.0 (2026-03-07): Repositioned the skill as the primary verification-phase runbook; rewrote description and opening sections to sharpen routing against planning and implementation-complexity skills; strengthened required proof-of-verification output.
- 2.0.0 (2026-03-04): Rewrite to be repo-agnostic; adds gate discovery, explicit decision rules, and a required "How I verified" report.