# Slice-32 Plan

## Slice Id and Title
- Slice id: `Slice-32`
- Slice title: `Pipeline evasion remediation tranche 3d (pipeline_backdrops.py)`

## Objective
- Remove anti-evasion suppression from `src/jfin/pipeline_backdrops.py`.
- Keep honest formatter-compatible LOC for `src/jfin/pipeline_backdrops.py` at `<=300`.
- Preserve backdrop safety/phase semantics.

## Scope
- In scope:
  - `src/jfin/pipeline_backdrops.py`
  - optional one adjacent helper module only if required
  - `project/v1-slices-reports/slice-32/*`
- Out of scope:
  - unrelated runtime cleanup
  - route-fence or safety-contract redesign
  - same-SHA CI closure work

## Acceptance Criteria
- `src/jfin/pipeline_backdrops.py` has no `# fmt: off/on`.
- Honest LOC `<=300`.
- No anti-evasion tactics.
- `verify_governance --check loc` and `--check all` have no anti-evasion offenders in `src/`.
- `A-08` remains open; Theme A remains open (until Slice-33 evidence gate).

## Verification (authoritative)
```powershell
$env:PYTHONPATH='src'
git status --short
git diff --name-only -- src
git ls-files --others --exclude-standard src
rg -n "#\s*fmt:\s*(off|on)" src/jfin/pipeline_backdrops.py
(Get-Content src/jfin/pipeline_backdrops.py).Length
.\.venv\Scripts\python.exe -m ruff check src/jfin/pipeline_backdrops.py --select E701,E702,E703
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline.py tests/characterization/safety_contract/test_safety_contract_pipeline.py tests/test_jfin.py tests/test_route_fence_runtime.py
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
.\.venv\Scripts\python.exe -m ruff format --check .
git diff --numstat -- src
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit
```

## Next Slice
- `Slice-33 A-08 same-SHA CI proof + Theme A closure gate`.
