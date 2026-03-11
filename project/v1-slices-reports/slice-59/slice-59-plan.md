# Slice 59 Plan v3 (Final) - Runtime-Gate Scope Decomposition for `config_init|n/a` Claim Eligibility

Date: 2026-03-11
Branch: feat/v1-overhaul
Local SHA: 0ffb028df2645282686376972853246c08235c0a

## Slice ID/title
- Slice 59
- Runtime-gate scope decomposition for `config_init|n/a` claim eligibility

## Goal/objective
- Add exactly one runtime-gate target required to make `config_init|n/a` claim-path eligibility complete.
- Target to add:
  - `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_generate_config_blocks_operational_flags`
- Keep this slice limited to runtime-gate target decomposition only.
- Preserve governance progression state: no route-fence mutation, no parity/workflow coverage mutation, and no readiness activation in this slice.

## Planning worker boundary (this turn)
- Planning worker writes only `project/v1-slices-reports/slice-59/slice-59-plan.md`.
- Planning worker does not edit `WORK_ITEMS.md`.

## Worker responsibility split (execution phase)
- Implementation worker:
  - may edit only runtime-gate contract/schema alignment surfaces:
    - `project/verification-contract.yml`
    - `project/scripts/governance_contract.py`
    - `tests/test_governance_checks.py`
  - may write only `project/v1-slices-reports/slice-59/slice-59-implementation.md` as execution evidence
- Audit worker:
  - may write only `project/v1-slices-reports/slice-59/slice-59-audit.md`
- Orchestration thread only:
  - may update `WORK_ITEMS.md` only after explicit audit PASS

## Baseline snapshot (planning time)
- Completed through Slice 58.
- Current runtime gate targets (3):
  1. `tests/characterization/safety_contract`
  2. `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_test_jf_blocks_operational_flags`
  3. `tests/characterization/config_contract/test_config_contract_characterization.py::test_config_requires_core_fields`
- Eligibility unblock target to add:
  - `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_generate_config_blocks_operational_flags`
- Expected counter movement for this slice:
  - runtime-gate targets configured/checked/passed: `3 -> 4`
  - runtime-gate targets failed: remains `0`
  - readiness claims: unchanged at `claimed_rows=3`, `validated_rows=3`

## In-scope files (Slice 59 execution)
- `project/verification-contract.yml`
- `project/scripts/governance_contract.py`
- `tests/test_governance_checks.py`
- `project/v1-slices-reports/slice-59/slice-59-plan.md`
- `project/v1-slices-reports/slice-59/slice-59-implementation.md`
- `project/v1-slices-reports/slice-59/slice-59-audit.md`

## Out-of-scope files/work
- `project/route-fence.md`
- `project/route-fence.json`
- `project/parity-matrix.md`
- `project/workflow-coverage-index.json`
- `project/verification-contract.yml` fields other than `characterization_runtime_gate_targets`
- `.github/workflows/ci.yml`
- any runtime code under `src/`
- any characterization test sources under `tests/characterization/`
- any route mutation (`v0 -> v1`), parity-status mutation (`pending -> ready`), or workflow-coverage cell mutation
- any `WORK_ITEMS.md` update before audit PASS

## Acceptance criteria
1. Runtime-gate targets list is exactly four entries in order:
   1. `tests/characterization/safety_contract`
   2. `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_test_jf_blocks_operational_flags`
   3. `tests/characterization/config_contract/test_config_contract_characterization.py::test_config_requires_core_fields`
   4. `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_generate_config_blocks_operational_flags`
2. Added target is synchronized across all required schema/default surfaces:
   - `project/verification-contract.yml` (`characterization_runtime_gate_targets`)
   - `project/scripts/governance_contract.py` (`EXPECTED_RUNTIME_GATE_TARGETS`)
   - `tests/test_governance_checks.py` (`_contract_text` default runtime targets)
3. `characterization_runtime_gate_budget_seconds` remains `180`.
4. No edits occur in route-fence, parity matrix, workflow coverage index, or characterization suites.
5. Governance checks pass with no regressions:
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization`
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity`
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness`
   - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`
6. Characterization runtime-gate report shows configured/checked/passed targets `4/4` and failed targets `0`.
7. Readiness counters remain unchanged at `claimed_rows=3`, `validated_rows=3`.
8. Slice 59 implementation and audit reports exist, and audit is explicitly PASS before any orchestration update to `WORK_ITEMS.md`.

## Binary Success Condition
Slice 59 is successful only if the sole governance mutation is adding `test_cli_generate_config_blocks_operational_flags` to the runtime-gate target list, that list is synchronized exactly across `project/verification-contract.yml`, `project/scripts/governance_contract.py`, and `tests/test_governance_checks.py`, governance checks pass (`characterization`, `parity`, `readiness`, `all`), readiness remains `3/3`, scope stays in-bounds, and audit is explicitly PASS before any `WORK_ITEMS.md` update.

## Fail-Close Criteria
- Any route mutation on any row (`v0 -> v1` or otherwise).
- Any parity-status mutation on any row (`pending -> ready` or otherwise).
- Any workflow coverage mutation (including `project/workflow-coverage-index.json`).
- Runtime-gate target list drift or unsynced ordering/content across the three required files:
  - `project/verification-contract.yml`
  - `project/scripts/governance_contract.py`
  - `tests/test_governance_checks.py`
- Any out-of-scope file edit.
- Missing Slice 59 audit report or audit not explicitly PASS.
- Any `WORK_ITEMS.md` edit before explicit audit PASS.

## Implementation steps (for Slice 59 execution worker)
1. Reconfirm current runtime-gate baseline targets (3) from contract and schema expectation module.
2. Add one target (`test_cli_generate_config_blocks_operational_flags`) to `characterization_runtime_gate_targets` in `project/verification-contract.yml`.
3. Mirror the same fourth target in `project/scripts/governance_contract.py` (`EXPECTED_RUNTIME_GATE_TARGETS`) and `tests/test_governance_checks.py` (`_contract_text` defaults).
4. Capture diff-scope proof showing only in-scope runtime-gate surfaces changed.
5. Run governance verification checks (`characterization`, `parity`, `readiness`, `all`) and record counters.
6. Write `slice-59-implementation.md` with before/after target list, command outputs, and unchanged readiness proof.
7. Hand off for independent audit (`slice-59-audit.md`).

## Minimum Evidence Commands (PowerShell)
```powershell
# Runtime target list proof (run before and after)
Select-String -Path project/verification-contract.yml -Pattern '^characterization_runtime_gate_targets:|^\s*-\s*tests/characterization/'
Select-String -Path project/verification-contract.yml -Pattern '^characterization_runtime_gate_budget_seconds:\s*180$'
Select-String -Path project/scripts/governance_contract.py -Pattern 'EXPECTED_RUNTIME_GATE_TARGETS|test_cli_test_jf_blocks_operational_flags|test_config_requires_core_fields|test_cli_generate_config_blocks_operational_flags' -Context 0,8
Select-String -Path tests/test_governance_checks.py -Pattern 'runtime_targets = runtime_gate_targets or \[|test_cli_test_jf_blocks_operational_flags|test_config_requires_core_fields|test_cli_generate_config_blocks_operational_flags' -Context 0,8

# Diff-scope constraints
git diff --name-only
git diff -- project/verification-contract.yml project/scripts/governance_contract.py tests/test_governance_checks.py
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json .github/workflows/ci.yml WORK_ITEMS.md

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

# Readiness unchanged proof (must remain 3/3)
$readiness = .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
$readiness
$readiness | Select-String 'Route readiness claims: 3'
$readiness | Select-String 'Route readiness claims validated: 3'
```

Expected proof points:
- Before: runtime-gate targets show exactly 3 entries in all three required files.
- After: runtime-gate targets show exactly 4 entries in all three required files, with the added fourth target:
  - `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_generate_config_blocks_operational_flags`
- Ordering/content is identical across all three files after mutation.
- Runtime-gate budget remains unchanged at `characterization_runtime_gate_budget_seconds: 180`.
- `git diff --name-only` remains within in-scope execution files only.
- Targeted out-of-scope diff check shows no edits in route-fence/parity/workflow/CI/`WORK_ITEMS.md`.
- Governance checks above all PASS.
- Readiness proof output includes:
  - `INFO: Route readiness claims: 3`
  - `INFO: Route readiness claims validated: 3`

## Risk/guardrails
- Risk: accidental governance drift outside runtime-gate decomposition.
  Guardrail: fail closed if diff touches route-fence, parity matrix, workflow coverage, CI workflow, runtime code, or characterization suites.
- Risk: schema mismatch from incomplete target synchronization.
  Guardrail: require exact target-list parity across contract, schema expectation constant, and governance test default helper.
- Risk: hidden ordering drift in runtime targets.
  Guardrail: enforce exact ordered list in acceptance criteria.
- Risk: premature readiness progression claim.
  Guardrail: this slice prohibits parity/readiness route progression and treats claim activation as next-slice work.

## Suggested next slice
- Slice 60: readiness-claim activation for `config_init|n/a` (`parity_status: pending -> ready`) while preserving `route=v0`, contingent on Slice 59 audit PASS.

## Explicit split rule if scope grows
- Stop and split immediately if any of the following becomes necessary:
  - edits to `project/route-fence.md` or `project/route-fence.json`
  - edits to `project/parity-matrix.md` or `project/workflow-coverage-index.json`
  - edits to characterization test sources (`tests/characterization/**`)
  - runtime-gate budget changes, CI workflow changes, or docs/workflow broad sync
- Keep Slice 59 limited to one objective: add one runtime-gate target for `config_init|n/a` eligibility with required schema/default synchronization and slice report artifacts.
