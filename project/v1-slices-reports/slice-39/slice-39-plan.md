# Slice 39 Plan v3 - Ownership Completion for Next Candidate Route

Date: 2026-03-09
Branch: feat/v1-overhaul
HEAD at planning start: 22527bcaa2f412a197e3a11bddf3732a0a0118cf
Starting worktree state: intentionally unclean (`project/v1-slices-reports/slice-39/` scaffold files only)

## 1. Baseline State (Recomputed)

Artifacts reviewed:
- WORK_ITEMS.md
- project/v1-slices-reports/audits/post-theme-d-planning-baseline-audit-2026-03-09.md
- project/v1-slices-reports/audits/post_theme_d_next_slice_roadmap.md
- project/v1-slices-reports/audits/track-1-iteration-roadmap.md
- project/route-fence.md
- project/route-fence.json
- project/workflow-coverage-index.json

Governance evidence snapshot (2026-03-09 after Slice 38):
- readiness: PASS (`claimed=1`, `validated=1`)
- parity: PASS
- characterization: PASS (`cells=2`, `validated=2`)
- architecture: PASS (`0` warnings)

Current metrics:
- route-fence total rows: 8
- ready rows: 1
- pending rows: 7
- owner placeholders: 7
- non-placeholder owners: 1
- all rows remain `v0`
- workflow coverage cells: 2
- validated readiness claim paths: 1

## 2. Exact Blocker Targeted

- Post-Theme-D progression gate condition 4 is open because there is not yet an additional non-placeholder owned route beyond `run|backdrop`.

## 3. Slice Objective (Single Sentence)

Replace exactly one non-backdrop placeholder owner row with concrete ownership metadata while preserving `route=v0` and `parity status=pending`.

## 4. Route Candidate Selection

Selected candidate: `test_connection | n/a`

Selection rationale:
- Lowest blast radius among non-backdrop candidates.
- Ownership-only update can be audited without coupling to coverage/claim activation in the same slice.

## 5. In-Scope Files

- project/route-fence.md
- project/route-fence.json
- project/v1-slices-reports/slice-39/slice-39-plan.md
- project/v1-slices-reports/slice-39/slice-39-implementation.md
- project/v1-slices-reports/slice-39/slice-39-audit.md
- WORK_ITEMS.md

## 6. Out-of-Scope Files and Work

- project/workflow-coverage-index.json
- project/parity-matrix.md
- project/architecture-baseline.json
- Any route `v0` -> `v1` flip
- Any parity status `pending` -> `ready` transition for `test_connection`
- Any new readiness claim activation
- Runtime-gate policy edits
- Source/runtime code changes

## 7. Why This Slice Is Small Enough

- Single-row metadata change in one governance table + synced JSON mirror.
- No behavior/runtime changes.
- Pass/fail sentence is binary: "`test_connection` owner is no longer `WI-00X` and all rows stay `v0`."

## 8. Behavior-Preservation Obligations

- Preserve all route values at `v0`.
- Preserve existing ready claim path count (`1`) and validated claim count (`1`).
- Preserve parity statuses except owner metadata for the selected row.
- No route-fence schema changes.

## 9. Honest Remediation Path

1. Update `test_connection` owner slice from `WI-00X` to `Slice-39` in route-fence markdown table.
2. Apply the same owner update in route-fence JSON.
3. Run governance checks to confirm schema and readiness contracts remain valid.
4. Record implementation and audit evidence.
5. Confirm exactly one route-fence row changed (`test_connection`) and no other row drift occurred.

## 10. Why This Does Not Overreach

- Does not claim route readiness.
- Does not add workflow evidence cells.
- Does not alter parity matrix.
- Does not change runtime gate scope or CI policy.

## 11. Expected Blocker Contraction

Expected cleared blocker:
- Progression gate condition 4 (at least one additional non-placeholder route owner).

Progression-gate impact:
- Condition 4: expected to move from unmet -> met.
- Condition 7: remains met (all rows stay `v0`).
- Conditions 5, 6, 8, 9, and 10 remain open by design.

Expected remaining blockers:
- Workflow breadth still minimal (2 cells).
- Claim breadth still minimal (1 validated claim path).
- Runtime-gate scope decision still open.
- Same-SHA CI closure discipline still open.

## 12. Exact Verification Commands for Audit

- git status --short
- git diff --name-only
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture

Targeted validators:
- None beyond governance checks (route-fence schema/consistency covered by readiness/parity checks).

## 13. Rollback Path

If scope drifts or checks regress:
1. Revert route-fence owner row changes.
2. Keep slice-39 reports with blocked/fail-close explanation.
3. Do not commit partial mixed-scope changes.

## 14. Exact Next-Slice Expectation if Successful

- Next slice: Slice 40 workflow coverage expansion for `test_connection` readiness path inputs.

## 15. Inherited Unresolved Audit Remediation

- Expand workflow readiness evidence beyond 2-cell baseline.
- Activate second validated claim path.
- Decide runtime-gate scope explicitly.
- Codify same-SHA CI closure discipline.
- Address test LOC maintainability debt in dedicated slice.

## 16. Scope-Tightening Controls

Excluded adjacent work:
- Claim activation
- Coverage expansion
- Runtime gate policy
- CI evidence policy

Too-large signals:
- More than one route-fence row owner changed.
- Any parity-status transition to `ready` introduced.
- Any artifact outside route-fence/WORK_ITEMS/slice reports altered.

Decomposition signals:
- Need to alter workflow coverage index to validate ownership change.
- Need to change governance script behavior for row ownership format.

## 17. Fail-Close Criteria

- Any row changes route value away from `v0`.
- Any governance check fails/regresses.
- Any accidental readiness claim activation occurs.
