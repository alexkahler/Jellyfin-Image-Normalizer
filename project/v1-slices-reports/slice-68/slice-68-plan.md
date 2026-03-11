# Slice 68 Plan v3 (Final) - External-Unblock Prerequisite: Enable CI Trigger Coverage for `feat/v1-overhaul` (No Route Mutation)

Date: 2026-03-11  
Branch: `feat/v1-overhaul`
Planning review status: v1 reviewed, v2 reviewed, v3 final.

## 1) Slice ID and Title
- Slice 68
- External-unblock prerequisite: enable CI trigger coverage for `feat/v1-overhaul` (no route mutation)

## 2) Goal / Objective
Remove the discovered blocker that prevents same-SHA CI evidence collection on the working branch by adding `feat/v1-overhaul` to CI workflow trigger branches, while preserving required CI jobs and governance truth outside this explicit trigger-scope change.

## 3) In-Scope / Out-of-Scope
### In scope
- Update `.github/workflows/ci.yml` trigger branches for both:
  - `on.push.branches`
  - `on.pull_request.branches`
- Add branch `feat/v1-overhaul` only.
- Keep required CI job set unchanged: `test`, `security`, `quality`, `governance`.
- Produce slice reports (`plan`, `implementation`, `audit`).

### Out of scope
- Any route mutation (`project/route-fence.md` / `project/route-fence.json`).
- Any parity/workflow/verification-contract mutation outside explicit CI trigger scope.
- Any runtime/test code changes under `src/` or `tests/`.
- Any job-step logic changes in CI jobs.

## 4) Writable File Allowlist
- Planning worker: `project/v1-slices-reports/slice-68/slice-68-plan.md` only
- Implementation worker: `project/v1-slices-reports/slice-68/slice-68-implementation.md` and `.github/workflows/ci.yml` only
- Audit worker: `project/v1-slices-reports/slice-68/slice-68-audit.md` only
- Orchestration thread only (after audit PASS): `WORK_ITEMS.md`

## 5) Acceptance Criteria
1. `.github/workflows/ci.yml` includes `feat/v1-overhaul` in both push and pull-request branch trigger lists.
2. No other branch entries are added or removed in either trigger list beyond adding `feat/v1-overhaul`.
3. CI required jobs remain unchanged and still present: `test`, `security`, `quality`, `governance`.
4. No changes outside scoped files (`.github/workflows/ci.yml` + slice report artifacts + post-audit `WORK_ITEMS.md`).
5. Route-fence row for `config_init|n/a` remains unchanged (`v0 | Slice-57 | ready`).
6. Governance checks pass: `--check readiness`, `--check parity`, `--check all`.
7. Implementation report documents trigger change evidence and no-mutation diffs.
8. Audit report returns explicit PASS before `WORK_ITEMS.md` update.

## 6) Binary Success Condition
Slice 68 is successful only if trigger coverage is unblocked by adding `feat/v1-overhaul` to both CI trigger lists with no other trigger branch list mutations, required CI jobs remain intact, governance checks pass, and audit returns PASS before any `WORK_ITEMS.md` update.

## 7) Fail-Close Triggers
- Any branch addition/removal in trigger lists other than adding `feat/v1-overhaul`.
- Any mutation to route-fence, parity/workflow/verification-contract, runtime code, or tests.
- Any CI job rename/removal or job-step logic mutation.
- Missing implementation or audit report, or non-PASS audit verdict.
- `WORK_ITEMS.md` updated before audit PASS.

## 8) Implementation Steps
1. Capture baseline `ci.yml` trigger branch lists and required job names.
2. Edit `.github/workflows/ci.yml` to add `feat/v1-overhaul` under both push and pull_request branch arrays.
3. Verify no CI job names or job steps were modified.
4. Verify no other trigger branch entries were added or removed.
5. Capture protected-file diff proof (only allowed changes present).
6. Run governance checks (`readiness`, `parity`, `all`) and record outputs.
7. Write implementation report and hand off to audit worker.

## 9) Risk / Guardrails
- Risk: accidental broadening of CI triggers beyond required branch.
  - Guardrail: add only `feat/v1-overhaul`; no wildcard expansion in this slice.
- Risk: accidental CI job contract drift.
  - Guardrail: explicitly verify unchanged required job names and job definitions.
- Risk: hidden scope creep into governance/runtime artifacts.
  - Guardrail: protected-file diff checks must be explicit and empty outside approved scope.

## 10) Suggested Next Slice
- Slice 69:
  - If a same-SHA CI run becomes available for the target progression SHA, run progression-decision slice for `config_init|n/a` with required-job evidence.
  - If still unavailable, run external prerequisite diagnostics (repository/workflow permissions or CI settings) without repeating identical evidence-only continuation slices.

## 11) Verification Commands
```powershell
# Baseline snapshots
Select-String -Path .github/workflows/ci.yml -Pattern '^on:|^\s+pull_request:|^\s+push:|^\s+branches:'
Select-String -Path .github/workflows/ci.yml -Pattern '^\s{2}(test|security|quality|governance):'

# Route-fence unchanged proof
Select-String -Path project/route-fence.md -Pattern '^\|\s*config_init\s*\|\s*n/a\s*\|'
$rf = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rf.rows | Where-Object { $_.command -eq 'config_init' -and $_.mode -eq 'n/a' } |
  Select-Object command, mode, route, owner_slice, parity_status

# Scope/diff proof
git diff --name-only
git diff -- .github/workflows/ci.yml project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml WORK_ITEMS.md

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

## 12) Evidence and Reporting Outputs
- Plan: `project/v1-slices-reports/slice-68/slice-68-plan.md`
- Implementation: `project/v1-slices-reports/slice-68/slice-68-implementation.md`
- Audit: `project/v1-slices-reports/slice-68/slice-68-audit.md`

## 13) Split-if-too-large Rule
Stop immediately and split this work into follow-on slices if any of the following occurs:
- Scope drifts beyond the intended CI-trigger edit in `.github/workflows/ci.yml`.
- CI job logic changes (job names, steps, runner shape, or verification semantics) become necessary.
- Runtime/test/governance mutations are required beyond the explicit CI-trigger scope for this slice.

If a split is triggered, keep Slice 68 limited to documented evidence of the blocker and defer expanded changes to a dedicated prerequisite slice.
