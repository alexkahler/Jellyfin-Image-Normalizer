# Slice 21 Plan

## Slice Id and Title
- Slice id: `A-05b`
- Slice title: `Pipeline LOC closure split tranche 2 (pipeline blocker closure)`

## Objective
Complete the remaining behavior-preserving decomposition required to close the `src/jfin/pipeline.py` LOC blocker after A-05a. This slice is complete only when `src/jfin/pipeline.py` is `<=300` LOC.

## In-Scope / Out-of-Scope
- In scope: residual extraction from `pipeline.py` into focused helper modules, with `pipeline.py` retained as compatibility facade.
- In scope: preserving current call ordering, side effects, dry-run/write safety, and backdrop sequencing already established in A-05a.
- In scope: preserving test seam behavior via `jfin.pipeline` for patched symbols (`state`, `IMAGE_TYPE_TO_MODE`, `_normalize_image_bytes`, `guess_extension_from_content_type`).
- Out of scope: CLI/config semantic redesign, route-fence changes, architecture redesign, route flips, unrelated cleanup.

## Target Files
- `src/jfin/pipeline.py`
- `src/jfin/pipeline_image_normalization.py` (new)
- `src/jfin/pipeline_image_payload.py` (new)
- `src/jfin/pipeline_orchestration.py` (new)
- `src/jfin/pipeline_profiles.py` (new)
- `project/v1-slices-reports/slice-21/slice-21-plan.md`
- `project/v1-slices-reports/slice-21/slice-21-audit.md` (post-implementation)
- `WORK_ITEMS.md` (status update for A-05b closure)

## Public Interfaces Affected
- Preserve signatures/behavior for:
  - `_plan_and_backup_image`
  - `_normalize_image_bytes`
  - `_process_item_image_payload`
  - `normalize_item_image_api`
  - `normalize_item_backdrops_api`
  - `process_discovered_items`
  - `process_libraries_via_api`
  - `normalize_profile_user`
  - `process_profiles`
  - `process_single_item_api`
  - `process_single_profile`
- Compatibility requirement: existing imports from `jfin.pipeline` remain valid.

## Acceptance Criteria
- `src/jfin/pipeline.py` is `<=300` LOC.
- All touched `src/` Python files are `<=300` LOC.
- Backdrop phased ordering remains preserved: fetch/stage -> normalize/prepare -> delete+404 verify -> upload -> cleanup/finalize.
- Dry-run/write safety invariants are preserved for item and backdrop write paths.
- Monkeypatch seams used by current tests remain functional via `jfin.pipeline` facade.
- Targeted pipeline regression matrix passes.
- Pipeline safety characterization passes.
- `verify_governance.py --check architecture` passes.
- `verify_governance.py --check loc` runs with evidence captured (remaining expected blocker after A-05b may be `cli.py` only).
- `git diff --numstat -- src` evidence captured and net `src/` LOC delta justified if >150.

## Exact Verification Commands
```powershell
@(
  'src/jfin/pipeline.py',
  'src/jfin/pipeline_backdrops.py',
  'src/jfin/pipeline_image_normalization.py',
  'src/jfin/pipeline_image_payload.py',
  'src/jfin/pipeline_orchestration.py',
  'src/jfin/pipeline_profiles.py'
) | ForEach-Object { if (Test-Path $_) { "{0}:{1}" -f $_, (Get-Content $_).Length } }
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline.py -k "normalize_item_backdrops_api or normalize_item_image_api or process_item_image_payload or single_item or logo_padding or backup"
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/safety_contract/test_safety_contract_pipeline.py
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
git diff --numstat -- src
```

## Rollback Step
`git revert <A-05b commit>` and rerun the A-05b verification commands above.

## Behavior-Preservation Statement
This slice is a structural refactor only. No intended behavior change. Control flow, side effects, dry-run gates, and safety semantics must remain contract-equivalent.

## Implementation Steps
1. Extract residual image normalization internals from `pipeline.py` into `pipeline_image_normalization.py` and `pipeline_image_payload.py`.
2. Extract residual collection/single-item orchestration from `pipeline.py` into `pipeline_orchestration.py`.
3. Extract residual profile orchestration from `pipeline.py` into `pipeline_profiles.py`.
4. Keep `pipeline.py` as a compatibility facade with thin delegating wrappers.
5. Ensure facade wrappers pass seam-sensitive references (`state`, callback functions, mappings) so existing monkeypatch-based tests keep working.
6. Re-check per-file LOC during extraction to keep every touched `src/` file `<=300`.
7. Run A-05b targeted verification matrix and record evidence in `slice-21-audit.md`.

## Risks / Guardrails
- Risk: seam regression from moving logic behind helpers.
- Guardrail: direct-lift function bodies; wrappers only delegate.
- Risk: monkeypatch compatibility break.
- Guardrail: route seam-sensitive lookups through `jfin.pipeline` facade wrappers.
- Risk: accidental behavior drift in dry-run/write flows.
- Guardrail: run targeted pipeline regression and safety characterization before closure.
- Risk: introducing a new LOC blocker in helper modules.
- Guardrail: enforce `<=300` per touched `src/` file continuously during implementation.

## Post-A-05b Adaptive Revalidation Rule
After A-05b closes, rerun LOC revalidation (`verify_governance.py --check loc`) before selecting the next slice:
- If `pipeline.py` is still `>300`, continue pipeline work first (do not advance).
- Otherwise select the next high-coupling blocker by roadmap rule (expected `cli.py` if still `>300`).
- Do not proceed to A-07/A-08 until A-05/A-06 dependencies are satisfied.

## Expected Commit Title
`a-05b: pipeline LOC closure tranche 2`
