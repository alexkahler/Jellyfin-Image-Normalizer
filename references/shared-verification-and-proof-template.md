# Shared Verification and Proof Template

Use this reference when a skill needs the common mechanics of verification.
This file centralizes the repeated process for:
- choosing the smallest relevant checks first,
- deferring canonical gate commands to `AGENTS.md`,
- applying stop-and-fix discipline,
- running full verification before completion,
- and recording a short proof/report.

This reference does **not** replace skill-specific verification requirements.
Each skill must still define its own:
- behavior-specific tests,
- contract-specific assertions,
- completion checklist,
- and stop conditions.

## When to use this reference
Use this reference from a skill when:
- the skill changes code, docs, config, contracts, or workflows that must be verified,
- the repo already defines canonical gates in `AGENTS.md`,
- and the skill only needs shared verification mechanics rather than a bespoke verification procedure.

Do **not** use this reference as a substitute for:
- domain-specific test design,
- migration-specific validation,
- behavior-specific assertions,
- or repo policy defined in `AGENTS.md`.

## Verification invariants

1. **`AGENTS.md` is canonical for repo gates**
- Do not duplicate repo-wide verification commands inside skills unless there is a strong local reason.
- If a skill references repo gates, it should point to `AGENTS.md` rather than restating the full command set.

2. **Run the smallest relevant checks first**
- Start with the narrowest tests/checks that directly validate the changed behavior.
- Use fast, local verification before expensive full-suite runs.

3. **Apply stop-and-fix discipline**
- If a targeted check fails, stop expanding scope.
- Fix the failure or narrow the claim before proceeding.
- Do not continue stacking changes on top of a known-bad state.

4. **Run full required gates before declaring done**
- After targeted checks pass, run the full repo gates required by `AGENTS.md`.
- Do not declare completion based only on partial verification unless the task explicitly allows it and the limitation is recorded.

5. **Record proof, not just confidence**
- End with a short verification note that states what was run, what passed, what was intentionally not run, and why.

6. **Handle same-SHA CI evidence explicitly for closure claims**
- For route-work closure/progression claims, include a minimal closure-evidence record:
  - local SHA,
  - workflow identity,
  - CI run id/url when same-SHA evidence exists,
  - per-required-job status summary for required CI jobs from `project/verification-contract.yml` (currently `test/security/quality/governance`).
- If same-SHA CI evidence cannot be obtained, explicitly record inability, include residual risk, and do not imply same-SHA validation occurred.
- If same-SHA evidence remains unavailable across consecutive slices for the same target row with no new external action, stop continuation slicing and run the loop-breaker flow in `project/loop-breaker-playbook.md`.

## Inputs and preconditions
Before using this template, identify:
- the changed surface,
- the smallest direct checks for that surface,
- the relevant repo-wide gates from `AGENTS.md`,
- and any environment limits that affect what can be run.

Minimum input record:
- **Changed surface:** <what changed>
- **Targeted checks:** <smallest relevant tests/checks>
- **Repo gates from AGENTS.md:** <lint/type/test/etc. as applicable>
- **Constraints:** <none / missing creds / external dependency / time-sensitive / platform-specific>

## Workflow

### 1) State the verification target
**Goal:** Verify the actual change, not a vague sense of progress.

**Action:**
Write a 1–3 line note:
- what changed,
- what must now be true,
- what evidence would prove it.

**Expected output:** A short verification target statement.

Template:
- **Changed surface:** …
- **Must now be true:** …
- **Direct evidence:** …

---

### 2) Choose the smallest relevant checks first
**Goal:** Validate the claim cheaply before invoking broader gates.

**Action:**
Select the narrowest checks tied to the change, for example:
- focused unit tests,
- a single contract test,
- one CLI help/behavior assertion,
- one config validation test,
- a targeted doc/example sanity check,
- a smoke test for the edited path.

**Rules:**
- Prefer behavior-facing checks over incidental implementation checks.
- Prefer targeted tests over full-suite runs as the first step.
- If the change is docs-only but behavior-linked, validate the documented command/example against reality where feasible.

**Expected output:** A short list of targeted checks.

Template:
- **Targeted check 1:** …
- **Targeted check 2:** …
- **Why these are first:** …

---

### 3) Run targeted verification
**Goal:** Establish direct evidence for the changed surface.

**Action:**
Run the targeted checks.

**If/then rules:**
- If a targeted check fails:
  - stop,
  - diagnose the failure,
  - fix code/docs/config or narrow the claim,
  - rerun the targeted check before moving on.
- If a targeted check cannot be run:
  - state exactly why,
  - use the closest safe proxy check if one exists,
  - record the limitation in the final proof note.

**Expected output:** Pass/fail result for each targeted check.

Template:
- **Check:** …
- **Result:** pass / fail / blocked
- **Notes:** …

---

### 4) Run repo-wide gates from `AGENTS.md`
**Goal:** Confirm the change also satisfies the repo’s standard quality bar.

**Action:**
Run the applicable verification gates defined in `AGENTS.md`.

Typical examples may include:
- formatting,
- linting,
- type checking,
- unit/integration tests,
- docs/example validation,
- build/package checks.

**Rules:**
- `AGENTS.md` remains the source of truth for which gates matter.
- Do not invent substitute commands unless the repo explicitly documents alternatives.
- If a full gate is not run, record why and whether the omission materially limits confidence.

**Expected output:** Repo-gate results.

Template:
- **Gate:** …
- **Result:** pass / fail / not run
- **Notes:** …

---

### 5) Apply stop-and-fix discipline
**Goal:** Prevent “mostly verified” changes from being treated as complete.

**Action:**
If any targeted check or required gate fails:
- stop,
- fix the issue,
- rerun the smallest relevant failing check first,
- then rerun the affected broader gate(s).

**Rules:**
- Do not keep broadening the diff while verification is red.
- Do not hide failed checks behind a general statement like “looks good overall.”
- If the task must end in a partial state, say so plainly.

**Expected output:** A clean verified state or an explicit partial-state note.

---

### 6) Produce a short “How I Verified” note
**Goal:** Leave portable proof that another person or agent can inspect quickly.

**Action:**
Record:
- what was run,
- what passed,
- what was not run,
- any blockers/limitations,
- and whether the final claim is full or partial.

**Expected output:** A concise verification note.

Template:
## How I Verified
- Targeted checks run:
  - <check> — passed
  - <check> — passed
- Repo gates run from `AGENTS.md`:
  - <gate> — passed
  - <gate> — passed
- Not run / limitations:
  - <item> — <reason>
- Final confidence:
  - Full / Partial
- Remaining risk:
  - <brief note or “none beyond normal change risk”>

## Reusable checklist
Use this inside a skill-local verification section if helpful:

- [ ] I identified the changed surface and what must now be true.
- [ ] I ran the smallest relevant checks first.
- [ ] I applied stop-and-fix when a check failed.
- [ ] I ran the repo’s applicable gates from `AGENTS.md`.
- [ ] I recorded a short “How I Verified” note.
- [ ] Any skipped checks or limitations are explicitly disclosed.

## Skill integration pattern

A skill should **reference** this file for common mechanics, then keep only its local verification specifics inline.

Recommended pattern inside a skill:

### Verification
Use `references/shared-verification-and-proof-template.md` for the common verification flow:
- run the smallest relevant checks first,
- use `AGENTS.md` as the canonical source for repo gates,
- apply stop-and-fix,
- then record a short “How I Verified” note.

Additional skill-specific requirements for this skill:
- <behavior-specific requirement 1>
- <behavior-specific requirement 2>
- <migration/config/docs/API/refactor-specific requirement>

## What stays local to each skill
Do **not** move these into the shared reference:
- exact contract assertions,
- migration/deprecation validation,
- public-surface compatibility checks,
- refactor-specific characterization tests,
- doc-impact-specific checks,
- risk-specific proof obligations,
- skill-specific completion criteria.

## Example references from current skills
This shared reference fits the repeated mechanics already visible in the library:
- contract changes already say to run focused tests first, then repo gates from `AGENTS.md`, and stop-and-fix on failure;
- docs synchronization already says to verify against reality, run the smallest relevant checks first, then run repo gates, and record “How I Verified.”

Those local sections should remain, but can now be shortened to reference this file plus their skill-specific requirements.
