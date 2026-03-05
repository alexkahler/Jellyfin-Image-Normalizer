---
name: docs-self-healing-update-loop
description: Keep docs and agent guidance synchronized with code changes to prevent “docs drift”. Use after any non-trivial PR (behavior changes, refactors, renamed/moved files, CLI/config/API changes, defaults, safety/permission semantics). Don’t use for purely internal refactors that do not change user/developer workflows or any documented surface.
metadata:
  version: "2.0.0"
  updated: "2026-03-04"
  owners: 
    - "@codex"
    - "@alexkahler"
  notes: This skill is repo-agnostic. If you want stronger guarantees, consider adding CI checks that execute documentation examples (e.g., doctest / pytest doctest support / Markdown code-block testing plugins). Those are optional and may require dependencies and CI configuration.
---

# Docs Self-Healing Update Loop

A repeatable, verification-driven loop to keep documentation, examples, and agent instructions aligned with actual code behavior. This is designed as an operational runbook (not a style guide) and favors “copy/paste runnable” examples and explicit verification.

## Scope and intent

### Use this skill when
- You changed any **public or semi-public surface**:
  - CLI flags, subcommands, exit codes, default behaviors
  - config keys/schema/defaults/validation/error messages
  - API endpoints/contracts, auth, retries/timeouts, rate limits
  - file paths, project layout, entry points, scripts, tooling commands
  - safety semantics (dry-run, write-gates, permissions, destructive operations)
- You moved/renamed files or changed workflows described in:
  - README, docs/, examples/, templates, agent guidance (AGENTS.md, skills)

### Don’t use this skill when
- The change is truly internal and **does not affect** any documented workflow, command, configuration, or public-facing behavior.

## Inputs and preconditions
- A PR or set of changes already exists (code/tests changed).
- Repo has **AGENTS.md** with **verification gates** (assumed).
- You can run the repo’s verification commands locally or in CI (assumed).

## Tools and permissions
- Expected tools: git diff/log, grep/ripgrep, test runner(s) from AGENTS.md.
- Safety: **Do not invent commands**. Prefer commands already used by the repo and recorded in docs/AGENTS.md.

## Workflow

### 1) Identify doc-impacting change surfaces
**Goal:** Build a short, explicit “doc impact list” before editing docs.

**Action (checklist):**
- From the diff, list which of these changed:
  - **Commands:** new/removed/changed CLI usage, flags, subcommands, exit codes
  - **Configuration:** new/renamed/removed keys; defaults; validation rules; config file locations
  - **Paths/layout:** moved modules, renamed directories, new entry points, new scripts
  - **Behavior semantics:** safety gates, dry-run defaults, retry rules, destructive actions, auth behavior
  - **Outputs:** logs, printed output format, structured output, file artifacts
- Write a 5–10 bullet “Doc Impact Summary” (what changed + where users will notice).

**Expected output:** A concrete list of “surfaces that docs must reflect”.

---

### 2) Locate all candidate documentation that may now be stale
**Goal:** Avoid drift by updating *all* references in one sweep.

**Action (search targets):**
- README and root docs
- `docs/` (guides, reference pages, architecture notes, ADRs)
- `examples/`, sample configs, templates (e.g., `config.example.*`)
- `AGENTS.md` (and any nested AGENTS.md)
- `.agents/skills/**` and other agent instructions

**Technique:**
- Search by keywords taken from the diff:
  - old/new flag names
  - config keys
  - old/new file paths
  - error message fragments (if they are documented)
  - command snippets

**Expected output:** A short “Files to update” list.

---

### 3) Apply the “single source of truth” rule (de-duplication)
**Goal:** Prevent contradictory instructions across docs.

**Rules:**
- Put *invariant, always-needed* contributor rules in **AGENTS.md**.
- Put *task-scoped procedures* in **skills** (this skill is one of them).
- Keep README short: link to deeper docs rather than duplicating long runbooks.

**Action:**
- If you find duplicated instructions, pick one canonical location and:
  - update the canonical content
  - replace the duplicate with a short pointer/link

**Expected output:** Reduced duplication + fewer future drift points.

---

### 4) Update docs using “runnable truth”
**Goal:** Make docs executable enough that they stay correct.

**Rules for edits:**
- Commands must be **copy/paste runnable** (or explicitly marked as pseudocode).
- Examples must reflect:
  - correct working directory assumptions
  - correct file paths
  - current defaults and safety semantics (especially destructive operations)
- If behavior changed, describe it in terms of:
  - **Before → After**
  - migration notes (if users must change anything)
  - rollback notes (if the change is risky)

**Tip (optional hardening):**
- Prefer automatically testable examples:
  - Python docstring examples via `doctest`.
  - README / Markdown snippet testing via pytest plugins (optional).

---

### 5) Verification loop (don’t claim “done” without it)
**Goal:** Ensure docs match reality *now*, not “in theory”.

**Action:**
1. Run the **smallest relevant verification** first (targeted unit tests, linters).
2. Run the repo’s **full verification gates** from AGENTS.md.
3. Sanity-check documentation commands:
   - If a doc includes a command sequence, confirm it matches current CLI/help output and paths.
   - If examples create files or modify state, use safe modes (dry-run) or temporary directories where possible.

**Expected output:** A “How I verified” note (commands + short results).

---

## Verification checklist (must complete)
- [ ] All doc examples reflect current CLI/config/API behavior.
- [ ] Paths in docs match repo structure after the change.
- [ ] Safety semantics are correct and explicit (dry-run, write gates, destructive steps).
- [ ] No contradictory instructions remain across README/docs/examples/agent guidance.
- [ ] Repo verification gates from AGENTS.md pass.

## Completion criteria (stop condition)
You may stop only when:
- The “Files to update” list has been addressed, and
- The verification checklist is fully satisfied, and
- There is a short “How I verified” note suitable for a PR description.

## Troubleshooting

### Symptom: Docs still contradict each other
- Likely cause: duplicated instructions across README/docs/examples/agent files.
- Fix: choose one canonical source and replace other copies with links/pointers.

### Symptom: Doc commands are hard to validate safely
- Likely cause: commands are destructive or require external services.
- Fix:
  - add a safe “dry-run” or “smoke test” path to docs
  - gate integration steps behind explicit environment variables
  - document prerequisites clearly (and keep them minimal)

### Symptom: Example output keeps changing (unstable)
- Likely cause: timestamps, randomized IDs, nondeterministic ordering.
- Fix:
  - rewrite examples to avoid unstable outputs
  - assert properties rather than exact output where feasible
  - if using doctest/snippet tests, normalize outputs or avoid brittle expectations

## Examples (routing)

### SHOULD trigger this skill
- “I renamed a CLI flag / added a subcommand—update docs so they don’t drift.”
- “We changed config defaults and validation rules—make README and sample config accurate.”
- “This refactor moved directories and broke doc paths—fix all docs and examples.”

### SHOULD NOT trigger this skill
- “Refactor this internal helper function; no behavior changes.”
- “Improve doc wording/grammar only.”
- “Add more conceptual explanation without changing any workflows.”

## References and inspiration (optional reading)
- Designing high-quality skills as operational runbooks with verification and progressive disclosure.
- Diátaxis framework (keep doc types distinct; avoid mixing reference with how-to).
- Python doctest support (keeping examples in sync).
- Testing code blocks in README/Markdown with pytest plugins (optional).

## Changelog
- 2.0.0 (2026-03-04): Rewrite to be repo-agnostic; added explicit scope boundaries, verification-driven workflow, optional “executable docs” hardening, and trigger examples.