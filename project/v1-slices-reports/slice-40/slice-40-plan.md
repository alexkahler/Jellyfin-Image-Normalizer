# Slice 40 Plan v3 - Workflow Coverage Expansion for `test_connection|n/a`

Date: 2026-03-09
Branch: feat/v1-overhaul
HEAD at planning start: 99f1a394f37643e4de315e5a15aa2e4c5212c5d6
Starting worktree state: intentionally unclean (`project/v1-slices-reports/slice-40/` scaffold files plus this plan file)

## 1. Baseline State (Recomputed)

Artifacts reviewed:
- WORK_ITEMS.md
- project/v1-slices-reports/audits/post-theme-d-planning-baseline-audit-2026-03-09.md
- project/v1-slices-reports/audits/post_theme_d_next_slice_roadmap.md
- project/v1-slices-reports/slice-38/slice-38-audit.md
- project/v1-slices-reports/slice-39/slice-39-audit.md
- project/workflow-coverage-index.json
- project/route-fence.md
- project/route-fence.json
- project/parity-matrix.md
- project/architecture-baseline.json

Current governance evidence (2026-03-09, current HEAD):
- readiness: PASS (`claimed_rows=1`, `validated_rows=1`)
- parity: PASS
- characterization: PASS (`configured_cells=2`, `validated_cells=2`, `open_debts=0`, runtime-gate targets checked `1/1`)
- architecture: PASS (`0` warnings)

Current metrics:
- route-fence rows total: 8
- route state: `v0=8`, `v1=0`
- ready rows: 1 (`run|backdrop`)
- pending rows: 7
- owner placeholders: 6
- non-placeholder owners: 2 (`Slice-35`, `Slice-39`)
- workflow coverage cells: 2
- validated readiness claim paths: 1

## 2. Exact Blocker Targeted

- Post-Theme-D progression gate condition 5 is still open because workflow readiness evidence has not expanded beyond the 2-cell baseline.

## 3. Slice Objective (Single Sentence)

Add exactly one governed workflow coverage cell for `test_connection|n/a` using existing parity and characterization ownership evidence, while preserving `route=v0` and leaving readiness claims unchanged.

## 4. In-Scope Files

- project/workflow-coverage-index.json
- project/v1-slices-reports/slice-40/slice-40-plan.md
- project/v1-slices-reports/slice-40/slice-40-implementation.md
- project/v1-slices-reports/slice-40/slice-40-audit.md
- WORK_ITEMS.md

## 5. Out-of-Scope Files and Work

- project/route-fence.md
- project/route-fence.json
- project/parity-matrix.md
- project/verification-contract.yml
- project/architecture-baseline.json
- Any `route=v0` to `route=v1` change
- Any parity-status change (`pending` to `ready`)
- Any readiness-claim activation (`claimed_rows` or `validated_rows` increase)
- Any runtime-gate target/budget policy change
- Any same-SHA CI closure-discipline change
- Any runtime source code or non-governance tests

## 6. Why This Slice Is Small Enough

- One blocker, one governance artifact change (`workflow-coverage-index.json`).
- Reuses existing parity row and owner test (`CLI-TESTJF-001` + existing characterization test), avoiding parity-matrix/baseline churn.
- Binary success statement: "Configured/validated coverage cells increase `2 -> 3` with open debts still `0`, all routes still `v0`, and readiness claims still `1/1`."

## 7. Why This Does Not Overreach

- No route-fence ownership/route/status mutations.
- No claim-path activation in readiness semantics.
- No runtime-gate scope decision changes.
- No CI-evidence discipline changes.

## 8. Behavior-Preservation Obligations

- Preserve runtime behavior and safety invariants (governance metadata only).
- Preserve all route-fence route values at `v0`.
- Preserve route-fence parity statuses (`test_connection` remains `pending`).
- Preserve readiness claim counters at `claimed_rows=1`, `validated_rows=1`.
- Preserve workflow open debt at `0`.

## 9. Honest Remediation Path

1. Add `test_connection|n/a` cell to `project/workflow-coverage-index.json`.
2. Bind the cell to existing evidence:
   - required parity id: `CLI-TESTJF-001`
   - required owner test: `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_test_jf_blocks_operational_flags`
3. Set evidence and ordering requirements to match baseline case payload for `CLI-TESTJF-001` (avoid vacuous sequence checks).
4. Set explicit `future_split_debt` contract fields with bounded semantics.
5. Run governance checks and targeted test evidence; confirm no unintended readiness or route movement.
6. Record implementation/audit evidence and update `WORK_ITEMS.md`.

## 10. Expected Blocker Contraction

Expected cleared blocker:
- Progression gate condition 5 (workflow breadth beyond minimal 2-cell baseline).

Progression-gate condition impact:
- Condition 5: expected unmet -> met.
- Condition 7: remains met (all routes still `v0`).
- Conditions 6, 8, 9: intentionally remain open.

## 11. Exact Verification Commands for Audit

- git status --short
- git diff --name-only
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

Targeted regression/validator command:
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_test_jf_blocks_operational_flags

## 12. Rollback Path

If scope drifts or checks regress:
1. Revert workflow-coverage index change for `test_connection|n/a`.
2. Keep slice-40 reports with blocked/fail-close narrative and evidence.
3. Do not commit partial mixed-scope closure.

## 13. Exact Next-Slice Expectation if Successful

- Slice 41: activate a second readiness claim path for the already-owned `test_connection|n/a` route while keeping `route=v0`.

## 14. Inherited Unresolved Audit Remediation

- Expand readiness claim paths from `1` to `>=2` validated.
- Make runtime-gate scope decision explicit (retain as-is with rationale, or widen with proof).
- Codify same-SHA CI evidence expectations in closure discipline artifacts.
- Reduce test LOC maintainability debt in dedicated slice.

## 15. Scope-Tightening Controls

Excluded adjacent work:
- route ownership completion for any row
- route/status flips in route-fence
- readiness claim activation
- runtime-gate policy changes
- CI evidence policy changes

Too-large signals:
- needing edits to route-fence/parity-matrix/verification-contract to make this cell validate
- adding more than one new workflow cell in this slice
- adding new parity rows or baseline cases

Decomposition signals:
- `CLI-TESTJF-001` proves semantically unsuitable for `test_connection|n/a` mapping
- baseline payload shape cannot satisfy non-vacuous evidence requirements without extra parity/baseline work
- characterization validation requires touching additional governance surfaces beyond declared scope

## 16. Fail-Close Criteria

- Any route value changes away from `v0`.
- Any route-fence parity status changes (`pending` -> `ready`) in this slice.
- Any increase in readiness claim counters in this slice.
- Any governance check failure/regression.
- Any unplanned governance-surface expansion beyond declared in-scope files.
