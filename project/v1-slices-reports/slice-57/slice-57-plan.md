# Slice 57 Plan v3 (Final) - Ownership-Only Kickoff for `config_init|n/a`

Date: 2026-03-11
Branch: feat/v1-overhaul
Local SHA: aa7cb8c6d676702eac8053d28326ec90250dba1e

## Slice ID/title
- Slice 57
- Ownership-only kickoff for `config_init|n/a` (`owner_slice: WI-00X -> Slice-57`, no route flip)

## Goal/objective
- Replace placeholder ownership for `config_init|n/a` with concrete ownership metadata.
- Preserve route/readiness invariants for the row: `route=v0`, `parity_status=pending`.
- Keep the slice narrow and bounded to prevent context rot.

## Worker responsibility split
- Implementation worker:
  - may edit only `project/route-fence.md` and `project/route-fence.json` for the single owner change on `config_init|n/a`
  - writes only `project/v1-slices-reports/slice-57/slice-57-implementation.md` as the report artifact
- Audit worker:
  - writes only `project/v1-slices-reports/slice-57/slice-57-audit.md`
- Orchestration thread only:
  - may update `WORK_ITEMS.md` only after explicit audit PASS

## Baseline snapshot (planning time)
- Target row: `config_init|n/a` is currently `route=v0`, `owner_slice=WI-00X`, `parity_status=pending`.
- Prior completed slice: Slice 56.

## In-scope
- Single-row owner mutation for `config_init|n/a` in:
  - `project/route-fence.md`
  - `project/route-fence.json`
- Slice 57 reports:
  - `project/v1-slices-reports/slice-57/slice-57-plan.md`
  - `project/v1-slices-reports/slice-57/slice-57-implementation.md`
  - `project/v1-slices-reports/slice-57/slice-57-audit.md`

## Out-of-scope
- Any route mutation (`v0 -> v1` or otherwise).
- Any parity mutation (`pending -> ready` or otherwise).
- Any multi-row route-fence mutation.
- Any workflow coverage, parity matrix, verification contract, CI workflow, or runtime code/test edits.
- Any `WORK_ITEMS.md` update before audit PASS.

## Acceptance criteria
- Exactly one row changes in route-fence artifacts: `config_init|n/a`.
- Exact invariants are preserved on the target row:
  - `route` remains `v0`
  - `parity_status` remains `pending`
  - only `owner_slice` changes (`WI-00X -> Slice-57`)
- No other route-fence row is edited.
- Governance checks pass: `--check parity`, `--check readiness`, and `--check all`.
- Audit report exists and is explicitly PASS before any orchestration update.

## Binary success condition
Slice 57 closes successfully only if the sole governance mutation is `config_init|n/a owner_slice: WI-00X -> Slice-57` in both route-fence artifacts, all invariants hold (`route=v0`, `parity_status=pending`), diff scope stays in-bounds, required governance checks pass, and audit is explicitly PASS.

## Fail-close criteria
- Any route value mutation on any row.
- Any parity status mutation on any row.
- Any multi-row route-fence edit (more than the target row).
- Any out-of-scope file edits.
- Missing audit report or audit not explicitly PASS.
- Any `WORK_ITEMS.md` update before audit PASS.

## Implementation steps
1. Capture baseline proof for `config_init|n/a` in markdown and JSON route-fence artifacts.
2. Apply owner-only update in both route-fence artifacts.
3. Capture post-change proof for the same row.
4. Capture diff-scope proof and route-fence-targeted diff proof.
5. Run governance checks (`parity`, `readiness`, `all`) and record results.
6. Write implementation report; hand off for independent audit.

## Minimum evidence commands (PowerShell)
```powershell
# target row before/after proof (markdown + JSON)
Select-String -Path project/route-fence.md -Pattern '^\|\s*config_init\s*\|\s*n/a\s*\|'
$rf = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rf.rows | Where-Object { $_.command -eq 'config_init' -and $_.mode -eq 'n/a' } | Format-List

# diff scope proof
git diff --name-only
git diff -- project/route-fence.md project/route-fence.json

# governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

Expected proof points:
- Before: target row shows `owner_slice=WI-00X`, `route=v0`, `parity_status=pending`.
- After: target row shows `owner_slice=Slice-57` with `route=v0` and `parity_status=pending` unchanged.
- Route-fence-targeted diff shows owner-only change for one row.
- Before audit, modified files are limited to:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/v1-slices-reports/slice-57/slice-57-implementation.md`
- Governance checks above all PASS.

## Risks / guardrails
- Risk: accidental row drift in route-fence files.
  Guardrail: fail closed unless diff proves one-row owner-only mutation.
- Risk: slice overreach into readiness/route progression.
  Guardrail: split immediately if parity/route/workflow scope appears.

## Suggested next slice
- Slice 58: workflow-coverage expansion for `config_init|n/a` readiness path input (no route flip).

## Explicit split rule
If scope expands beyond owner-only mutation for `config_init|n/a` (for example parity flip, route flip, or workflow coverage edits), stop and split into subsequent slices instead of extending Slice 57.
