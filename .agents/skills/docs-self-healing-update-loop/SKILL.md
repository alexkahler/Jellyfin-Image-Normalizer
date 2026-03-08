---
name: docs-self-healing-update-loop
description: >
  Synchronize README, docs, examples, templates, and agent guidance after externally
  visible code changes so documentation does not drift from actual behavior. Use as a
  companion after contract, workflow, CLI, config, API, path, safety, or user/developer
  experience changes have already been identified. Do not use as the primary skill for
  deciding the contract itself; use the contract- or domain-specific skill first, then
  use this one to propagate the final truth across documentation and guidance.
metadata:
  version: "2.1.0"
  updated: "2026-03-07"
  owners:
    - "@codex"
    - "@alexkahler"
  notes: >
    Repo-agnostic companion skill for post-change documentation synchronization.
    This skill does not own interface-contract decisions; it updates dependent
    documentation and agent guidance after those decisions are made. For stronger
    guarantees, optionally add CI checks that execute documentation examples.
---

# Docs Self-Healing Update Loop

A repeatable, verification-driven companion workflow for keeping documentation, examples, and agent instructions aligned with real code behavior after externally visible changes. This is an operational synchronization runbook, not a style guide and not the primary authority for defining CLI/config/API contracts.

## Scope and intent

### Primary role
Use this skill to **propagate already-decided changes** into:
- README
- `docs/`
- `examples/`
- templates and sample configs
- `AGENTS.md`
- skill files and other agent guidance

This skill is responsible for **post-change synchronization**.

### Companion positioning
This is usually a **companion skill**, not the first-choice trigger.

Typical pairing:
- **Primary first:** a contract or implementation skill determines the actual change.
- **Then this skill:** synchronize all documentation and guidance to match that final behavior.

Examples:
- Use `cli-and-config-contract` first for CLI/config behavior decisions, then use this skill to update README, examples, and agent guidance.
- Use a refactor or implementation skill first when paths, entry points, or workflows move, then use this skill to remove stale references everywhere.

### Use this skill when
- You changed any **public or semi-public surface**, including:
  - CLI flags, subcommands, exit codes, defaults, usage behavior
  - config keys, schema, validation, precedence, file locations
  - API endpoints, contracts, auth, retries, timeouts, rate limits
  - scripts, entry points, paths, project layout, repository workflows
  - safety semantics such as dry-run, write gates, permissions, destructive behavior
- You moved or renamed files, directories, modules, commands, or workflows that docs currently reference.
- A non-trivial PR has already changed behavior and you need to prevent doc drift.

### Don’t use this skill when
- You need to **decide** the contract itself. Use the narrower contract or domain skill first.
- The change is purely internal and does not affect documented workflows, commands, config, paths, or externally visible behavior.
- The task is only grammar, tone, wording polish, or conceptual expansion without behavior/workflow change.

## Inputs and preconditions
- Code changes already exist, or the final intended behavior is already known.
- Repo has `AGENTS.md` with verification expectations, if applicable.
- You can inspect the diff and run the repo’s documented checks.
- You know which primary skill or source of truth owns the changed behavior.

## Tools and permissions
- Expected tools:
  - diff inspection (`git diff`, PR diff, equivalent)
  - text search (`rg`, `grep`, editor/global search)
  - repo verification commands from `AGENTS.md`
- Safety rules:
  - Do not invent commands, paths, flags, defaults, or migration steps.
  - Treat code, help output, config schema, and tested behavior as the source of truth.
  - If docs and code disagree, update docs to match verified behavior unless the task explicitly says the code is wrong.

## Workflow

### 1) Confirm the authoritative source of truth
**Goal:** Synchronize from a known truth, not from guesswork.

**Action:**
- Identify what actually changed.
- Identify which artifact currently defines the truth:
  - code behavior
  - CLI help output
  - config schema/defaults
  - tests
  - migration logic
  - approved implementation notes from the primary skill
- Write a short "Source of Truth" note:
  - what changed
  - where the true behavior is defined
  - which companion docs must be updated

**Expected output:** A brief source-of-truth statement that anchors the rest of the pass.

**If/then rule:**
- If contract details are still undecided, stop and return to the primary contract/domain skill before editing docs.

---

### 2) Build a doc impact summary
**Goal:** Make documentation scope explicit before editing files.

**Action:**
From the diff, list every changed surface that users or developers may notice:
- commands, flags, subcommands, exit codes
- config keys, defaults, precedence, validation behavior
- file paths, entry points, scripts, module locations
- required setup steps or workflow order
- safety/permission semantics
- outputs, artifacts, logs, structured responses
- migration or rollback implications

Write a short 5–10 bullet **Doc Impact Summary**.

**Expected output:** A concrete impact list that can be checked against updated files.

---

### 3) Find every dependent documentation location
**Goal:** Update all stale references in one pass.

**Search targets:**
- `README*`
- `docs/**`
- `examples/**`
- sample configs and templates
- setup scripts or bootstrap docs
- `AGENTS.md` and nested agent guidance
- `.agents/skills/**` or equivalent skill directories

**Search by:**
- old and new flag names
- old and new config keys
- renamed paths and filenames
- old commands
- error text or help text fragments if docs quote them
- workflow phrases likely copied across files

**Expected output:** A short **Files to Update** list.

**If/then rule:**
- If you find duplicated instructions in several places, mark one as canonical and plan to replace duplicates with pointers where appropriate.

---

### 4) Apply canonical-source discipline
**Goal:** Reduce future drift, not just current drift.

**Rules:**
- Keep invariant contributor and repo rules in `AGENTS.md`.
- Keep task-scoped procedures in the relevant skill.
- Keep README concise and high-signal; link to deeper docs instead of duplicating long procedures.
- Keep contract ownership in the contract/domain skill or code-level truth, not here.

**Action:**
- When the same instruction appears in multiple places:
  - update the canonical version
  - shorten or replace duplicate copies with links or brief references
- Remove stale workflow copies that are likely to drift again.

**Expected output:** Fewer duplicate instructions and a clearer documentation ownership pattern.

---

### 5) Update docs to match runnable truth
**Goal:** Make documentation reflect current verified behavior.

**Editing rules:**
- Commands must be copy/paste runnable unless explicitly marked as pseudocode.
- Paths must match the current repository structure.
- Config examples must reflect real keys, defaults, validation rules, and precedence.
- Safety semantics must be explicit for destructive or stateful operations.
- If behavior changed, prefer documenting:
  - **Before → After**
  - required migration action
  - rollback or compatibility note when relevant

**Expected output:** Updated docs, examples, templates, and agent guidance aligned with the source of truth.

**If/then rule:**
- If a command or example cannot be run safely, rewrite it to use dry-run, temp directories, mocks, or an explicitly labeled illustrative form.

---

### 6) Synchronize agent guidance and skill references
**Goal:** Prevent human-facing docs and agent-facing instructions from diverging.

**Action:**
Check whether the change affects:
- `AGENTS.md`
- skill trigger descriptions
- workflow steps in related skills
- setup or verification instructions used by agents

Update only what changed. Keep agent guidance aligned with verified repo behavior and avoid duplicating long documentation unnecessarily.

**Expected output:** Agent instructions that reflect the same current truth as user-facing docs.

---

### 7) Verify against reality
**Goal:** Do not declare success based on plausible wording alone.

**Action:**
Use `references/shared-verification-and-proof-template.md` for the common verification flow:
- run the smallest relevant checks first,
- use `AGENTS.md` as the canonical source for repo gates,
- apply stop-and-fix on failures,
- and record a short verification note.

Then perform the docs-specific sanity checks for this skill:
- CLI examples match actual help output and flags
- config examples match real schema/defaults
- paths and filenames exist
- workflow order matches current repo expectations

**Expected output:** A concise verification record tied to the doc updates.

**If/then rule:**
- If docs conflict with observed behavior during verification, fix docs or escalate to the primary skill if the underlying contract is still unclear.

## Verification checklist
- [ ] The source of truth for the change was identified before docs were edited.
- [ ] All affected documentation surfaces were searched and reviewed.
- [ ] README, docs, examples, templates, and agent guidance reflect current behavior where relevant.
- [ ] Paths, commands, flags, config keys, defaults, and safety semantics are accurate.
- [ ] Contradictory duplicate instructions were removed or reduced.
- [ ] Repo verification gates from `AGENTS.md` pass.
- [ ] A short "How I Verified" note exists.

## Completion criteria
Stop only when:
- The **Doc Impact Summary** has been fully reflected in the affected documentation set.
- The **Files to Update** list has been cleared.
- User-facing docs and agent-facing guidance agree with the verified source of truth.
- Verification is complete and recorded.

## Troubleshooting

### Symptom: Docs still contradict each other
- **Likely cause:** duplicated instructions across README, docs, examples, and agent files.
- **Recovery:**
  - choose one canonical location
  - update that location first
  - replace other copies with brief pointers or remove stale duplicates

### Symptom: This skill is being used to decide the contract
- **Likely cause:** the task started in the wrong skill.
- **Recovery:**
  - pause documentation propagation
  - switch to the narrower contract/domain skill
  - return here only after the behavior is settled

### Symptom: Commands in docs are hard to validate safely
- **Likely cause:** examples are destructive or depend on external systems.
- **Recovery:**
  - add dry-run or smoke-test forms
  - use temp directories
  - make prerequisites explicit
  - label illustrative pseudocode clearly where execution is not appropriate

### Symptom: Example output is unstable
- **Likely cause:** timestamps, random IDs, nondeterministic ordering, environment-specific text.
- **Recovery:**
  - avoid brittle exact output where possible
  - assert stable properties instead
  - normalize output in tests if example execution is automated

## Routing examples

### SHOULD trigger this skill
- "We changed config defaults and validation rules; sync README, sample config, and agent guidance."
- "This refactor moved directories and broke doc paths everywhere; update docs and examples."
- "The CLI changed and I want all references, templates, and skill instructions brought back in sync."

### SHOULD NOT trigger this skill
- "Decide what the new CLI flag behavior should be."
- "Refactor this internal helper function; there are no workflow or behavior changes."
- "Improve wording and readability in the docs only."

### Companion / near-miss guidance
- **Use as companion with:** `cli-and-config-contract`, refactor skills, implementation skills, verification skills, or any workflow that changed externally visible behavior.
- **Near miss:** if the task is defining the interface contract itself, this skill should not lead.
- **Handoff pattern:** primary skill decides the change → this skill propagates that truth → verification confirms docs and guidance now match.

## References and resources
- Use repo-native verification commands from `AGENTS.md`.
- Prefer current code, tests, help output, and schema definitions over stale prose.
- references/shared-verification-and-proof-template.md — use for common verification mechanics and proof recording
- Optional hardening:
  - doctest for Python examples
  - Markdown code-block testing in CI
  - doc link or example validation where appropriate

## Changelog
- 2.1.0 (2026-03-07): Repositioned as a companion skill for post-change synchronization; clarified that it does not own contract decisions; added explicit primary/companion/near-miss guidance and a source-of-truth step.
- 2.0.0 (2026-03-04): Rewrite to be repo-agnostic; added explicit scope boundaries, verification-driven workflow, optional executable-docs hardening, and trigger examples.