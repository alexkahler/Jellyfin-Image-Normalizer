# Track-1 Theme A Iteration Roadmap (Final Revision)

Target file: `project/v1-slices-reports/audits/track-1-theme-a-iteration-roadmap.md`  
Date: 2026-03-07  
Theme: **A - Governance Contract Posture Recovery**  
Gaps: **GG-001**, **GG-008**

## Summary
- This is a **roadmap and closure contract**, not a fixed implementation design.
- Later high-coupling slices are explicitly **provisional** and must be revalidated after each prior slice.
- GG-008 proof standard is now normalized to one auditable same-SHA evidence contract.

## SECTION 1 — Theme A Iteration Roadmap

### Theme A done/open rule
Theme A is **done** only when both are closed:
1. **GG-001 closed:** `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` passes, and all Python files under **`src/`** satisfy LOC contract (`<=300`).
2. **GG-008 closed:** same commit SHA has CI evidence for required jobs from `project/verification-contract.yml` (`test`, `security`, `quality`, `governance`) all successful.

Theme A remains **open** if either condition is not met.  
If same-SHA CI linkage cannot be proven, label **insufficient evidence**, keep **GG-008 open**, and keep Theme A **open**.

### Non-regression guardrails (theme-wide)
- No architecture redesign.
- No route flips and no route-fence semantics changes.
- No CLI contract redesign and no config semantics redesign.
- Dry-run dual gate behavior must remain preserved.
- Backdrop/restore safety behavior must remain preserved.
- Architecture check must be non-regressing (`--check architecture` must pass).

### Slice ordering with revalidation gates
Ordered slices:
1. A-01 Imaging LOC closure.
2. A-02 Backup LOC closure.
3. A-03 Medium-coupling closure slot 1 (adaptive: `config.py` or `client.py`).
4. A-04 Medium-coupling closure slot 2 (adaptive: remaining of `config.py` / `client.py`).
5. A-05 High-coupling closure slot 1 (adaptive: `cli.py` or `pipeline.py`).
6. A-06 High-coupling closure slot 2 (adaptive: remaining high-coupling blocker).
7. A-07 Residual blocker closure + GG-001 closure gate.
8. A-08 Same-SHA CI proof + GG-008 closure gate.

Dependencies:
- A-03 starts only after A-01 and A-02 are complete.
- A-05 starts only after A-03 and A-04 are complete.
- A-07 starts only after A-05 and A-06 are complete.
- A-08 starts only after A-07 is complete.

### Revalidation rule for provisional slices (material change)
After each slice from A-03 onward, run a revalidation gate before selecting the next slice target:
- Recompute blockers via `verify_governance.py --check loc`.
- If a module touched in prior slice is still >300 LOC, next slice must continue that module first.
- Otherwise choose next target by tier rule:
  - Medium tier first (`config.py`, `client.py`), then high tier (`cli.py`, `pipeline.py`).
  - Within tier, choose higher LOC overage first.
- If projected work violates slice policy (`>150` net `src/` LOC without justification, or verification >10 min), split into `A-xa`, `A-xb` before implementation.

This keeps roadmap intent stable while preventing over-commitment on high-risk seams.

### Same-SHA CI evidence standard (normalized)
Accepted GG-008 proof must include all of the following:
- `commit_sha` from `git rev-parse HEAD`.
- CI run identity proving canonical workflow is `.github/workflows/ci.yml` (workflow `CI`).
- Run `headSha` equals `commit_sha`.
- Job results for required jobs: `test`, `security`, `quality`, `governance`, all `success`.
- Evidence artifact in roadmap report with run URL, run ID, workflow identity, head SHA, and per-job conclusions.

Accepted retrieval methods:
- Primary: `gh run` / `gh api` machine-readable JSON.
- Fallback: GitHub REST API JSON with equivalent fields.
- Anything else is non-canonical for GG-008 closure and must be marked **insufficient evidence**.

## SECTION 2 — Slice Work Item Drafts

### A-01 — Imaging LOC Closure
## 1. Objective
Close the `src/jfin/imaging.py` LOC blocker with behavior-preserving seam extraction.

## 2. In-scope / Out-of-scope
In-scope: `src/jfin/imaging.py` and at most one adjacent helper module.  
Out-of-scope: pipeline orchestration changes, CLI/config semantics changes, route-fence changes.

## 3. Public interfaces affected
Existing `jfin.imaging` function signatures remain compatible.

## 4. Acceptance criteria
- `src/jfin/imaging.py` is `<=300` LOC.
- No touched file under `src/` exceeds 300 LOC.
- Net `src/` LOC delta is `<=150` unless justified in WI.
- Imaging tests and imaging characterization pass.

## 5. Verification commands (<10 min)
- `@('src/jfin/imaging.py') | % { "{0}:{1}" -f $_, (Get-Content $_).Length }`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_imaging.py`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/imaging_contract`
- `git diff --numstat -- src`

## 6. Rollback step
`git revert <A-01 commit>` and rerun A-01 verification.

## 7. Behavior-preservation statement
Preserved. Internal structural extraction only.

---

### A-02 — Backup LOC Closure
## 1. Objective
Close the `src/jfin/backup.py` LOC blocker with behavior-preserving seam extraction.

## 2. In-scope / Out-of-scope
In-scope: `src/jfin/backup.py` and at most one adjacent helper module.  
Out-of-scope: restore semantics redesign, route-fence changes.

## 3. Public interfaces affected
Restore entrypoints remain signature-compatible.

## 4. Acceptance criteria
- `src/jfin/backup.py` is `<=300` LOC.
- No touched `src/` file exceeds 300 LOC.
- Net `src/` LOC delta is `<=150` unless justified in WI.
- Restore safety tests pass.
- `--check architecture` passes.

## 5. Verification commands (<10 min)
- `@('src/jfin/backup.py') | % { "{0}:{1}" -f $_, (Get-Content $_).Length }`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_backup.py`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/safety_contract/test_safety_contract_restore.py`
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture`
- `git diff --numstat -- src`

## 6. Rollback step
`git revert <A-02 commit>` and rerun A-02 verification.

## 7. Behavior-preservation statement
Preserved. Restore behavior remains contract-equivalent.

---

### A-03 — Medium-Coupling Closure Slot 1 (Adaptive)
## 1. Objective
Close one medium-coupling LOC blocker (`src/jfin/config.py` or `src/jfin/client.py`) selected by revalidation rule.

## 2. In-scope / Out-of-scope
In-scope: selected module + at most one adjacent helper module.  
Out-of-scope: the other medium-coupling blocker unless needed for compile/import fix.

## 3. Public interfaces affected
Selected module’s public signatures remain compatible.

## 4. Acceptance criteria
- Selected module is `<=300` LOC.
- No touched `src/` file exceeds 300 LOC.
- Net `src/` LOC delta is `<=150` unless justified in WI.
- Module-specific regression suite passes.
- `--check architecture` passes.

## 5. Verification commands (<10 min)
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`
- If selected is `config.py`: run `tests/test_config.py` and `tests/characterization/config_contract`.
- If selected is `client.py`: run `tests/test_client.py`, `tests/test_discovery.py`, and `tests/characterization/safety_contract/test_safety_contract_api.py`.
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture`
- `git diff --numstat -- src`

## 6. Rollback step
`git revert <A-03 commit>` and rerun A-03 verification.

## 7. Behavior-preservation statement
Preserved. No CLI/config/API contract redesign.

---

### A-04 — Medium-Coupling Closure Slot 2 (Adaptive)
## 1. Objective
Close the remaining medium-coupling LOC blocker not closed in A-03.

## 2. In-scope / Out-of-scope
In-scope: remaining medium module + at most one adjacent helper module.  
Out-of-scope: high-coupling modules except import-fix touch-ups.

## 3. Public interfaces affected
Remaining medium module public signatures remain compatible.

## 4. Acceptance criteria
- Remaining medium module is `<=300` LOC.
- No touched `src/` file exceeds 300 LOC.
- Net `src/` LOC delta is `<=150` unless justified in WI.
- Relevant medium-module regression suite passes.
- `--check architecture` passes.

## 5. Verification commands (<10 min)
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`
- Run medium-module test matrix for selected module (same matrix as A-03).
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture`
- `git diff --numstat -- src`

## 6. Rollback step
`git revert <A-04 commit>` and rerun A-04 verification.

## 7. Behavior-preservation statement
Preserved. Medium-coupling closure only; contracts preserved.

---

### A-05 — High-Coupling Closure Slot 1 (Adaptive, Provisional)
## 1. Objective
Close one high-coupling LOC blocker (`src/jfin/cli.py` or `src/jfin/pipeline.py`) selected by revalidation rule.

## 2. In-scope / Out-of-scope
In-scope: selected high-coupling module + at most one adjacent helper module.  
Out-of-scope: route flips, route-fence artifact changes, architecture redesign.

## 3. Public interfaces affected
CLI/pipeline external behavior remains compatibility-equivalent.

## 4. Acceptance criteria
- Selected high-coupling module is `<=300` LOC.
- No touched `src/` file exceeds 300 LOC.
- Net `src/` LOC delta is `<=150` unless justified in WI.
- High-coupling module regression suite passes.
- `--check architecture` passes.
- If closure cannot meet budget/time, split before merge (`A-05a`, `A-05b`).

## 5. Verification commands (<10 min)
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`
- If selected is `cli.py`: run `tests/test_jfin.py`, `tests/characterization/cli_contract`, `tests/test_route_fence_runtime.py`.
- If selected is `pipeline.py`: run targeted `tests/test_pipeline.py -k "<changed flows>"` and `tests/characterization/safety_contract/test_safety_contract_pipeline.py`.
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture`
- `git diff --numstat -- src`

## 6. Rollback step
`git revert <A-05 commit>` and rerun A-05 verification.

## 7. Behavior-preservation statement
Preserved. No route flips and no control-plane semantic drift.

---

### A-06 — High-Coupling Closure Slot 2 (Adaptive, Provisional)
## 1. Objective
Close the remaining high-coupling LOC blocker not closed in A-05.

## 2. In-scope / Out-of-scope
In-scope: remaining high-coupling module + at most one adjacent helper module.  
Out-of-scope: unrelated module cleanup.

## 3. Public interfaces affected
Remaining high-coupling module external behavior remains compatible.

## 4. Acceptance criteria
- Remaining high-coupling module is `<=300` LOC.
- No touched `src/` file exceeds 300 LOC.
- Net `src/` LOC delta is `<=150` unless justified in WI.
- Relevant high-coupling regression suite passes.
- `--check architecture` passes.
- If closure cannot meet budget/time, split before merge (`A-06a`, `A-06b`).

## 5. Verification commands (<10 min)
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`
- Run high-module test matrix for selected module (same matrix as A-05).
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture`
- `git diff --numstat -- src`

## 6. Rollback step
`git revert <A-06 commit>` and rerun A-06 verification.

## 7. Behavior-preservation statement
Preserved. High-risk closure with compatibility and safety invariants preserved.

---

### A-07 — Residual Blocker Closure + GG-001 Gate
## 1. Objective
Resolve any remaining `src/` LOC blockers and close GG-001.

## 2. In-scope / Out-of-scope
In-scope: only residual blockers reported by `--check loc`; may be evidence-only if none remain.  
Out-of-scope: new refactors unrelated to remaining blockers.

## 3. Public interfaces affected
None expected unless required by residual closure.

## 4. Acceptance criteria
- All Python files under `src/` are `<=300` LOC.
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` passes.
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture` passes.
- GG-001 marked closed with command evidence.

## 5. Verification commands (<10 min)
- `Get-ChildItem src -Recurse -Filter *.py | % { "{0}:{1}" -f $_.FullName, (Get-Content $_.FullName).Length }`
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture`
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`

## 6. Rollback step
`git revert <A-07 commit>` and rerun A-07 verification.

## 7. Behavior-preservation statement
Preserved. This slice closes governance posture, not product behavior.

---

### A-08 — Same-SHA CI Proof + GG-008 Gate
## 1. Objective
Close GG-008 by attaching canonical same-SHA CI proof for required jobs.

## 2. In-scope / Out-of-scope
In-scope: evidence retrieval, validation, and attachment to Theme A roadmap report.  
Out-of-scope: runtime refactor, governance redesign.

## 3. Public interfaces affected
Governance evidence/closure artifact only.

## 4. Acceptance criteria
- `commit_sha` captured from local HEAD.
- Local `verify_governance --check all` passes on that SHA.
- CI evidence proves workflow `.github/workflows/ci.yml` run for same SHA.
- Required jobs (`test`, `security`, `quality`, `governance`) all `success`.
- Evidence table includes run URL, run ID, workflow identity, head SHA, and job conclusions.
- If any element missing or ambiguous: label **insufficient evidence**, GG-008 remains open, Theme A remains open.

## 5. Verification commands (<10 min)
- `$sha = git rev-parse HEAD`
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`
- `gh run list --workflow CI --commit $sha --json databaseId,headSha,workflowName,status,conclusion,url --limit 10`
- `gh run view <run_id> --json headSha,jobs,url`

## 6. Rollback step
Remove/revert closure claim and evidence attachment if same-SHA proof is invalidated.

## 7. Behavior-preservation statement
Preserved. Evidence-only closure step.

## Assumptions
- High-coupling closure slices are intentionally provisional and must be revalidated at each gate.
- Any unresolved pre-existing CI issue that blocks required-job success keeps GG-008 open until corrected and reproved on same SHA.

## SECTION 3 - Theme A Closure Evidence (Slice-33)

Date: 2026-03-08

### GG-001 closure evidence
- `git rev-parse HEAD` -> `c77a57bccf24d70fcf5b9a1784f3075ab8dd01c7`
- `python project/scripts/verify_governance.py --check all` -> PASS (warnings only)
- Interpretation: all `src/` anti-evasion/LOC blockers are cleared; GG-001 is closed.

### GG-008 same-SHA CI evidence
- workflow name: `CI`
- workflow path: `.github/workflows/ci.yml`
- run id: `22826331766`
- run URL: `https://github.com/alexkahler/Jellyfin-Image-Normalizer/actions/runs/22826331766`
- run head SHA: `c77a57bccf24d70fcf5b9a1784f3075ab8dd01c7`
- run status/conclusion: `completed/success`

Required jobs:
- `test`: success
- `security`: success
- `quality`: success
- `governance`: success

Interpretation: GG-008 same-SHA proof contract is satisfied.

### Theme A status
- GG-001: closed
- GG-008: closed
- Theme A: closed
