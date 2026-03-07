---
name: audit-governance-and-slice-compliance
description: Produce an independent, evidence-based audit report for JFIN work (PR/branch/slice) to confirm compliance with Track 1 governance and the slice plan (WIs, parity matrix, route fence, verification contract). Use after implementation work is done (or mid-flight checkpoints), NOT during slice implementation. Outputs a detailed audit report with findings, severity, evidence, and remediation steps. Don’t use for writing new slices or making code changes; this skill reads, verifies, and reports.
metadata:
  version: "1.0.0"
  updated: "2026-03-05"
  owners:
    - "@jfin"
    - "@codex"
    - "@akaehler"
  report_style: "evidence-first"
compatibility: Assumes access to the JFIN repo, git diff/history, and ability to run repo verification commands and project governance scripts. Network access is not required.
---

# JFIN Audit: Governance + Slice Plan Compliance

## Scope and intent

This skill is a **governance audit runbook** for JFIN Track 1 work. It is designed to run **independently**
from slice implementation and produce a **detailed audit report** that answers:

- Is the work compliant with Track 1 governance rules and the verification contract?
- Is the work compliant with the Track 1 slice plan and work-item acceptance criteria?
- Is behavior preservation demonstrated and properly recorded (parity matrix + characterization/goldens)?
- Is routing/route-fence handling correct and not prematurely flipped?
- Are CI and repo contracts consistent (anti-drift)?

This skill is structured as an operational runbook with progressive disclosure and explicit verification steps.

### Non-goals

- Implementing fixes, refactors, or new features.
- Designing new governance systems beyond what Track 1 defines.
- Redefining the slice plan or WI acceptance criteria.

If the audit finds issues, it should recommend next actions and **which existing skill/runbook** to use to fix them,
but it should not perform the fix within this audit.

## When to use

Use this skill when you need a **formal, detailed audit report** for one of these targets:

- A PR, branch, or commit range representing a slice or set of slices.
- A claimed "slice complete" milestone requiring verification.
- A governance-heavy change (parity/characterization/goldens/architecture guards/route-fence enforcement).
- A release-readiness checkpoint for Track 1.

Do **not** use this skill while actively implementing the slice. Instead, implement first, then audit.

## Inputs and preconditions

### Required inputs (provide what you have; record missing items as audit gaps)

1) **Audit target**
- PR number and base branch, OR
- branch name, OR
- commit range (e.g., `main..feature/slice-x`)

2) **Slice context**
- WI identifier(s) if the work claims to satisfy a specific slice:
  - `WORK_ITEMS.md` order and WI mapping
  - WI docs (e.g., WI-001..WI-005)
  - WI template expectations

3) **Governance sources of truth**
- Track 1 blueprint and hard contracts
- Verification contract file
- Parity matrix + route fence artifacts
- Repo documentation (README / Technical Notes) for behavioral context

### Preconditions

- You can run local commands (tests, linters, governance scripts) or you have CI logs/artifacts.
- You can inspect diffs and changed files.

If any precondition is not met, proceed anyway and record an **Audit Limitation**.

## Tools and permissions

Allowed actions:
- Read repository files, diffs, and CI output.
- Run **non-destructive** verification commands (tests/linters/governance checks).
- Generate a report artifact (Markdown) summarizing compliance and gaps.

Prohibited actions:
- Editing code, tests, docs, or governance artifacts as part of the audit.
- Running destructive commands (uploads, deletes, restore runs against a real server).
- Rewriting the slice plan or changing governance policies.

## Audit workflow

### Step 0 — Establish audit envelope (required)

**Goal:** define exactly what is being audited and what "compliance" means.

1) Record:
- Target (PR/branch/range)
- Claimed slice/WI scope (if claimed)
- Time window (commit dates)
- Expected outputs (what the work claims is done)

2) Identify applicable governance contracts:
- Track 1 "hard" contracts and gates
- Verification contract commands + CI job requirements
- Parity + route-fence rules

**Output requirement:** a short "Audit Target Summary" section for the report.

---

### Step 1 — Collect evidence (files + commands)

**Goal:** gather verifiable evidence, not opinions.

#### 1A) Evidence: changed surface inventory
- Produce a path-only list of changed files grouped by:
  - `src/` runtime
  - `tests/`
  - `project/` governance scripts/artifacts
  - CI/workflows
  - docs

#### 1B) Evidence: governance artifacts touched
Explicitly check whether the change touches any of:
- `project/parity-matrix.md`
- `project/route-fence.md` or route-fence JSON generation
- `project/verification-contract.yml`
- `project/scripts/verify_governance.py` or governance checks wiring (mentioned in blueprint/README/notes)
- characterization baselines under `tests/characterization/baselines/`
- imaging goldens manifest under `tests/golden/imaging/manifest.json` (if applicable)

#### 1C) Evidence: verification runs (prefer local; otherwise CI)
Run or obtain results for the verification contract:
- Commands listed in `project/verification-contract.yml`
- Governance gate: `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` (Track 1 contract)

Also record CI job results vs `required_ci_jobs` in the verification contract.

**Output requirement:** a "Verification Evidence" section listing exact commands and pass/fail status.

> If you cannot run a command, mark it as **Not Executed** and state why (missing environment, time, CI unavailable).

---

### Step 2 — Verify governance compliance

**Goal:** check the actual Track 1 governance rules, not "best effort".

Perform the checks below and record each as:
- **PASS / FAIL / PARTIAL / NOT APPLICABLE / NOT VERIFIED**
- Evidence (file paths + command output references)
- Impact and remediation

#### 2A) Verification contract compliance (anti-drift)
- Does the change modify CI workflow(s) or verification commands?
- If verification contract changed, does CI reflect it in the same change? (Track 1 anti-drift rule)
- Are all `required_ci_jobs` present and green?

#### 2B) LOC policy compliance
- Enforce the `loc_policy` in `project/verification-contract.yml`:
  - `src_max_lines` blocker, `tests_max_lines` warn
- Confirm no new violations were introduced beyond known baseline (when applicable per README/Track 1 notes).

#### 2C) Architecture guards compliance (if applicable)
If the slice claims architecture checks (WI-001) or touches `sys.exit`/import boundaries:
- Verify `--check architecture` results and ratchet behavior (baseline counter does not grow).

#### 2D) Parity matrix schema + linkage compliance
- Validate parity matrix required columns and linkage resolvability:
  - `behavior_id`, `baseline_source`, `current_result`, `status`, `owner_test`, `approval_ref`
- For any row marked `changed/removed/suspicious`, confirm:
  - `approval_ref` is present and meaningful
  - notes + migration note (if used) are consistent with the blueprint contract

#### 2E) Characterization + golden governance (when applicable)
If the change touches behavior-covered areas:
- CLI/config characterization requirements (WI-004)
- Imaging characterization + golden requirements (WI-003)
- Safety contracts requirements (WI-005)

Confirm governance linkage checks:
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization` passes when the work modifies baselines or related tests.

---

### Step 3 — Verify slice-plan compliance

**Goal:** confirm the work aligns with the slice structure and constraints, not just "it works".

#### 3A) Slice identification and WI acceptance criteria
If the work claims a WI:
- Compare outputs to the WI’s acceptance criteria and public interfaces list.
- Verify that out-of-scope items were not silently included (especially: route flips, runtime behavior changes where prohibited).

#### 3B) "One objective per slice" and diff discipline
- Confirm the change set is slice-scoped (no "while I’m here" drift).
- If scope is broad, flag as governance risk and recommend slicing discipline remediation.

(When recommending remediation, reference: `verification-gates-and-diff-discipline` skill.)

#### 3C) Verification runtime budget (<10 minutes per slice)
- Check the WI’s "Verification commands (<10 min)" and confirm evidence exists that these are runnable/passed (locally or in CI).
- If verification exceeds 10 minutes or isn’t independently runnable, flag as noncompliance with Track 1 slice policy.

#### 3D) Rollback clarity
- Confirm rollback steps exist and are actionable (WI template field 6).

#### 3E) Behavior preservation statement
- Confirm presence and truthfulness of "Behavior-preservation statement" (WI template field 7).
- If behavior may have changed, confirm parity matrix reflects it and approvals are present.

---

### Step 4 — Verify route-fence compliance (Track 1 strangler discipline)

**Goal:** ensure routing is not flipped early and that artifacts remain consistent.

1) Confirm the route fence table is valid and unchanged unless explicitly part of the slice.
2) If route-fence JSON sync is part of the work:
- confirm markdown table ↔ runtime artifact sync is validated (as described in technical notes / README).
3) Confirm no `v1` route is enabled unless parity readiness for that row is demonstrably green (per Track 1 rule).

---

### Step 5 — Produce the audit report (required output)

Your final output must be a **standalone audit report** with the sections below.

## Audit report format (mandatory)

### 1) Executive summary
- Overall compliance status: **Compliant / Conditionally Compliant / Noncompliant**
- Top 3 risks (with severity)
- Immediate blockers (if any)

### 2) Audit target and scope
- Target PR/branch/range
- Claimed WI(s) / slice(s)
- Out-of-scope confirmations

### 3) Evidence collected
- Changed files summary (paths only)
- Verification evidence (commands + pass/fail/not-run)
- Key artifacts inspected (parity matrix, route fence, verification contract, baselines)

### 4) Compliance checklist (table-friendly, but not required to be a literal markdown table)
For each domain, record: status, evidence, notes.
- Verification contract & CI jobs
- Governance checks (`--check all`, relevant subchecks)
- LOC policy
- Parity matrix schema & linkage
- Characterization/goldens linkage (if applicable)
- Route-fence discipline
- Slice plan discipline (one objective, <10 min verification, rollback)

### 5) Findings (detailed)
For each finding:
- **ID**: AUD-001, AUD-002, …
- **Severity**: Blocker / High / Medium / Low
- **Condition**: what you observed
- **Criteria**: what rule/contract it violates (cite the governing artifact)
- **Evidence**: file paths, command outputs, CI job name
- **Impact**
- **Recommended remediation** (and which skill to use)

### 6) Remediation plan (prioritized)
- List fixes in recommended order
- Include verification to rerun after each fix

### 7) Audit limitations
- What you couldn’t verify and why
- How to close the gap

### 8) Final attestation
- A short statement of whether the work is audit-passing and what must be done to reach compliance.

## Remediation mapping to existing skills (use in recommendations)

When recommending fixes, refer to the appropriate skill rather than inventing a new workflow:

- Verification ordering + "How I verified" discipline → `verification-gates-and-diff-discipline`
- Planning + risk register + rollback definition → `plan-first-scope-and-risks`
- Python code quality bar + JFIN invariants → `python-quality-bar`
- Characterization tests for imaging → `pytest-characterization-tests-for-imaging`
- CLI/config contract changes → `cli-and-config-contract`
- Diff sizing / LOC & complexity → `loc-and-complexity-discipline`
- Docs drift cleanup after interface changes → `docs-self-healing-update-loop`
- Behavior-preserving Python refactors → `safe-refactor-python-modules`

## Decision rules (for consistent audit outcomes)

### Severity rubric
- **Blocker:** Violates a Track 1 hard gate (e.g., governance checks fail; CI required jobs missing; route fence flipped without parity proof; LOC blocker newly introduced in `src/`).
- **High:** Parity/characterization linkage broken; verification evidence missing for required commands; rollback missing; scope clearly exceeds slice plan.
- **Medium:** Docs drift likely; incomplete evidence; partial compliance with acceptance criteria; minor contract mismatches without immediate risk.
- **Low:** Style/clarity issues that do not affect governance correctness.

### Stop-and-report rule
If you detect any Blocker early (governance checks failing, route-fence violation, contract drift), **stop expanding audit scope** and prioritize:
1) documenting the blocker with evidence, and
2) listing minimal remediation to restore compliance.

## Examples

### SHOULD trigger this skill
- "Audit this PR to confirm it complies with Track 1 governance and the slice plan."
- "Produce an audit report showing whether WI-004 acceptance criteria are actually met."
- "Check that characterization baselines + parity matrix links are valid and governance gates pass."
- "Verify route-fence wasn’t flipped early and CI contract still matches verification-contract.yml."

### SHOULD NOT trigger this skill
- "Implement WI-00X for me." (use implementation/planning skills)
- "Refactor this module." (use refactor/quality skills)
- "Write new governance policy." (out of scope for Track 1 audit)

## References and resources (repo-local)

Authoritative Track 1 governance and plan artifacts:
- `project/verification-contract.yml` — verification commands + CI job requirements + LOC policy
- `project/parity-matrix.md` — behavior inventory + linkage ownership
- `project/route-fence.md` — strangler routing plan table
- `plans/v1-plan.md` — Track 1 blueprint, hard contracts, gates, and slice policy
- `WORK_ITEMS.md` and `plans/WI-*.md` — slice ordering + acceptance criteria
- `docs/TECHNICAL_NOTES.md` + `README.md` — runtime and workflow context

Skill-design guidance used to structure this runbook:
- `designing-skill-md-deep-research-report.md`

## Changelog
- 1.0.0 (2026-03-05): Initial governance + slice-plan audit runbook for JFIN Track 1.
```
