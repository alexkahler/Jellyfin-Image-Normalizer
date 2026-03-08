# Slice 24 Audit (A-08)

## slice id and title
- Slice id: `A-08`
- Title: `Same-SHA CI proof + GG-008 gate`
- Audit date: `2026-03-08`
- Auditor scope: evidence review only

## verdict
**Noncompliant (required CI job failure)** for GG-008 closure.

- GG-001 evidence condition is satisfied: local governance gate passes on current HEAD.
- GG-008 closure condition is not satisfied: canonical same-SHA CI run exists, but required job `quality` failed.
- Theme A remains **open** per `track-1-theme-a-iteration-roadmap.md` done/open rule.

## what changed
- A-08 unblock remediation was applied: `.github/workflows/ci.yml` now triggers on branch `v1/thm-a-governance-contract-posture-recovery`.
- Same-SHA CI evidence was recollected for current HEAD `7e837f93826e44b3a0a955a7fab2a956192dd58a`.
- `project/v1-slices-reports/slice-24/a08-ci-evidence.json` was updated with canonical run and job results.
- No `src/` runtime code changes were made.

## acceptance checklist
- [x] Local HEAD SHA captured.
- [x] Local `verify_governance.py --check all` passes on the same SHA.
- [x] Same-SHA canonical workflow `.github/workflows/ci.yml` (`CI`) run identified.
- [ ] Required jobs `test`, `security`, `quality`, `governance` all `success`.
- [x] Evidence includes run URL, run ID, workflow identity, head SHA, and per-job conclusions.
- [x] Fail-closed rule applied because one required job failed.

## verification commands and results
- `git rev-parse HEAD`
  - Result: `7e837f93826e44b3a0a955a7fab2a956192dd58a`.
- `\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`
  - Result: **PASS** (warnings only).
- `Invoke-RestMethod https://api.github.com/repos/alexkahler/Jellyfin-Image-Normalizer/actions/runs?head_sha=7e837f93826e44b3a0a955a7fab2a956192dd58a&per_page=20`
  - Result: canonical run found: `run_id=22809696578`, `status=completed`, `conclusion=failure`, `run_url=https://github.com/alexkahler/Jellyfin-Image-Normalizer/actions/runs/22809696578`.
- `Invoke-RestMethod https://api.github.com/repos/alexkahler/Jellyfin-Image-Normalizer/actions/runs/22809696578/jobs?per_page=100`
  - Result: required jobs
    - `test=success`
    - `security=success`
    - `quality=failure`
    - `governance=success`
- `Invoke-RestMethod https://api.github.com/repos/alexkahler/Jellyfin-Image-Normalizer/actions/jobs/66164345190`
  - Result: failing job `quality`; failing step `Run ruff format check`.
- `.\.venv\Scripts\python.exe -m ruff format --check .`
  - Result: **FAIL**; 15 files would be reformatted (including `src/jfin/backup.py`, `src/jfin/cli.py`, `src/jfin/pipeline.py`, and related extracted modules), consistent with CI `quality` failure cause.
- `git diff --numstat -- src`
  - Result: no output (A-08 remained evidence-only for runtime code).

## LOC / governance status
- Governance aggregate check: **PASS with warnings**.
- LOC policy status:
  - `src/` blocker policy: **PASS**.
  - `tests/` policy: **WARN-only**, non-blocking.
- CI required jobs contract (`project/verification-contract.yml`):
  - `test`, `security`, `quality`, `governance`.
- GG-008 status: **OPEN** because required job set is not fully successful.

## behavior-preservation assessment
- A-08 remained evidence/governance-only.
- No `src/` behavior changes were introduced in this pass.
- Safety invariants are unchanged.

## issues found
- **AUD-A08-001 (Blocker): Required same-SHA CI job failure**
  - Criteria violated: Theme A A-08/GG-008 requires all required jobs successful on same SHA.
  - Evidence: run `22809696578` on SHA `7e837f93826e44b3a0a955a7fab2a956192dd58a` has `quality=failure`.
  - Impact: GG-008 cannot close; Theme A cannot close.
  - Required remediation:
    1. Fix `quality` failure cause (`Run ruff format check`; local check currently reports 15 files needing formatting).
    2. Push updated SHA.
    3. Re-collect same-SHA CI proof showing all required jobs `success`.

## whether fixes were required
Yes. One fix was applied (CI trigger scope in `ci.yml`), which resolved the "no run" blocker. Additional fixes are still required because required job `quality` failed.

## final closure recommendation
- **Do not close Slice 24 (A-08) yet.**
- Keep GG-008 and Theme A **open**.
- Re-run A-08 closure gate only after required jobs are all successful on the same SHA.
