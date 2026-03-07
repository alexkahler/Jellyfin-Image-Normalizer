# Slice 20 Audit Report

## Slice Id and Title
- Slice id: `A-05a`
- Slice title: `Pipeline LOC closure split tranche 1 (blocked-state recovery)`
- Audit date: `2026-03-07`

## Verdict
- **Conditionally Compliant (Closed for tranche A-05a)**
- A-05 overall remains open pending `A-05b` (`pipeline.py` still above 300 LOC).

## What Changed
- Extracted backdrop orchestration seam from `src/jfin/pipeline.py` into new helper `src/jfin/pipeline_backdrops.py`.
- Replaced in-file backdrop implementation with compatibility facade delegation in `pipeline.py`.
- Preserved seam-sensitive symbols through `jfin.pipeline` facade injection:
  - `IMAGE_TYPE_TO_MODE`
  - `_normalize_image_bytes`
  - `guess_extension_from_content_type`
  - `state`

## Acceptance Checklist
- [x] One cohesive backdrop seam extracted into one helper module.
- [x] Backdrop ordering/phase semantics preserved (fetch -> normalize -> delete/404 verify -> upload -> cleanup).
- [x] Dry-run/write safety behavior preserved for backdrop path.
- [x] Monkeypatch seams remain functional via `jfin.pipeline` facade.
- [x] Measurable `pipeline.py` LOC reduction from blocked baseline (`1059 -> 800`).
- [x] New helper module is `<=300` LOC (`pipeline_backdrops.py: 300`).
- [x] Targeted pipeline regression matrix passes.
- [x] Pipeline safety characterization passes.
- [x] Architecture governance check passes.
- [x] LOC governance check run with evidence captured.
- [x] Residual closure work for `A-05b` explicitly identified.

## Verification Commands and Results
1. LOC probe
```powershell
@('src/jfin/pipeline.py','src/jfin/pipeline_backdrops.py') | ForEach-Object { if (Test-Path $_) { "{0}:{1}" -f $_, (Get-Content $_).Length } }
```
Result:
```text
src/jfin/pipeline.py:800
src/jfin/pipeline_backdrops.py:300
```

2. Governance LOC check
```powershell
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
```
Result: **FAIL (expected residual blocker posture)**
- `ERROR: src/jfin/cli.py has 817 lines (max 300).`
- `ERROR: src/jfin/pipeline.py has 800 lines (max 300).`
- Test-file warnings unchanged.

3. Targeted pipeline regression matrix
```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline.py -k "normalize_item_backdrops_api or normalize_item_image_api or process_item_image_payload or single_item or logo_padding or backup"
```
Result: **PASS**
```text
24 passed in 0.70s
```

4. Pipeline safety characterization
```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/safety_contract/test_safety_contract_pipeline.py
```
Result: **PASS**
```text
2 passed in 0.47s
```

5. Architecture governance check
```powershell
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
```
Result: **PASS**
```text
[PASS] architecture
Governance checks passed with 0 warning(s).
```

6. Source diff inventory
```powershell
git diff --numstat -- src
```
Result:
```text
19 278 src/jfin/pipeline.py
```
Notes:
- New helper file `src/jfin/pipeline_backdrops.py` added (untracked in working copy at audit time, 300 LOC).

## LOC / Governance Status
- `pipeline.py` reduced but still above contract threshold: `800 > 300`.
- `cli.py` remains `817 > 300`.
- GG-001 remains open at end of A-05a by design.
- A-05 split progression is now active and unblocked for `A-05b`.

## Behavior-Preservation Assessment
- No observed regression in targeted pipeline behavior or safety contract.
- Backdrop dry-run safety and delete/upload ordering remain consistent with existing characterization/tests.
- Compatibility facade preserves existing call sites and monkeypatch seams for current tests.

## Issues Found
- Major issues: **None for A-05a tranche objective**.
- Residual blocker (expected): `pipeline.py` still >300; requires `A-05b` closure pass.

## Fixes Required
- Immediate fixes for A-05a: **No**.
- Required next slice: **Yes (`A-05b`)** to complete pipeline LOC closure.

## Final Closure Recommendation
- **Close slice A-05a** as successfully executed blocked-state recovery tranche.
- Proceed directly to `A-05b`; do not advance to A-06/A-07/A-08 until A-05 split closure is complete.
