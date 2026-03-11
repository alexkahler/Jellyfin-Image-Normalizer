# Slice 58 Plan v3 (Final) - Workflow Coverage Expansion for `config_init|n/a`

Date: 2026-03-11
Branch: feat/v1-overhaul
Local SHA: 3b93cc6e22945341c74da77266d886e50ebdb0dc

## Slice ID and title
- Slice 58
- Workflow-coverage expansion for `config_init|n/a` (no route flip, no parity flip)

## Goal/objective
- Add exactly one governed workflow-coverage cell for `config_init|n/a`.
- Bind the cell to existing characterization/parity evidence:
  - parity anchor: `CLI-GENCFG-001`
  - owner test anchor: `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_generate_config_blocks_operational_flags`
- Preserve route-fence row invariants for `config_init|n/a`: `route=v0`, `owner_slice=Slice-57`, `parity_status=pending`.
- Keep scope narrowly bounded to one workflow-coverage objective to avoid context rot.

## Worker responsibility split (execution phase)
- Implementation worker:
  - may edit only `project/workflow-coverage-index.json` for a single-cell addition (`config_init|n/a`)
  - may write only `project/v1-slices-reports/slice-58/slice-58-implementation.md` as execution evidence
- Audit worker:
  - may write only `project/v1-slices-reports/slice-58/slice-58-audit.md`
- Orchestration only:
  - may update `WORK_ITEMS.md` only after explicit audit PASS

## Planning worker boundary (this turn)
- Planning worker writes only `project/v1-slices-reports/slice-58/slice-58-plan.md`.
- Planning worker does not modify `WORK_ITEMS.md`.

## Baseline snapshot (planning time)
- Current completed slice: Slice 57.
- Route-fence target row currently:
  - `command=config_init`, `mode=n/a`, `route=v0`, `owner_slice=Slice-57`, `parity_status=pending`.
- Workflow sequence counters (from governance characterization check):
  - configured/validated: `4/4`
  - open debts: `0`
- Readiness claims (from governance readiness check):
  - claimed/validated: `3/3`
- Expected movement for this slice:
  - workflow sequence configured/validated: `4/4 -> 5/5`
  - open debts: `0 -> 0`
  - readiness claims: remain `3/3`

## In-scope files (Slice 58 execution)
- `project/workflow-coverage-index.json` (single-cell addition only)
- `project/v1-slices-reports/slice-58/slice-58-plan.md`
- `project/v1-slices-reports/slice-58/slice-58-implementation.md`
- `project/v1-slices-reports/slice-58/slice-58-audit.md`

## Out-of-scope files/work
- `project/route-fence.md`
- `project/route-fence.json`
- `project/parity-matrix.md`
- `project/verification-contract.yml`
- `.github/workflows/ci.yml`
- Any runtime code under `src/`
- Any test source under `tests/` (owner test anchor is reused, not edited)
- Any route change (`v0 -> v1`) or parity-status change (`pending -> ready`)
- Any non-target workflow-cell mutation (add/remove/rewire for cells other than `config_init|n/a`)
- Any `WORK_ITEMS.md` update before audit PASS

## Acceptance criteria
1. Exactly one new workflow cell is added: `config_init|n/a` in `project/workflow-coverage-index.json`.
2. New cell references existing evidence anchors exactly:
   - `required_parity_ids` includes `CLI-GENCFG-001`.
   - `required_owner_tests` includes `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_generate_config_blocks_operational_flags`.
3. Route-fence row for `config_init|n/a` remains unchanged (`route=v0`, `owner_slice=Slice-57`, `parity_status=pending`).
4. No other workflow cell is added/removed/rewired in `project/workflow-coverage-index.json`.
5. Governance checks pass without regression: `--check characterization`, `--check parity`, `--check readiness`, `--check all`.
6. Workflow counters move exactly `4/4 -> 5/5` with open debts unchanged at `0`.
7. Readiness claims remain unchanged at `3/3`.
8. Slice 58 implementation and audit reports exist, and audit is explicitly PASS before any `WORK_ITEMS.md` update.

## Binary success condition
Slice 58 is successful only if the sole governance mutation is one new `config_init|n/a` workflow cell with required anchors (`CLI-GENCFG-001`, `test_cli_generate_config_blocks_operational_flags`), route-fence invariants remain unchanged, workflow counters advance exactly `4/4 -> 5/5` with debts `0`, readiness remains `3/3`, governance checks pass, and audit is explicitly PASS before any orchestration update.

## Fail-close criteria
- Any route mutation on any row.
- Any parity-status mutation on any row.
- Any workflow-coverage mutation outside the target cell `config_init|n/a`.
- Any out-of-scope file edit.
- Missing audit report or audit not explicitly PASS.
- Any `WORK_ITEMS.md` change before audit PASS.
- Any governance check failure for `characterization`, `parity`, `readiness`, or `all`.

## Implementation steps (for Slice 58 execution worker)
1. Reconfirm baseline invariants for `config_init|n/a` in route-fence markdown and JSON.
2. Add one new cell `config_init|n/a` to `project/workflow-coverage-index.json` using the existing parity/test anchors.
3. Populate evidence/ordering/severity/future-split-debt fields to match current schema and neighboring cell conventions.
4. Capture target-cell proof and diff-scope proof (single-cell bounded change).
5. Run governance verification commands and record results.
6. Write `slice-58-implementation.md` with baseline, mutation proof, expected-vs-actual counters, and command outputs.
7. Hand off for independent audit report (`slice-58-audit.md`).

## Minimum evidence commands (PowerShell)
```powershell
# Route-fence target row proof (run before and after)
Select-String -Path project/route-fence.md -Pattern '^\|\s*config_init\s*\|\s*n/a\s*\|'
$rf = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rf.rows |
  Where-Object { $_.command -eq 'config_init' -and $_.mode -eq 'n/a' } |
  Format-List command, mode, route, owner_slice, parity_status

# Workflow target-cell proof (after mutation)
$wc = Get-Content -Raw project/workflow-coverage-index.json | ConvertFrom-Json
$cell = $wc.cells.'config_init|n/a'
$cell | ConvertTo-Json -Depth 8
$cell.required_parity_ids
$cell.required_owner_tests

# Diff-scope constraints
git diff --name-only
git diff -- project/workflow-coverage-index.json
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/verification-contract.yml .github/workflows/ci.yml WORK_ITEMS.md

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

Expected proof points:
- Before and after, route-fence target row remains `route=v0`, `owner_slice=Slice-57`, `parity_status=pending`.
- `project/workflow-coverage-index.json` contains `cells['config_init|n/a']` with `CLI-GENCFG-001` and the owner test anchor.
- `git diff --name-only` stays within allowed execution-scope files only.
- Targeted diff confirms only intended workflow-cell addition in `project/workflow-coverage-index.json`.
- Governance check output shows:
  - workflow sequence configured/validated `4 -> 5`
  - workflow sequence open debts remains `0`
  - readiness claims remain `3/3`
  - all listed checks PASS

## Risks/guardrails
- Risk: accidental expansion beyond single-cell coverage update.
  Guardrail: fail closed if diff touches route-fence/parity/verification-contract/runtime/test artifacts.
- Risk: hidden route/parity movement while adding workflow coverage.
  Guardrail: explicitly assert unchanged `config_init|n/a` route-fence row before and after.
- Risk: weak evidence mapping (incorrect parity/test anchor).
  Guardrail: require exact anchors `CLI-GENCFG-001` and `test_cli_generate_config_blocks_operational_flags`.
- Risk: context rot from combining progression work in one slice.
  Guardrail: no readiness or route/parity flip work in Slice 58.

## Suggested next slice
- Slice 59: runtime-gate scope decomposition for `config_init|n/a` claim eligibility, adding owner test `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_generate_config_blocks_operational_flags` to runtime gate targets before any readiness activation/progression slice.

## Split rule if scope grows too large
- If any of the following become necessary, stop and split instead of widening Slice 58:
  - parity-matrix edits
  - route-fence edits
  - new/edited characterization tests
  - multiple workflow-cell additions
  - readiness-claim activation changes
- Keep Slice 58 limited to one governed workflow cell (`config_init|n/a`) plus slice report artifacts.
