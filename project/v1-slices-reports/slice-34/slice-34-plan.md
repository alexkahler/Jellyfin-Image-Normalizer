# Slice-34 Plan (v3 FINAL, implementation-ready)

## Slice Id and Title
- Slice id: `Slice-34`
- Slice title: `Theme B unblock: close run|backdrop readiness debt contract`
- Plan posture: implementation-ready planning artifact; no implementation completion claim.

## 1) Pre-slice baseline state
- Branch baseline: `v1/thm-b-route-fence-flip-readiness`.
- Baseline head at planning capture: `f6e05f17baf9c1db9ca241b7766e4a7ecb7251c8`.
- Governance baseline:
  - `verify_governance.py --check parity`: `PASS`
  - `verify_governance.py --check characterization`: `PASS`, `Workflow sequence open debts: 1`
  - `verify_governance.py --check readiness`: `PASS`, `Route readiness claims: 0`, `validated: 0`
- Target debt baseline (`project/workflow-coverage-index.json`, cell `run|backdrop`):
  - debt id: `DEBT-BACKDROP-ID-SPLIT-001`
  - status: `open`
  - `readiness_blocking: true`
  - closure: `type=parity_id_count_min`, `cell=run|backdrop`, `min_required=2`
  - current linkage is one backdrop parity ID only (`PIPE-BACKDROP-001`), so closure is not honest yet.
- Theme B closure criterion #3 evidence is currently missing:
  - there is no explicit targeted test proving readiness can evaluate at least one real `run|backdrop` claim candidate with closed debt and full linkage.

## 2) Exact in-scope files and exact out-of-scope files
In-scope files (exact):
- `project/workflow-coverage-index.json`
- `project/parity-matrix.md`
- `tests/characterization/baselines/safety_contract_baseline.json`
- `tests/characterization/safety_contract/test_safety_contract_pipeline_backdrop_split.py` (new file)
- `project/scripts/characterization_contract.py`
- `project/scripts/parity_contract.py`
- `tests/test_characterization_checks.py`
- `tests/_readiness_test_helpers.py`
- `tests/test_readiness_checks.py`
- `project/v1-slices-reports/slice-34/slice-34-plan.md`
- `project/v1-slices-reports/slice-34/slice-34-implementation.md`
- `project/v1-slices-reports/slice-34/slice-34-audit.md`

Out-of-scope files and changes (exact policy):
- `project/route-fence.md`
- `project/route-fence.json`
- Any route flip (`v0 -> v1`) in canonical route-fence artifacts.
- Any canonical route-fence `parity status` change (`pending -> ready`).
- Any canonical ownership WI replacement (`WI-00X` replacement is out-of-scope).
- Any multi-cell workflow expansion in `project/workflow-coverage-index.json`.
- Any runtime behavior change under `src/jfin/**`.
- Any enforcement weakening in `project/scripts/readiness_checks.py`, `project/scripts/characterization_checks.py`, or `project/scripts/governance_checks.py`.

## 3) Single targeted blocking debt item
- Target debt (only one): `DEBT-BACKDROP-ID-SPLIT-001` at workflow cell `run|backdrop`.
- No other debt closure, route activation, or breadth expansion is in scope.

## 4) Why this slice is small enough to avoid context rot
- One objective: honestly satisfy one existing closure contract for one existing workflow cell.
- Bounded contract-chain work:
  - one new backdrop parity ID,
  - one new baseline case,
  - one new owner test file,
  - one new parity-matrix row,
  - one workflow-cell linkage update,
  - fixture/helper updates needed to keep tests canonical.
- No route-fence artifact changes and no runtime-code edits.

## 5) Behavior-preservation obligations
- Preserve runtime behavior and safety semantics (`src/jfin/**` untouched).
- Preserve strict governance posture:
  - no severity downgrades,
  - no check bypasses,
  - no synthetic count inflation using unrelated parity IDs.
- Debt closure must be backed by real backdrop evidence linkage (`baseline` + `owner_test` + `parity_row` + `workflow_cell`).

## 6) Honest remediation path (no weakening of enforcement)
1. Add backdrop-specific parity behavior ID: `PIPE-BACKDROP-002`.
2. Add real safety baseline case:
   - file: `tests/characterization/baselines/safety_contract_baseline.json`
   - anchor: `PIPE-BACKDROP-002`
   - payload: real backdrop contract observations under safety schema.
3. Add new backdrop owner test:
   - file: `tests/characterization/safety_contract/test_safety_contract_pipeline_backdrop_split.py`
   - nodeid: `test_pipe_backdrop_002_characterization`.
4. Add parity-matrix linkage row:
   - file: `project/parity-matrix.md`
   - `behavior_id=PIPE-BACKDROP-002`
   - `baseline_source=tests/characterization/baselines/safety_contract_baseline.json#PIPE-BACKDROP-002`
   - `status=preserved`
   - `current_result=matches-baseline`
   - `owner_test=tests/characterization/safety_contract/test_safety_contract_pipeline_backdrop_split.py::test_pipe_backdrop_002_characterization`
5. Update required ID registries:
   - `project/scripts/parity_contract.py` (`REQUIRED_BEHAVIOR_IDS`)
   - `project/scripts/characterization_contract.py` (`SAFETY_BEHAVIOR_IDS` and derived required list)
6. Update workflow coverage linkage for `run|backdrop`:
   - `required_parity_ids` becomes exactly `PIPE-BACKDROP-001`, `PIPE-BACKDROP-002`
   - `required_owner_tests` contains both backdrop owner nodeids
   - keep closure contract object unchanged (`min_required=2` remains)
7. Close debt only after linkage is complete:
   - set `future_split_debt.status` to `closed` after steps 1-6 pass.
8. Add explicit Theme B closure criterion #3 evidence:
   - update readiness fixtures/helpers (`tests/test_characterization_checks.py`, `tests/_readiness_test_helpers.py`) to canonical two-ID backdrop contract,
   - add targeted readiness test in `tests/test_readiness_checks.py` that exercises a `run|backdrop` ready claim candidate with:
     - `route` remaining `v0` in canonical artifacts,
     - test-local row set to `parity_status=ready`,
     - closed debt,
     - both backdrop parity IDs and owner tests linked,
     - runtime mapping including both parity IDs,
   - assert readiness result has `claimed_rows == 1` and `validated_rows == 1` with no readiness errors.

## 7) Why no Theme C activation and no Theme D breadth expansion
- No Theme C activation in this slice:
  - no canonical route-fence markdown/json edits,
  - no canonical parity-status activation,
  - no ownership WI replacement,
  - no route flips.
- No Theme D breadth expansion:
  - workflow index remains exactly one cell (`run|backdrop`),
  - only min-required closure completion for that same cell is performed.
- Criterion #3 evidence uses targeted tests in isolated test repositories, not canonical route-fence activation.

## 8) Expected blocker contraction after success
Before -> after expectations:
- `Workflow sequence open debts`: `1 -> 0`.
- `DEBT-BACKDROP-ID-SPLIT-001`: `open -> closed`.
- `run|backdrop required_parity_ids`: `1 -> 2` with both IDs backdrop-specific and parity-backed.
- Theme B closure criterion #3 evidence: explicit targeted readiness claim-candidate test `PASS`.
- GG-004 blocking portion: `blocked -> unblocked`.
- Canonical readiness claims can remain `0` until Theme C; this slice proves evaluability via targeted readiness test coverage.

## 9) Exact verification commands for audit worker
```powershell
$ErrorActionPreference = 'Stop'
$env:PYTHONPATH='src'

# Branch and surface sanity
git rev-parse --abbrev-ref HEAD
git status --short
git diff --name-only

# New parity ID linkage must exist across all contract artifacts
rg -n "PIPE-BACKDROP-002" `
  project/workflow-coverage-index.json `
  project/parity-matrix.md `
  tests/characterization/baselines/safety_contract_baseline.json `
  tests/characterization/safety_contract/test_safety_contract_pipeline_backdrop_split.py `
  project/scripts/characterization_contract.py `
  project/scripts/parity_contract.py `
  tests/test_characterization_checks.py `
  tests/_readiness_test_helpers.py `
  tests/test_readiness_checks.py

# Targeted characterization tests (existing + new backdrop contract)
.\.venv\Scripts\python.exe -m pytest -q `
  tests/characterization/safety_contract/test_safety_contract_pipeline.py `
  tests/characterization/safety_contract/test_safety_contract_pipeline_backdrop_split.py

# Targeted canonical fixture/readiness tests for Theme B closure criterion #3
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_characterization_checks.py `
  tests/test_readiness_checks.py::test_readiness_evaluates_run_backdrop_real_claim_candidate_after_debt_closure

# Targeted governance checks before aggregate gate
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture

# Debt and scope assertions
$payload = Get-Content project/workflow-coverage-index.json -Raw | ConvertFrom-Json
$cells = $payload.cells.PSObject.Properties.Name
if (@($cells).Count -ne 1 -or $cells[0] -ne 'run|backdrop') {
  throw "Theme D expansion detected: workflow cells must remain exactly run|backdrop."
}
$cell = $payload.cells.'run|backdrop'
if ($cell.future_split_debt.id -ne 'DEBT-BACKDROP-ID-SPLIT-001') { throw "Unexpected debt id." }
if ($cell.future_split_debt.status -ne 'closed') { throw "Debt must be closed." }
if ($cell.future_split_debt.readiness_blocking -ne $true) { throw "readiness_blocking must remain true." }
if ($cell.future_split_debt.closure.type -ne 'parity_id_count_min') { throw "closure.type mismatch." }
if ($cell.future_split_debt.closure.cell -ne 'run|backdrop') { throw "closure.cell mismatch." }
if ([int]$cell.future_split_debt.closure.min_required -ne 2) { throw "closure.min_required must remain 2." }

$expectedParityIds = @('PIPE-BACKDROP-001', 'PIPE-BACKDROP-002')
$actualParityIds = @($cell.required_parity_ids) | Sort-Object
if (Compare-Object $expectedParityIds $actualParityIds) {
  throw "required_parity_ids must be exactly PIPE-BACKDROP-001 and PIPE-BACKDROP-002."
}

$expectedOwnerTests = @(
  'tests/characterization/safety_contract/test_safety_contract_pipeline.py::test_pipe_backdrop_001_characterization',
  'tests/characterization/safety_contract/test_safety_contract_pipeline_backdrop_split.py::test_pipe_backdrop_002_characterization'
) | Sort-Object
$actualOwnerTests = @($cell.required_owner_tests) | Sort-Object
if (Compare-Object $expectedOwnerTests $actualOwnerTests) {
  throw "required_owner_tests mismatch for closed backdrop debt contract."
}

# Confirm Theme C artifacts unchanged
git diff --name-only -- project/route-fence.md project/route-fence.json

# Aggregate governance gate
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

# Repo verification contract command set
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit
```

## 10) Rollback path
Post-commit rollback:
1. `git revert <slice-34-commit-sha>`
2. Re-run:
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity`
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization`
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness`
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture`
3. Confirm blocker baseline restored (`open debts: 1`, debt `status=open`).

Pre-commit rollback:
1. `git restore --source=HEAD -- project/workflow-coverage-index.json project/parity-matrix.md tests/characterization/baselines/safety_contract_baseline.json project/scripts/characterization_contract.py project/scripts/parity_contract.py tests/test_characterization_checks.py tests/_readiness_test_helpers.py tests/test_readiness_checks.py`
2. `git clean -f -- tests/characterization/safety_contract/test_safety_contract_pipeline_backdrop_split.py`
3. Re-run targeted readiness and governance checks above.

## 11) Exact next-slice expectation if successful
- Next slice: `Slice-35 (Theme C1) route-fence ownership accountability for run|backdrop`.
- Expected next-slice in-scope:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/v1-slices-reports/slice-35/*`
- Next-slice guardrails:
  - keep route `v0`,
  - no parity-status activation yet (`ready` remains Theme C2),
  - no Theme D multi-cell expansion.

## 12) Inherited unresolved remediation from previous audit
- None explicitly inherited from the immediately previous slice audit (`slice-33` compliant/closable with no open remediation list).

## 13) Explicit scope-tightening
Tempting excluded work:
- Adding non-backdrop parity IDs or closing additional debts.
- Canonical route-fence ownership/readiness/route-value edits.
- Any workflow index multi-cell broadening.
- Validator redesign or severity-ratchet changes.
- Runtime refactor/cleanup under `src/jfin/**`.

What would make the slice too large:
- Combining Theme B closure with any Theme C activation.
- Expanding beyond one-cell contract completion.
- Broad rewrite of test harness topology.

Decomposition triggers:
- If two-ID backdrop contract cannot be linked without runtime code changes.
- If canonical fixture updates require touching broad unrelated test suites.
- If registry updates cascade into governance-system redesign.

## 14) Concise slice-size sanity-check answers
- Single objective only? `Yes`.
- Title unchanged? `Yes`.
- Debt target unchanged (`DEBT-BACKDROP-ID-SPLIT-001` only)? `Yes`.
- Theme C activation performed? `No`.
- Theme D multi-cell work performed? `No`.
- Explicit criterion #3 claim-evaluability evidence required? `Yes`.
