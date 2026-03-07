# Slice 21 Audit Report

## Slice Id and Slice Title
- Slice id: `A-05b`
- Slice title: `Pipeline LOC closure split tranche 2 (pipeline blocker closure)`
- Audit date: `2026-03-07`

## Verdict
- **Compliant for A-05b closure (with minor governance warning only)**.
- `src/jfin/pipeline.py` is now under the LOC contract (`284 <= 300`), behavior-preserving checks passed, and architecture check passed.

## What Changed
- `src/jfin/pipeline.py` was reduced to a compatibility facade (`284` LOC) that delegates to focused helper modules while preserving public function signatures.
- Added helper modules:
  - `src/jfin/pipeline_image_normalization.py` (`184` LOC)
  - `src/jfin/pipeline_image_payload.py` (`102` LOC)
  - `src/jfin/pipeline_orchestration.py` (`196` LOC)
  - `src/jfin/pipeline_profiles.py` (`231` LOC)
- Existing backdrop helper from A-05a remains unchanged and at contract limit:
  - `src/jfin/pipeline_backdrops.py` (`300` LOC)
- One in-slice corrective fix was applied after initial architecture failure:
  - Removed non-entry `SystemExit` raises from `pipeline_profiles.py` helper flow.
  - Restored exit behavior in `pipeline.py` wrapper (`process_single_profile`) so behavior is preserved and architecture guard passes.

## Acceptance Checklist
- [x] `src/jfin/pipeline.py` is `<=300` LOC.
- [x] All touched `src/` files are `<=300` LOC.
- [x] Backdrop phased ordering behavior preserved (fetch/stage -> normalize/prepare -> delete+404 verify -> upload -> cleanup/finalize).
- [x] Dry-run/write safety checks preserved for targeted pipeline flows.
- [x] Monkeypatch seam compatibility preserved through `jfin.pipeline` facade and targeted tests.
- [x] Targeted pipeline regression matrix passes.
- [x] Pipeline safety characterization passes.
- [x] `verify_governance.py --check architecture` passes.
- [x] `verify_governance.py --check loc` executed with evidence.
- [x] `git diff --numstat -- src` executed and caveat on untracked new files documented.

## Verification Commands and Results
1. LOC probe
```powershell
@('src/jfin/pipeline.py','src/jfin/pipeline_backdrops.py','src/jfin/pipeline_image_normalization.py','src/jfin/pipeline_image_payload.py','src/jfin/pipeline_orchestration.py','src/jfin/pipeline_profiles.py') | ForEach-Object { if (Test-Path $_) { "{0}:{1}" -f $_, (Get-Content $_).Length } }
```
Result:
```text
src/jfin/pipeline.py:284
src/jfin/pipeline_backdrops.py:300
src/jfin/pipeline_image_normalization.py:184
src/jfin/pipeline_image_payload.py:102
src/jfin/pipeline_orchestration.py:196
src/jfin/pipeline_profiles.py:231
```

2. LOC governance check
```powershell
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
```
Result: **FAIL (expected residual non-pipeline blocker)**
```text
ERROR: src/jfin/cli.py has 817 lines (max 300).
```
Note: `pipeline.py` is no longer listed as a blocker.

3. Targeted pipeline regression matrix
```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline.py -k "normalize_item_backdrops_api or normalize_item_image_api or process_item_image_payload or single_item or logo_padding or backup"
```
Result: **PASS**
```text
24 passed in 1.49s
```

4. Pipeline safety characterization
```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/safety_contract/test_safety_contract_pipeline.py
```
Result: **PASS**
```text
2 passed in 1.16s
```

5. Architecture governance check
```powershell
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
```
Result: **PASS with warning**
```text
WARN: architecture: exit counter dropped below baseline for src/jfin/pipeline.py.system_exit_raises: observed 2, baseline 5. Update project/architecture-baseline.json to ratchet downward.
```

6. Source diff inventory
```powershell
git diff --numstat -- src
```
Result:
```text
64 580 src/jfin/pipeline.py
```
Caveat: new helper files are currently untracked and therefore not shown in `git diff --numstat`. Verified separately via:
```powershell
git status --short src/jfin
git ls-files --others --exclude-standard src/jfin | rg "pipeline_"
```

## LOC / Governance Status
- A-05b objective status:
  - `pipeline.py` LOC blocker is closed (`284 <= 300`).
- Remaining global LOC blocker:
  - `src/jfin/cli.py: 817`.
- Governance checks:
  - `--check loc`: fails only due `cli.py` (expected residual blocker for next adaptive slice).
  - `--check architecture`: passes with one ratchet warning (non-blocking).

## Behavior-Preservation Assessment
- No behavior regression found in targeted A-05b matrices.
- Safety characterization for pipeline path remains green.
- Critical behavior semantics preserved:
  - backdrop phase ordering
  - dry-run/write gating
  - compatibility facade for `jfin.pipeline` entrypoints

## Issues Found
- **Minor**: Architecture ratchet warning for reduced `SystemExit` count in `pipeline.py` baseline.
  - Impact: none on runtime behavior; governance metadata follow-up needed later.
- **No major blockers** for A-05b closure.

## Fixes Required
- Major fixes required to close A-05b: **No**.
- In-slice fix applied: **Yes** (moved non-entry exit behavior out of helper module to satisfy architecture rules while preserving semantics).

## Final Closure Recommendation
- **Close A-05b**.
- Treat A-05 split path (`A-05a` + `A-05b`) as resolved.
- Proceed to adaptive revalidation gate immediately:
  - rerun `verify_governance.py --check loc`
  - since `pipeline.py` is closed and `cli.py` remains `>300`, next correct target is the remaining high-coupling blocker (`cli.py`) for the next slice (A-06 path).
