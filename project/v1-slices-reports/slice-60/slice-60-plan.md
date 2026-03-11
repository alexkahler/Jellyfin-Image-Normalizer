# Slice 60 Plan v3 (Final) - Readiness Claim Activation for `config_init|n/a` (`pending -> ready`, keep `route=v0`)

Date: 2026-03-11  
Branch: feat/v1-overhaul  
Local SHA: 19bd182358b64fcad055075cf3be4e9b2f57bd3d

## Slice ID/title
- Slice 60
- Readiness claim activation for `config_init|n/a` (`parity_status: pending -> ready`) with `route=v0` unchanged

## Goal/objective
- Activate readiness for exactly one route-fence row: `config_init|n/a`.
- Apply one governance mutation only: `parity_status: pending -> ready`.
- Preserve row invariants: `route=v0` and `owner_slice=Slice-57`.
- Keep scope tightly bounded to one objective to avoid context rot.

## Planning worker boundary (this turn)
- Planning worker writes only `project/v1-slices-reports/slice-60/slice-60-plan.md`.
- Planning worker does not edit `WORK_ITEMS.md`.

## Worker responsibility split (execution phase)
- Implementation worker:
  - may edit only `project/route-fence.md` and `project/route-fence.json` for the single-row readiness activation
  - may write only `project/v1-slices-reports/slice-60/slice-60-implementation.md` as execution evidence
- Audit worker:
  - may write only `project/v1-slices-reports/slice-60/slice-60-audit.md`
- Orchestration thread only:
  - may update `WORK_ITEMS.md` only after explicit audit PASS

## Baseline snapshot (planning time)
- Completed through Slice 59 (audit PASS).
- Current target row:
  - `command=config_init`, `mode=n/a`, `route=v0`, `owner_slice=Slice-57`, `parity_status=pending`
- Prerequisites confirmed in-repo:
  - workflow coverage cell exists for `config_init|n/a`
  - runtime-gate targets include `test_cli_generate_config_blocks_operational_flags`
- Readiness counters before this slice:
  - claimed/validated: `3/3`
- Expected movement for this slice:
  - claimed/validated: `3/3 -> 4/4`

## In-scope files (Slice 60 execution)
- `project/route-fence.md` (single-row parity status change only)
- `project/route-fence.json` (single-row parity status change only)
- `project/v1-slices-reports/slice-60/slice-60-plan.md`
- `project/v1-slices-reports/slice-60/slice-60-implementation.md`
- `project/v1-slices-reports/slice-60/slice-60-audit.md`

## Out-of-scope files/work
- `project/workflow-coverage-index.json`
- `project/verification-contract.yml`
- `project/parity-matrix.md`
- `.github/workflows/ci.yml`
- Any runtime code under `src/`
- Any test source under `tests/` (including characterization suites)
- Any route mutation (`v0 -> v1`) for any row
- Any owner change (`owner_slice`) for any row
- Any non-target row mutation in route-fence artifacts
- Any `WORK_ITEMS.md` update before audit PASS

## Acceptance criteria
1. Exactly one governance mutation exists in route-fence artifacts for target row `config_init|n/a`: `parity_status` changes `pending -> ready`.
2. Target row invariants are preserved in both route-fence artifacts:
   - `route` remains `v0`
   - `owner_slice` remains `Slice-57`
   - `command` and `mode` remain `config_init` and `n/a`
3. No other route-fence row is changed.
4. No out-of-scope artifact is edited (workflow coverage, verification contract, parity matrix, CI workflow, runtime code/tests).
5. Governance checks pass: `--check parity`, `--check readiness`, `--check all`.
6. Readiness counters advance exactly from `3/3` to `4/4`.
7. Slice 60 implementation and audit reports exist, and audit is explicitly PASS before any orchestration update to `WORK_ITEMS.md`.

## Binary success condition
Slice 60 is successful only if the sole governance mutation is `config_init|n/a parity_status: pending -> ready` in both route-fence artifacts, while `route=v0` and `owner_slice=Slice-57` remain unchanged, readiness advances to `4/4`, required governance checks pass, scope stays in-bounds, and audit is explicitly PASS before any `WORK_ITEMS.md` update.

## Fail-close criteria
- Any route mutation on any row.
- Any owner mutation on any row.
- Any parity mutation outside `config_init|n/a`.
- Any multi-row route-fence mutation.
- Any out-of-scope file edit.
- Readiness counters do not advance exactly to `INFO: Route readiness claims: 4` and `INFO: Route readiness claims validated: 4`.
- Missing Slice 60 audit report or audit not explicitly PASS.
- Any `WORK_ITEMS.md` update before explicit audit PASS.

## Implementation steps (for Slice 60 execution worker)
1. Capture baseline proof for `config_init|n/a` in `project/route-fence.md` and `project/route-fence.json`.
2. Reconfirm prerequisites are already present (workflow cell and runtime-gate target) without editing those artifacts.
3. Update only target-row `parity_status` from `pending` to `ready` in both route-fence artifacts.
4. Capture post-change proof showing `route=v0` and `owner_slice=Slice-57` unchanged.
5. Capture diff-scope proof and confirm no out-of-scope edits.
6. Run governance verification: `parity`, `readiness`, `all`.
7. Write `slice-60-implementation.md` with before/after row evidence, readiness counters, and command output summary.
8. Hand off for independent audit (`slice-60-audit.md`).

## Minimum evidence commands (PowerShell)
```powershell
# Target row proof (before/after)
Select-String -Path project/route-fence.md -Pattern '^\|\s*config_init\s*\|\s*n/a\s*\|'
$rf = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rf.rows |
  Where-Object { $_.command -eq 'config_init' -and $_.mode -eq 'n/a' } |
  Format-List command, mode, route, owner_slice, parity_status

# Prerequisite presence proof (no mutation expected)
$wc = Get-Content -Raw project/workflow-coverage-index.json | ConvertFrom-Json
$wc.cells.PSObject.Properties.Name | Where-Object { $_ -eq 'config_init|n/a' }
Select-String -Path project/verification-contract.yml -Pattern 'test_cli_generate_config_blocks_operational_flags'

# Diff-scope constraints
git diff --name-only
git diff -- project/route-fence.md project/route-fence.json
git diff -- project/workflow-coverage-index.json project/verification-contract.yml project/parity-matrix.md .github/workflows/ci.yml WORK_ITEMS.md

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

Expected proof points:
- Before: target row is `route=v0`, `owner_slice=Slice-57`, `parity_status=pending`.
- After: target row is `route=v0`, `owner_slice=Slice-57`, `parity_status=ready`.
- `git diff --name-only` remains limited to allowed route-fence files (plus slice report artifacts).
- Before audit, implementation-tracked changes are limited to:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/v1-slices-reports/slice-60/slice-60-implementation.md`
- No diff output for out-of-scope governance artifacts listed above.
- Readiness output advances to:
  - `INFO: Route readiness claims: 4`
  - `INFO: Route readiness claims validated: 4`

## Risks/guardrails
- Risk: accidental route or owner drift while updating parity status.
  Guardrail: fail closed unless before/after evidence proves `route=v0` and `owner_slice=Slice-57` unchanged.
- Risk: unintended multi-row mutation in route-fence artifacts.
  Guardrail: require one-row targeted diff proof for `config_init|n/a` only.
- Risk: hidden scope creep into prerequisite artifacts.
  Guardrail: prerequisites are verification-only in this slice; edits to workflow coverage/runtime-gate artifacts are prohibited.
- Risk: closure claimed without audit discipline.
  Guardrail: no `WORK_ITEMS.md` update until explicit Slice 60 audit PASS.

## Suggested next slice
- Slice 61: decision-only progression record for `config_init|n/a` (no route flip), contingent on Slice 60 audit PASS and stable readiness evidence.
- Any `v0 -> v1` proposal for `config_init|n/a` is deferred to later same-SHA-evidence/progression slices.

## Explicit split rule if scope grows too large
- Stop and split immediately if any of the following becomes necessary:
  - edits outside target row in `project/route-fence.md` or `project/route-fence.json`
  - any change to workflow coverage, runtime-gate contract, parity matrix, CI workflow, runtime code, or test sources
  - any owner change or route change for `config_init|n/a`
- Keep Slice 60 limited to one objective: readiness activation (`pending -> ready`) for `config_init|n/a` with `route=v0` preserved.
