# Slice 38 Plan v3 - Governance Hygiene and Roadmap Refresh

Date: 2026-03-09
Branch: feat/v1-overhaul
HEAD at planning start: 18c9172d448c370737ac557590267d8bf3279c7f
Starting worktree state: intentionally unclean (`project/v1-slices-reports/slice-38/` scaffold files only)

## 1. Baseline State (Recomputed)

Artifacts reviewed:
- AGENTS.md
- WORK_ITEMS.md
- project/v1-plan.md
- project/v1-slices-reports/audits/post-theme-d-planning-baseline-audit-2026-03-09.md
- project/v1-slices-reports/audits/post_theme_d_next_slice_roadmap.md
- project/v1-slices-reports/audits/track-1-iteration-roadmap.md
- project/workflow-coverage-index.json
- project/route-fence.md
- project/route-fence.json
- project/parity-matrix.md
- project/architecture-baseline.json

Governance command evidence (2026-03-09):
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness -> PASS (`claimed=1`, `validated=1`)
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity -> PASS
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization -> PASS (`cells configured=2`, `cells validated=2`, `runtime gate targets=1`)
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture -> PASS with 1 warning (`src/jfin/pipeline.py.system_exit_raises observed=2`, baseline=5)

Current metrics:
- Route-fence rows total: 8
- Route-fence ready rows: 1
- Route-fence pending rows: 7
- Route-fence rows at v0: 8
- Route-fence rows at v1: 0
- Placeholder owners (`WI-00X`): 7
- Non-placeholder owners: 1
- Workflow coverage cells: 2
- Validated readiness claim paths: 1

## 2. Exact Blocker Targeted

Single blocker family targeted in this slice:
- Post-Theme-D governance hygiene drift (planning narrative + architecture ratchet signal) that keeps progression-gate conditions 2 and 3 open.

Concrete manifestations:
- `project/v1-slices-reports/audits/track-1-iteration-roadmap.md` still frames Themes A-D as upcoming.
- `project/architecture-baseline.json` is stale for `src/jfin/pipeline.py.system_exit_raises` (baseline 5 vs observed 2).

## 3. Slice Objective (Single Sentence)

Align governance and planning artifacts with the post-Theme-D baseline so architecture warning drift is resolved and roadmap narrative no longer misstates closed themes.

## 4. In-Scope Files

- project/architecture-baseline.json
- project/v1-slices-reports/audits/track-1-iteration-roadmap.md
- project/v1-slices-reports/slice-38/slice-38-plan.md
- project/v1-slices-reports/slice-38/slice-38-implementation.md
- project/v1-slices-reports/slice-38/slice-38-audit.md
- WORK_ITEMS.md

## 5. Out-of-Scope Files and Work

- project/route-fence.md and project/route-fence.json ownership edits
- project/workflow-coverage-index.json coverage expansion
- project/parity-matrix.md behavior inventory changes
- Any route `v0` -> `v1` flip
- Runtime-gate scope widening
- Test maintainability refactors
- CI workflow redesign
- Source runtime behavior changes under `src/jfin/`

## 6. Why This Slice Is Small Enough

- Touches only governance/planning artifacts, no runtime code.
- Two direct drifts from the post-Theme-D baseline are targeted in one coherent hygiene objective.
- Success/failure statement is one sentence: "roadmap reflects post-Theme-D closure and architecture warning drift is cleared."
- Audit proof is machine-checkable via architecture/governance checks and artifact diff.

## 7. Behavior-Preservation Obligations

- No change to runtime behavior, CLI behavior, safety invariants, or route dispatch behavior.
- Preserve all route-fence rows as `v0`.
- Preserve current readiness claims (`claimed=1`, `validated=1`) and avoid overclaiming new readiness.
- Preserve Themes A-D as closed in planning posture.

## 8. Honest Remediation Path

1. Update roadmap narrative to explicitly state Themes A-D are closed and reframe next phase as controlled route-by-route readiness scaling.
2. Ratchet `project/architecture-baseline.json` downward to observed counter (`src/jfin/pipeline.py.system_exit_raises: 2`) with no other counter expansion.
3. Record implementation notes with exact changed files and rationale.
4. Run required governance checks to verify warning removal and no regressions.
5. Record audit outcome including deferred blockers.

## 9. Why This Does Not Overreach

- It does not claim any new route ownership, coverage breadth, or readiness path activation.
- It does not alter route fence rows, parity statuses, or readiness claims.
- It does not modify governance validators or weaken checks.
- It does not include route progression decisions.

## 10. Expected Blocker Contraction

Expected cleared blockers:
- Architecture ratchet warning drift removed or explicitly justified via baseline sync.
- Stale roadmap framing (Themes A-D as upcoming) removed.

Progression-gate impact:
- Condition 2: expected to move from unmet -> met.
- Condition 3: expected to move from unmet -> met.
- Condition 7 remains met (all routes stay `v0`).
- Conditions 4, 5, 6, 8, 9, and 10 remain open after this slice.

Expected remaining blockers after this slice:
- 7 placeholder route-fence owners remain.
- Only 2 workflow coverage cells remain.
- Only 1 validated readiness claim path remains.
- Runtime-gate scope policy still pending explicit decision.
- Same-SHA CI closure discipline artifacts still pending explicit codification.

## 11. Exact Verification Commands for Audit

Required:
- git status --short
- git diff --name-only
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
- .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture

Targeted validators:
- None additional expected beyond governance checks, because only planning/governance artifact text and architecture baseline values are touched.

## 12. Rollback Path

If audit fails or scope drifts:
1. Revert only slice-38 touched files in working tree.
2. Keep slice-38 report files with explicit blocked/fail-close record.
3. Do not commit partial closure.
4. Re-slice into narrower remediation if the combined hygiene objective proves too broad.

## 13. Exact Next-Slice Expectation if Successful

- Next slice: Slice 39 (ownership completion for one non-backdrop candidate row, preference `test_connection` or `config_validate`).
- Slice 39 must keep all rows at `v0` and only replace one placeholder owner with concrete ownership.

## 14. Inherited Unresolved Audit Remediation

Inherited from post-Theme-D baseline audit and roadmap:
- Replace placeholder ownership on additional route-fence row(s).
- Expand workflow readiness evidence beyond current minimal baseline.
- Activate second validated readiness claim path.
- Make runtime-gate scope decision explicit (widen with proof or retain with rationale).
- Codify same-SHA CI evidence expectations for closure discipline.
- Address test LOC warning debt in dedicated maintainability slices.

## 15. Scope-Tightening Controls

Excluded adjacent work in this slice:
- Route-fence ownership completion
- Workflow coverage cell additions
- Readiness claim activation
- Runtime-gate policy expansion
- Test file decomposition

This slice becomes too large if:
- Any route-fence row content changes beyond preserving `v0` posture.
- Any workflow coverage or parity matrix row is added/rewritten.
- Governance script behavior is modified rather than artifacts synchronized.

Decomposition signals (must stop and split):
- Need to modify more than one governance policy artifact outside roadmap + architecture baseline.
- Need to introduce/alter tests or runtime code to justify architecture baseline changes.
- Discovery of coupling that forces ownership/coverage activation in same diff.

## 16. Fail-Close Criteria

Mark slice blocked/fail-closed if any of these occur:
- Architecture warning cannot be removed without changing runtime behavior.
- Roadmap refresh requires route-fence/coverage edits that materially widen scope.
- Any governance check regresses from current pass state.
- Any unplanned route progression implication appears.
