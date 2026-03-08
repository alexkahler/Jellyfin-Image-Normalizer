# Slice 20 Plan

## Slice Id and Title
- Slice id: `A-05a`
- Slice title: `Pipeline LOC closure split tranche 1 (blocked-state recovery)`

## Objective
Execute the first split tranche for blocked A-05 by extracting one cohesive backdrop orchestration seam from `src/jfin/pipeline.py` into a single helper module, preserving facade compatibility and reducing `pipeline.py` from the blocked baseline (`1059` LOC).

## In-Scope / Out-of-Scope
- In scope: direct-lift extraction of the backdrop phased orchestration flow behind `normalize_item_backdrops_api`.
- In scope: compatibility facade/wrapper updates in `pipeline.py` so public imports and monkeypatch seams remain stable.
- In scope: minimal wiring needed for the helper module to use existing safety-sensitive behavior.
- Out of scope: full `pipeline.py <=300` closure (reserved for `A-05b`).
- Out of scope: `cli.py`, CLI/config semantic changes, route-fence artifact changes, architecture redesign.

## Target Files
- `src/jfin/pipeline.py`
- `src/jfin/pipeline_backdrops.py` (single helper module)

## Public Interfaces Affected
- Preserve signatures and behavior for:
  - `normalize_item_image_api`
  - `normalize_item_backdrops_api`
  - `process_discovered_items`
  - `process_libraries_via_api`
  - `normalize_profile_user`
  - `process_profiles`
  - `process_single_item_api`
  - `process_single_profile`
- Preserve test seams currently monkeypatched through `jfin.pipeline`:
  - `IMAGE_TYPE_TO_MODE`
  - `_normalize_image_bytes`
  - `guess_extension_from_content_type`
  - `state`

## Explicit Seam Extraction and A-05b Residual
- A-05a extracted seam:
  - Backdrop orchestration phases under `normalize_item_backdrops_api`: fetch/stage, normalize/prepare, delete+404 verify, upload, cleanup/finalize.
- What remains for A-05b:
  - Remaining non-backdrop pipeline orchestration functions and shared image/profile flow still in `pipeline.py`.
  - Final decomposition needed to bring `src/jfin/pipeline.py` to `<=300` LOC while preserving current behavior.

## Acceptance Criteria
- One-helper seam extraction is complete and behavior-preserving.
- `src/jfin/pipeline.py` LOC is measurably reduced from baseline (`1059`).
- New helper module remains `<=300` LOC.
- No new `src/` LOC blocker is introduced beyond known pre-slice blockers.
- Net `src/` LOC delta is `<=150` unless justified in this slice report.
- Targeted pipeline regression matrix passes.
- `tests/characterization/safety_contract/test_safety_contract_pipeline.py` passes.
- `verify_governance.py --check architecture` passes.
- `verify_governance.py --check loc` is run and evidence is captured/documented.
- Residual work for A-05b is explicitly documented.

## Exact Verification Commands
```powershell
@('src/jfin/pipeline.py','src/jfin/pipeline_backdrops.py') | ForEach-Object { if (Test-Path $_) { "{0}:{1}" -f $_, (Get-Content $_).Length } }
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline.py -k "normalize_item_backdrops_api or normalize_item_image_api or process_item_image_payload or single_item or logo_padding or backup"
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/safety_contract/test_safety_contract_pipeline.py
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
git diff --numstat -- src
```

## Rollback Step
`git revert <A-05a commit>` and rerun the commands above.

## Behavior-Preservation Statement
This is structural extraction only. Backdrop sequencing, dry-run/write safety, and pipeline control-flow semantics must remain unchanged.

## Implementation Steps
1. Extract backdrop-phase orchestration logic from `pipeline.py` into `pipeline_backdrops.py` using direct-lift logic moves (no semantic rewrites).
2. Keep `pipeline.py` exporting `normalize_item_backdrops_api` and preserve existing signatures/import paths.
3. Preserve monkeypatch seam compatibility by resolving seam-sensitive symbols through `jfin.pipeline` facade state.
4. Verify backdrop phase ordering and dry-run/write safety invariants via targeted tests.
5. Capture post-slice LOC and explicitly document remaining A-05b closure work.

## Risks / Guardrails
- Risk: backdrop phase-order drift.
- Guardrail: no logic rewrites; direct-lift extraction and targeted safety characterization.
- Risk: monkeypatch seam break in existing tests.
- Guardrail: keep seam-sensitive lookups anchored to `jfin.pipeline` compatibility surface.
- Risk: unintended slice expansion.
- Guardrail: one seam, one helper, one objective only.

## Expected Commit Title
`a-05a: pipeline LOC closure tranche 1`
