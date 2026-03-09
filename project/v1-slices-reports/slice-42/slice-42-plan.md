# Slice 42 Plan v3 (Implementation-Ready) - Second Readiness Claim Activation for `test_connection|n/a`

Date: 2026-03-09
Branch: feat/v1-overhaul
HEAD at planning start: 811d1b6
Starting worktree state: intentionally unclean (`project/v1-slices-reports/slice-42/` scaffold files only)

## 1. Baseline State (Recomputed)

Artifacts reviewed:
- WORK_ITEMS.md
- project/v1-slices-reports/audits/post-theme-d-planning-baseline-audit-2026-03-09.md
- project/v1-slices-reports/audits/post_theme_d_next_slice_roadmap.md
- project/v1-slices-reports/slice-40/slice-40-audit.md
- project/v1-slices-reports/slice-41/slice-41-audit.md
- project/route-fence.md
- project/route-fence.json
- project/workflow-coverage-index.json
- project/verification-contract.yml

Current verified state:
- route posture: `v0=8`, `v1=0`
- non-placeholder owners: `2` (`Slice-35`, `Slice-39`)
- workflow coverage: `configured_cells=3`, `validated_cells=3`, `open_debts=0`
- readiness claims: `claimed_rows=1`, `validated_rows=1`
- `test_connection|n/a` row: owner `Slice-39`, route `v0`, parity `pending`
- runtime-gate targets include selected claim owner-test nodeid and pass within budget.

## 2. Exact Blocker Targeted

- Post-Theme-D progression condition 6: expand readiness claims from `1` to at least `2` validated claim paths.

## 3. In-Scope / Out-of-Scope Files

In-scope:
- project/route-fence.md
- project/route-fence.json
- project/v1-slices-reports/slice-42/slice-42-plan.md
- project/v1-slices-reports/slice-42/slice-42-implementation.md
- project/v1-slices-reports/slice-42/slice-42-audit.md
- WORK_ITEMS.md

Out-of-scope:
- project/workflow-coverage-index.json
- project/verification-contract.yml
- project/scripts/governance_contract.py
- project/parity-matrix.md
- project/architecture-baseline.json
- any runtime code/tests
- any route `v0 -> v1` change
- any owner metadata rewrites
- same-SHA CI closure-discipline changes

## 4. Why This Slice Is Small Enough

- Single-row readiness activation in route-fence artifacts only.
- Runtime-gate and workflow evidence prerequisites already exist from slices 39-41.
- Binary success sentence: "`test_connection|n/a` parity status changes `pending -> ready` with route still `v0`, and readiness counters move `1/1 -> 2/2`."

## 5. Behavior-Preservation Obligations

- Preserve all route values at `v0`.
- Preserve owners and commands/modes for every row.
- Preserve runtime behavior and safety invariants.
- Preserve workflow coverage metrics (`3/3`, open debts `0`).

## 6. Honest Remediation Path

1. Update `test_connection|n/a` parity status from `pending` to `ready` in route-fence markdown.
2. Apply matching parity-status change in route-fence JSON.
3. Keep row route as `v0`.
4. Run readiness/parity/characterization/architecture and `--check all`.
5. Run targeted supporting test for `CLI-TESTJF-001` owner test.
6. Confirm readiness counters now report `claimed_rows=2`, `validated_rows=2`.

## 7. Expected Blocker Contraction

Expected cleared blocker:
- condition 6 moves unmet -> met.

Expected remaining blocker after successful Slice 42:
- condition 9 remains open (same-SHA CI evidence expectations not yet codified).

## 8. Exact Verification Commands for Audit

- git status --short
- git diff --name-only
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_test_jf_blocks_operational_flags

## 9. Rollback Path

If scope drifts or checks regress:
1. Revert route-fence parity-status updates for `test_connection|n/a`.
2. Keep slice-42 reports with blocked/fail-close evidence.
3. Do not commit partial mixed-scope changes.

## 10. Exact Next-Slice Expectation

- Next slice: condition 9 closure-discipline codification (same-SHA CI evidence expectation explicit).

## 11. Inherited Unresolved Audit Remediation

- Codify same-SHA CI evidence handling in closure artifacts.
- Carry forward pre-existing test LOC warning debt to maintainability slice.

## 12. Scope-Tightening Controls

Excluded adjacent work:
- runtime-gate policy changes
- workflow coverage changes
- ownership expansion
- route flips
- CI checklist policy updates

Too-large signals:
- touching verification contract/runtime-gate artifacts
- touching parity matrix/workflow coverage artifacts
- adding another route-fence row status change

Decomposition signals:
- readiness validation fails for `test_connection` despite prerequisites
- route-fence sync/parity validator requires broader schema edits

## 13. Fail-Close Criteria

- Any route changes away from `v0`.
- Any owner field changes.
- Any additional row status change beyond `test_connection|n/a`.
- Any governance check failure/regression.
