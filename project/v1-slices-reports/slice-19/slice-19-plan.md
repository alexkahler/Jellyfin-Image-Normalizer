# Slice 19 Plan

## Slice Id and Title
- Slice id: `A-05`
- Slice title: `High-coupling closure slot 1 (adaptive) - pipeline.py`

## Objective
Reduce `src/jfin/pipeline.py` to `<=300` LOC via behavior-preserving extraction while preserving high-coupling pipeline semantics.

## Adaptive Revalidation Basis
- Prior touched module (`config.py`) is `<=300`, so continuation rule does not apply.
- High-tier blockers are `pipeline.py` (`1059`) and `cli.py` (`817`).
- Selected target for A-05: `pipeline.py` (higher overage first).

## In-Scope / Out-of-Scope
- In scope: `src/jfin/pipeline.py` plus at most one adjacent helper module.
- Out of scope: route flips, route-fence artifact changes, CLI/config semantic redesign.

## Target Files
- `src/jfin/pipeline.py`
- `src/jfin/pipeline_core.py` (new helper module, if needed)

## Public Interfaces Affected
- Preserve signatures/behavior for pipeline entrypoints:
  - `normalize_item_image_api`
  - `normalize_item_backdrops_api`
  - `process_discovered_items`
  - `process_libraries_via_api`
  - `normalize_profile_user`
  - `process_profiles`
  - `process_single_item_api`
  - `process_single_profile`

## Acceptance Criteria
- `src/jfin/pipeline.py` is `<=300` LOC.
- No touched `src/` file exceeds 300 LOC.
- Net `src` LOC delta is `<=150` unless justified.
- Pipeline regression matrix passes for changed flows.
- `tests/characterization/safety_contract/test_safety_contract_pipeline.py` passes.
- `verify_governance --check architecture` passes.
- If closure cannot meet budget/time constraints, split to `A-05a/A-05b` before merge.

## Exact Verification Commands
```powershell
@('src/jfin/pipeline.py','src/jfin/pipeline_core.py') | ForEach-Object { if (Test-Path $_) { "{0}:{1}" -f $_, (Get-Content $_).Length } }
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline.py -k "normalize_item_backdrops_api or normalize_item_image_api or process_item_image_payload or single_item or logo_padding or backup"
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/safety_contract/test_safety_contract_pipeline.py
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
git diff --numstat -- src
```

## Rollback Step
`git revert <A-05 commit>` and rerun the verification commands above.

## Behavior-Preservation Statement
Structural extraction only; preserve pipeline ordering/side effects, dry-run gates, and control-plane semantics.

## Implementation Steps
1. Extract orchestration internals into one helper module with direct-lift behavior.
2. Keep `pipeline.py` as compatibility facade preserving call order and side effects.
3. Preserve backdrop phase ordering and dry-run/write safety behavior.
4. Run targeted pipeline matrix and governance checks.
5. If closure cannot be achieved safely within one slice, stop and split to `A-05a/A-05b` with documented reason.

## Risks / Guardrails
- Risk: backdrop transaction-order drift.
- Guardrail: maintain phase order exactly and validate with safety characterization.
- Risk: monkeypatch seam breaks in tests.
- Guardrail: keep facade-level symbols/call points in `jfin.pipeline`.
- Risk: LOC closure infeasible in one pass.
- Guardrail: trigger roadmap split path (`A-05a/A-05b`) before merge.

## Expected Commit Title
`a-05: pipeline LOC closure`

## Blocked State Addendum
- Status: `BLOCKED` (stop condition triggered during implementation attempt).
- Why blocked:
  - Direct extraction attempt could not satisfy per-file `<=300` LOC for both `pipeline.py` and one-helper limit without high-risk broad rewrite.
  - Maintaining backdrop phase ordering, dry-run/write safety, and monkeypatch seams under the single-slice constraints is not safely achievable in one pass.
- Evidence:
  - `src/jfin/pipeline.py` remains `1059` LOC.
  - `verify_governance --check loc` still reports `pipeline.py` and `cli.py` as blockers.
  - No `src/` code was committed/retained for A-05 in this blocked attempt.
- Required next action (roadmap-compliant): execute formal split path `A-05a` then `A-05b` before proceeding to A-06+.
