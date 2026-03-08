# Slice 22 Audit Report

## Slice Id and Title
- Slice id: `A-06`
- Slice title: `High-coupling closure slot 2 (adaptive) - cli.py`
- Audit date: `2026-03-07`

## Verdict
- **Compliant for A-06 closure (with minor governance warning only).**
- `src/jfin/cli.py` is now under the LOC contract (`288 <= 300`), targeted CLI verification passed, and architecture check passed.

## What Changed
- `src/jfin/cli.py` was reduced to a compatibility-focused facade (`288` LOC) that preserves exported CLI functions and delegates parser/runtime orchestration internals.
- Added `src/jfin/cli_runtime.py` (`287` LOC) to host extracted parser construction and runtime execution flow.
- Maintained compatibility seams expected by tests through `jfin.cli` namespace usage in runtime delegation.

## Acceptance Checklist
- [x] `src/jfin/cli.py` is `<=300` LOC.
- [x] All touched `src/` Python files are `<=300` LOC.
- [x] CLI behavior and option semantics validated by targeted CLI tests/characterization.
- [x] Route enforcement remains fail-closed (covered by route-fence runtime tests).
- [x] Entry/exit behavior remains compatible and architecture-compliant.
- [x] `verify_governance.py --check loc` executed and no `src/` blockers remain.
- [x] `verify_governance.py --check architecture` executed and passed.
- [x] `git diff --numstat -- src` evidence captured (with new-file caveat documented).
- [x] Net `src/` LOC delta exceeds 150 by absolute value but is justified by required high-coupling blocker closure (`cli.py` monolith decomposition).

## Verification Commands and Results
1. LOC probe
```powershell
@('src/jfin/cli.py','src/jfin/cli_runtime.py') | ForEach-Object { if (Test-Path $_) { "{0}:{1}" -f $_, (Get-Content $_).Length } }
```
Result:
```text
src/jfin/cli.py:288
src/jfin/cli_runtime.py:287
```

2. LOC governance check
```powershell
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
```
Result: **PASS**
- No `src/` blockers reported.
- Existing test-size warnings remain (non-blocking per contract).

3. Architecture governance check
```powershell
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check architecture
```
Result: **PASS with warning**
```text
WARN: architecture: exit counter dropped below baseline for src/jfin/pipeline.py.system_exit_raises: observed 2, baseline 5. Update project/architecture-baseline.json to ratchet downward.
```

4. CLI unit/regression matrix
```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_jfin.py
```
Result: **PASS**
```text
33 passed in 1.07s
```

5. CLI characterization matrix
```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/characterization/cli_contract/test_cli_contract_characterization.py
```
Result: **PASS**
```text
6 passed in 0.97s
```

6. Route-fence runtime matrix
```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_route_fence_runtime.py
```
Result: **PASS**
```text
9 passed in 1.02s
```

7. Source diff inventory
```powershell
git diff --numstat -- src
```
Result:
```text
54 583 src/jfin/cli.py
```
Caveat:
- `src/jfin/cli_runtime.py` is a new untracked file and therefore not included in `git diff --numstat` output until staged.

## LOC / Governance Status
- `src/` blocker posture after A-06:
  - `cli.py` blocker is closed (`288 <= 300`).
  - `pipeline.py` remains closed (`284 <= 300`).
  - No remaining `src/` LOC blockers.
- Governance checks for this slice:
  - `--check loc`: pass (test warnings only).
  - `--check architecture`: pass with one non-blocking ratchet warning.

## Behavior-Preservation Assessment
- Public CLI entrypoints and compatibility import surface (`jfin.cli.*`) remain present.
- Targeted CLI tests, CLI characterization, and route-fence runtime tests all pass, supporting preserved behavior for command parsing, route enforcement, and execution flow.
- No evidence of dry-run/write safety or route behavior regression in slice-local verification.

## Issues Found
- **Minor:** architecture ratchet warning for `src/jfin/pipeline.py` exit counter baseline drift (`observed 2`, baseline `5`).
- **No major blockers** for A-06 closure.

## Whether Fixes Were Required
- **Yes (in-slice, pre-audit closure):** helper exit ownership was adjusted so `SystemExit` raising remains controlled at CLI entrypoint level, resolving prior non-entry architecture violation.
- **No additional post-audit fixes required.**

## Final Closure Recommendation
- **Close A-06.**
- Proceed to adaptive revalidation for A-07 eligibility:
  - Rerun `verify_governance.py --check loc` / blocker posture checks.
  - If all `src/` blockers remain closed, A-07 becomes the correct next slice gate candidate.
