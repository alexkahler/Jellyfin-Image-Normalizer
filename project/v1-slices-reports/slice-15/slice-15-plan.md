# Slice 15 Plan

## Slice Id and Title
- Slice id: `A-01`
- Slice title: `Imaging LOC closure`

## Objective
Reduce `src/jfin/imaging.py` from 426 LOC to `<=300` LOC using behavior-preserving internal extraction only.

## In-Scope / Out-of-Scope
- In scope: `src/jfin/imaging.py` and at most one adjacent helper module for extracted imaging internals.
- Out of scope: CLI/config semantics, route-fence semantics, pipeline architecture redesign, behavior changes.

## Target Files
- `src/jfin/imaging.py`
- `src/jfin/imaging_ops.py` (new helper module, if needed)

## Public Interfaces Affected
- `jfin.imaging` function/class import surface remains signature-compatible.
- Call sites (including `src/jfin/pipeline.py` and tests) remain unchanged unless import-preserving re-export is required.

## Acceptance Criteria
- `src/jfin/imaging.py` is `<=300` LOC.
- No touched file under `src/` exceeds 300 LOC.
- Net `src/` LOC delta is `<=150` unless explicitly justified.
- Imaging unit tests pass.
- Imaging characterization tests pass.
- Behavior remains preserved.

## Exact Verification Commands
```powershell
@('src/jfin/imaging.py') | ForEach-Object { "{0}:{1}" -f $_, (Get-Content $_).Length }
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_imaging.py
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/imaging_contract
git diff --numstat -- src
```

Additional governance verification required by touched files:
```powershell
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
```

## Rollback Step
`git revert <A-01 commit>` and rerun the verification commands above.

## Behavior-Preservation Statement
Internal structural extraction only; no intended behavior change and no contract redesign.

## Implementation Steps
1. Capture pre-change LOC and isolate extraction seams in `imaging.py`.
2. Extract rendering/encoding helper functions into one adjacent helper module.
3. Re-import and re-export moved symbols from `jfin.imaging` so existing imports remain valid.
4. Keep scale-plan/no-scale/reporting behavior unchanged.
5. Run slice verification commands and LOC/governance check.
6. Confirm net `src/` LOC delta remains within budget.

## Risks / Guardrails
- Risk: accidental image-processing behavior drift.
- Guardrail: run both unit and characterization imaging suites.
- Risk: interface break from moved functions.
- Guardrail: preserve `jfin.imaging` import surface.
- Risk: scope creep.
- Guardrail: no non-imaging module changes unless strict import fix is required.

## Expected Commit Title
`a-01: imaging LOC closure`
