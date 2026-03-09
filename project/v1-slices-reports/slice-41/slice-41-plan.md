# Slice 41 Plan v3 (Implementation-Ready) - Runtime-Gate Decomposition for `test_connection|n/a` Claim Eligibility

Date: 2026-03-09
Branch: feat/v1-overhaul
HEAD at planning start: e3a7f46
Starting worktree state: intentionally unclean (`project/v1-slices-reports/slice-41/` scaffold files only)

## 1. Baseline State (Recomputed)

Artifacts reviewed:
- WORK_ITEMS.md
- project/v1-slices-reports/audits/post-theme-d-planning-baseline-audit-2026-03-09.md
- project/v1-slices-reports/audits/post_theme_d_next_slice_roadmap.md
- project/v1-slices-reports/slice-39/slice-39-audit.md
- project/v1-slices-reports/slice-40/slice-40-audit.md
- project/route-fence.md
- project/route-fence.json
- project/workflow-coverage-index.json
- project/parity-matrix.md
- project/verification-contract.yml

Current verified state (2026-03-09, current HEAD):
- route posture: `v0=8`, `v1=0`
- non-placeholder owners: `2` (`Slice-35`, `Slice-39`)
- workflow coverage: `configured_cells=3`, `validated_cells=3`, `open_debts=0`
- readiness claims: `claimed_rows=1`, `validated_rows=1`
- `test_connection|n/a` row: owner `Slice-39`, route `v0`, parity `pending`

Blocking evidence requiring decomposition:
- runtime-gate targets currently: `tests/characterization/safety_contract` only.
- `test_connection` owner test is in `tests/characterization/cli_contract/...::test_cli_test_jf_blocks_operational_flags`.
- current runtime mapped parity IDs do not include `CLI-TESTJF-001`.
- therefore direct claim activation for `test_connection|n/a` would fail readiness (`runtime_not_green` / `runtime_unmapped_parity`).
- Roadmap-order deviation note: this Slice 41 decomposition is evidence-forced by runtime target mismatch, not scope creep.

## 2. Exact Blocker Targeted

- Post-Theme-D progression condition 8: runtime-gate scope must be explicit and intentional.

This slice is a mandatory decomposition/unblock slice for later condition 6 work; it does **not** activate a second claim.

## 3. Exact In-Scope / Out-of-Scope Files

In-scope files for Slice 41 implementation:
- project/verification-contract.yml
- project/scripts/governance_contract.py
- tests/test_governance_checks.py
- project/v1-slices-reports/slice-41/slice-41-plan.md
- project/v1-slices-reports/slice-41/slice-41-implementation.md
- project/v1-slices-reports/slice-41/slice-41-audit.md
- WORK_ITEMS.md

Out-of-scope files and work:
- project/route-fence.md
- project/route-fence.json
- project/workflow-coverage-index.json
- project/parity-matrix.md
- project/architecture-baseline.json
- any runtime code under `src/`
- any baseline file edits
- any test edits outside `tests/test_governance_checks.py` fixture-default alignment for runtime-gate schema coupling
- readiness claim count changes (`1/1` must remain unchanged)
- any route-fence parity/status changes (`test_connection` remains `pending`)
- any `route=v0 -> v1` flip
- same-SHA CI closure-discipline changes

## 4. Why This Slice Is Small Enough

- Single governance surface change: runtime-gate target set in verification contract.
- Minimal widening only for one claim path dependency, no broad umbrella expansion.
- Binary success statement: "Runtime-gate policy explicitly includes the selected `test_connection` owner-test target and governance checks remain green, while readiness counters stay `1/1`."

## 5. Behavior-Preservation Obligations

- Preserve runtime behavior and safety invariants (governance-only slice).
- Preserve all routes at `v0` and all route-fence parity statuses unchanged.
- Preserve readiness claim counters (`claimed_rows=1`, `validated_rows=1`).
- Preserve workflow coverage metrics (`configured=3`, `validated=3`, `open_debts=0`).
- Do not weaken readiness semantics or runtime enforcement.

## 6. Honest Remediation Path (Runtime-Gate Scope Decision)

1. Record decomposition rationale from current evidence (no target intersection, unmapped `CLI-TESTJF-001`).
2. Apply minimal target widening in `project/verification-contract.yml`:
   - keep existing `tests/characterization/safety_contract` target,
   - add only `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_test_jf_blocks_operational_flags`.
3. If `--check all` fails due runtime-target schema fence coupling, update:
   - `project/scripts/governance_contract.py` expected runtime target set, and
   - `tests/test_governance_checks.py` `_contract_text` default runtime targets,
   so governance schema defaults remain synchronized with the intentional runtime-gate policy.
4. Keep runtime budget unchanged at `180` seconds unless proof shows budget risk.
5. Verify characterization runtime gate proves both targets execute within budget.
6. Verify readiness counters remain unchanged (`1/1`) and route artifacts remain untouched.
7. Record explicit unblock signal for next slice: runtime mapping now exists for `CLI-TESTJF-001` claim path.

## 7. Expected Blocker Contraction

Expected cleared blocker:
- condition 8 moves unmet -> met (runtime-gate scope becomes explicit and intentional for the selected next claim path).

Expected unblock signal for condition 6:
- runtime target intersection exists for `test_connection` owner test,
- `CLI-TESTJF-001` becomes runtime-mapped,
- claim activation can be attempted in next slice without policy edits.

Expected remaining blockers after successful Slice 41:
- condition 6 (second validated claim activation) still open by design,
- condition 9 (same-SHA CI closure discipline) still open.

## 8. Exact Verification Commands for Audit

- git status --short
- git diff --name-only
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_test_jf_blocks_operational_flags

Runtime budget proof expectations for audit record:
- characterization output must report runtime gate target count increased as expected,
- runtime gate `failed=0`,
- runtime gate elapsed time <= configured budget (`180s`).

## 9. Rollback Path

If scope drifts or checks regress:
1. Revert only runtime-gate target edits in `project/verification-contract.yml`.
2. Keep slice-41 reports with blocked/fail-close evidence.
3. Do not commit partial mixed-scope work.

## 10. Exact Next-Slice Expectation

- Next slice is claim activation for `test_connection|n/a` (condition 6): update route-fence parity status `pending -> ready` while keeping `route=v0`, targeting readiness counters `1/1 -> 2/2`.

## 11. Inherited Unresolved Audit Remediation

- Activate second validated claim path after runtime mapping is in place.
- Codify same-SHA CI evidence handling in closure discipline.
- Carry forward pre-existing test LOC warning debt to maintainability slice.

## 12. Scope-Tightening Controls

Excluded adjacent work:
- route-fence row edits of any kind
- readiness claim activation
- workflow coverage expansion
- ownership changes
- same-SHA CI policy changes

Too-large signals:
- adding broad directory targets beyond the one required CLI nodeid
- changing runtime budget and target set in same slice without explicit budget necessity
- touching additional governance artifacts outside declared scope

Decomposition signals:
- added CLI nodeid target causes runtime failures or budget overrun
- readiness still reports claim-path runtime mismatch after minimal widening
- fixing failures would require broader target expansion not justified by selected route

## 13. Fail-Close Criteria

- Any route-fence status/route/owner changes occur.
- Readiness claim counters change from `1/1` in this slice.
- Runtime-gate policy is widened beyond minimal required target without explicit justification.
- Governance checks regress/fail.
- Runtime budget proof cannot be met and no honest bounded adjustment is possible.
