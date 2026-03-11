# Slice 50 Plan - Workflow Coverage Expansion for `config_validate|n/a`

Date: 2026-03-11
Branch: feat/v1-overhaul
Local SHA: 890268bfe35f8bb6792518683714dfcebd998dc2

## Slice Type
- workflow coverage expansion
- single-cell governance mutation

## Objective
- Add exactly one governed workflow-coverage cell for `config_validate|n/a` using existing parity and characterization evidence.
- Preserve route-fence state (`route=v0`, `parity_status=pending`) and readiness claim counters.

## Coverage-Expansion Precheck
target_cell: `config_validate|n/a` is owner-complete (`Slice-49`) and currently absent from workflow coverage.
parity_anchor: `CFG-CORE-001`.
owner_test_anchor: `tests/characterization/config_contract/test_config_contract_characterization.py::test_config_requires_core_fields`.
expected_counter_change: workflow coverage `configured/validated` should advance `3/3 -> 4/4` with open debts still `0`.
readiness_expectation: remains `claimed_rows=2`, `validated_rows=2` (no status/route mutation in this slice).
same_sha_status: unavailable
workflow_identity: GitHub Actions `ci.yml`
same_sha_unavailable_reason: GitHub Actions API query for local SHA `890268bfe35f8bb6792518683714dfcebd998dc2` returned `total_count=0`.
residual_risk: required-job summary (`test/security/quality/governance`) cannot be attached for this exact SHA.
rollback_path: remove `config_validate|n/a` cell from `project/workflow-coverage-index.json`.

## In Scope
- `project/workflow-coverage-index.json`
- `WORK_ITEMS.md`
- `project/v1-slices-reports/slice-50/slice-50-plan.md`
- `project/v1-slices-reports/slice-50/slice-50-implementation.md`
- `project/v1-slices-reports/slice-50/slice-50-audit.md`

## Out of Scope
- `project/route-fence.md`
- `project/route-fence.json`
- `project/parity-matrix.md`
- `project/verification-contract.yml`
- any `route=v0` to `route=v1` changes
- any parity-status transitions (`pending -> ready`)
- runtime code/tests outside targeted verification commands

## Binary Success Condition
- Success only if `config_validate|n/a` is added as one valid workflow-coverage cell, governance checks pass, route-fence remains unchanged, readiness counters remain unchanged, and same-SHA unavailability is explicitly documented.

## Expected Next Slice If Successful
- readiness-claim activation candidate planning for one pending owned row, most likely `config_validate|n/a` (`pending -> ready`, route still `v0`), only after runtime-gate coverage implications are explicitly validated.

## Expected Next Slice If Unsuccessful
- single-cell remediation for workflow-coverage contract/schema/evidence mismatch.
