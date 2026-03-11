# Slice 51 Plan - Runtime-Gate Scope Decomposition for `config_validate|n/a` Claim Eligibility

Date: 2026-03-11
Branch: feat/v1-overhaul
Local SHA: 8b2d3ad39abb525d2aee011a6b79372ccac7b8e8

## Slice Type
- runtime-gate scope decomposition
- governance-contract alignment

## Objective
- Add the minimum runtime-gate target needed for `config_validate|n/a` claim-path eligibility.
- Keep this as a policy/evidence slice only: no route-fence or readiness-claim activation changes.

## Decomposition Precheck
blocking_mismatch: `config_validate|n/a` workflow owner test is not covered by current runtime-gate targets.
target_to_add: `tests/characterization/config_contract/test_config_contract_characterization.py::test_config_requires_core_fields`
current_runtime_targets: safety contract directory + CLI `test_cli_test_jf_blocks_operational_flags` nodeid.
expected_unblock_signal: runtime gate target count increases from `2` to `3` and mapped parity IDs include `CFG-CORE-001`.
readiness_expectation: remains `claimed_rows=2`, `validated_rows=2`.
same_sha_status: unavailable
workflow_identity: GitHub Actions `ci.yml`
same_sha_unavailable_reason: GitHub Actions API query for local SHA `8b2d3ad39abb525d2aee011a6b79372ccac7b8e8` returned `total_count=0`.
residual_risk: required-job status summary (`test/security/quality/governance`) is unavailable for this exact SHA.
rollback_path: remove the added config nodeid target from runtime-gate defaults in all touched governance artifacts.

## In Scope
- `project/verification-contract.yml`
- `project/scripts/governance_contract.py`
- `tests/test_governance_checks.py`
- `WORK_ITEMS.md`
- `project/v1-slices-reports/slice-51/slice-51-plan.md`
- `project/v1-slices-reports/slice-51/slice-51-implementation.md`
- `project/v1-slices-reports/slice-51/slice-51-audit.md`

## Out of Scope
- `project/route-fence.md`
- `project/route-fence.json`
- `project/workflow-coverage-index.json`
- `project/parity-matrix.md`
- any route/value/status/owner mutation in route-fence
- runtime source code under `src/`

## Binary Success Condition
- Success only if runtime-gate target defaults are synchronized across contract/schema-test surfaces with one added config nodeid, governance checks pass, readiness counters remain unchanged, and same-SHA unavailability is explicitly documented.

## Expected Next Slice If Successful
- readiness-claim activation for `config_validate|n/a` (`pending -> ready`) while preserving `route=v0`.

## Expected Next Slice If Unsuccessful
- bounded remediation for runtime-gate target/schema drift or runtime-budget regression.
