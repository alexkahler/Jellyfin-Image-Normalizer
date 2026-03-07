---
name: plan-first-scope-and-risks
description: Plan non-trivial code changes before editing any code. Use when work needs pre-coding scoping, risk framing, staged milestones, rollback planning, or a read-only exploration phase because blast radius is unclear. Best for multi-file changes, refactors/migrations, interface changes (CLI/API/config), or data/schema work. Produces: repo map snippet, scoped non-goals, risk register, milestone plan with verification gates, and rollback strategy. Don't use for implementation-time complexity control, post-change verification/reporting, or trivial one-file edits with obvious tests and no behavior change.
compatibility: Assumes a Python repo with git, unit tests, and CI. Verification commands MUST be taken from AGENTS.md (source of truth). If the repo lacks AGENTS.md verification gates, add them first.
metadata:
  version: "1.2.0"
  updated: "2026-03-07"
  owners:
    - "@codex"
    - "@alexkahler"
  notes:
    - This skill is repo-agnostic. Replace example commands/paths with your repo's actual ones.
    - Verification gates MUST come from AGENTS.md. Do not invent commands if AGENTS.md disagrees or is missing.
    - If the repo does not use pytest, substitute the repo's test runner commands (from AGENTS.md).
    - This is a pre-coding planning skill. It should usually trigger before implementation or verification-focused skills.
---

# Plan First: Scope, Risks, and Staged Milestones (Universal)

## Scope and intent
This skill is for planning before code changes begin.
Use it to scope non-trivial work into staged, reviewable milestones with explicit risks, non-goals, and rollback strategy.

It defines what must be verified at each milestone, but it does not own executing repo gates or writing final proof after implementation. Hand off to the verification skill once code changes exist.

It prevents big-bang edits and silent regressions by requiring:
- a tight scope + explicit non-goals,
- a small risk register with mitigations,
- staged milestones that are independently verifiable,
- a concrete rollback plan.

**Hard rule:** do not change code until the plan outputs are complete.

## When to use
Use this skill when **any** is true:
- Touching more than ~2 files
- Refactor/migration where behavior should be preserved
- Changing public interfaces (CLI flags, config schema, API endpoints, file formats, DB schema, etc.)
- Unsure about blast radius, performance impact, or safety implications
- Work likely to exceed ~150 net new LOC or span many modules
- You need a read-only exploration step before deciding how to implement

Use this skill **before coding**, especially when the first problem is scoping, sequencing, or risk reduction.

Do **not** use when:
- The main task is implementation-time complexity control or keeping the diff small
- The main task is running verification gates, proving a completed change, or writing a verification report
- Single-file, obviously safe change with clear existing tests
- Pure documentation update
- Mechanical formatting only

## Inputs and preconditions (confirm before planning)
- The task request / goal (1–3 sentences).
- Current branch and whether main/trunk is green (or last known green commit).
- Location of **AGENTS.md** and its **Verification gates** section (commands are the source of truth).
- Any known "contracts" in the repo:
  - CLI interface
  - config files / schemas
  - API endpoints
  - DB migrations
  - output file formats
  - backward-compatibility expectations

If you cannot find verification gates or cannot define any verification for the change: **stop and escalate**.

## Handoffs
- Use this skill first when the problem is scoping, sequencing, rollback, or blast-radius reduction before editing code.
- Hand off to `loc-and-complexity-discipline` if the implementation starts growing in LOC, layers, branching, or scaffolding.
- Hand off to `verification-gates-and-diff-discipline` once code changes exist and the main task becomes proving the change with targeted checks, full gates, and a final verification note.

## Required outputs (must produce all)

### 1) Repo map snippet (paths only; no large dumps)
Provide a short list of relevant paths (as they exist in *this* repo), such as:
- Entry points (e.g., `src/...`, `package/__main__.py`, `cli.py`, `app.py`)
- Core modules touched / likely touched
- Tests root (e.g., `tests/`, `src/.../tests/`)
- CI workflow location(s) (e.g., `.github/workflows/...`)
- Docs likely impacted (e.g., `README.md`, `docs/`, `examples/`)

**Format**
- 8–15 bullets max
- paths only, optionally with 3–6 word "why" note

### 2) Change scope (in-scope / out-of-scope)
Write explicit bullets for:
- **In scope** (what will change)
- **Out of scope** (what will NOT change)
- **Assumptions** (only if needed; keep short)

### 3) Risk register (top 5, realistic)
Create a small risk register (table preferred). A risk register is a shared list of risks, impacts, and mitigations. Include:
- Risk
- Likelihood (L/M/H)
- Impact (L/M/H)
- Detection (how we'll notice)
- Mitigation (what we'll do to prevent/reduce)
- Verification (which gate/test validates it)
- Owner (who/what is responsible — can be "agent" if appropriate)

Notes:
- Keep it to the **top 5** most credible risks.
- Favor concrete engineering risks (regressions, compatibility, data loss, security, perf) over vague project risks.

### 4) Staged plan (milestones with verification gates)
Create 2–6 milestones. Each milestone MUST be independently verifiable.

For common verification mechanics, use
`references/shared-verification-and-proof-template.md`.

For each milestone include:
- **Objective** (1 sentence)
- **Files/areas likely touched** (paths)
- **Approach** (2–5 bullets)
- **Verification** (copy exact commands from `AGENTS.md`; add any milestone-specific targeted checks)
- **Exit criteria** (what must be true to move on)
- **Notes** (optional: performance, compatibility, migrations)

Skill-specific rule for this planning skill:
- The plan must name milestone-specific verification, but this skill does not execute or own final proof of the implementation.

### 5) Rollback plan (exact strategy)
Provide a rollback plan that matches the repo's release model. Include **at least one** of:
- **Git revert** strategy (preferred for most code-only changes)
- **Roll-forward** (fix forward) strategy (when revert is risky)
- **Feature flag / config toggle** (if the repo uses toggles)
- **Data rollback** (if migrations or data writes occur: backups, restore plan, "do not delete" rules)

Keep it concrete:
- "If X fails, do Y"
- Name the artifact to revert (commit/PR) and the steps (e.g., "revert commit", "redeploy previous version", "disable flag").

(General rollback guidance commonly distinguishes rollback vs revert vs roll-forward as different recovery tactics; choose explicitly.)

---

## Workflow (how to write the plan)

### Step 0 — Restate the goal and constraints
- Goal (1–3 sentences)
- Must-preserve behaviors (if any)
- Explicit "won't do" list starter (draft)

### Step 1 — Identify the "contract surface"
List what users/systems rely on:
- CLI flags / commands
- config keys/schema
- API endpoints
- output formats
- DB schema/migrations
- public Python APIs (import paths, function signatures)

If contract surface is unclear:
- plan a short exploration milestone first (read-only).

### Step 2 — Build the repo map snippet
Only include paths relevant to this change and verification.

### Step 3 — Define scope and non-goals
Make scope small enough that each milestone can pass verification quickly.

### Step 4 — Draft the risk register
Focus on:
- regressions in contract surface
- data loss / destructive operations
- security/perms changes
- performance regressions
- test fragility / CI failures

### Step 5 — Create staged milestones
Common milestone patterns (choose what fits):
- M1: baseline + targeted tests added (or characterization tests if needed)
- M2: implement minimal change behind a boundary / adapter
- M3: refactor/extract incrementally (if required)
- M4: docs update + final full gates

Stage-gate thinking: each stage ends with a gate (verification) before advancing.

### Step 6 — Add rollback plan
If any step touches data or external systems:
- include backup/restore strategy and "no destructive ops without explicit enable" rule.

### Step 7 — Completion criteria (Definition of Done)
A DoD is a shared checklist for "done". Include at minimum: tests pass, gates pass, docs updated if interface changed, and rollback is documented.

---

## Stop conditions (escalate)
Stop and request human review if:
- Verification cannot be defined or AGENTS.md is missing/contradictory
- Plan requires a rewrite across many modules without a safety net
- Behavior changes are unavoidable but not explicitly requested
- Change risks data loss or security exposure without clear mitigations

## Troubleshooting
- **Problem:** "I can't find the right verification commands."
  - **Fix:** Use the repo's AGENTS.md "Verification gates" section. If missing, add it before proceeding.
- **Problem:** "The plan is too big / too many files."
  - **Fix:** Split into smaller milestones or multiple PR slices; each slice must be independently verifiable.
- **Problem:** "Tests don't exist for the area."
  - **Fix:** Add targeted tests first; if behavior is hard to specify, add characterization tests at the boundary before refactoring.

## Examples

### SHOULD trigger
- "Before touching anything, plan how to split this refactor into safe stages."
- "Map the blast radius and risks before we change the config schema."
- "Create a staged plan for a CLI change with rollback and verification gates."
- "Plan a safe migration path before editing the data model."

### SHOULD NOT trigger
- "The code is already changed; now verify it and summarize what passed."
- "Keep this implementation under 100 LOC and avoid new abstraction layers."
- "Fix a typo in README."
- "Rename a local variable in one function and existing tests cover it."
- "Run formatting/linting only with no behavior changes."

## References and resources
- `references/shared-verification-and-proof-template.md` — use for common verification mechanics when defining milestone gates and final completion checks
- `references/risk-register-template.md` — optional template for consistent risk tables across planning-heavy skills

## Changelog
- 2026-03-07 (1.2.0): Rewrote description and early positioning to clarify that this is the pre-coding planning skill; added explicit boundaries against implementation-time complexity control and post-change verification ownership.
- 2026-03-04 (1.1.0): Made repo-agnostic; replaced project-specific paths with a universal contract-surface + gates approach; added DoD framing, risk register structure, and explicit rollback tactic selection.