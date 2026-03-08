# Slice-31 Plan

## Slice Id and Title
- Slice id: `Slice-31`
- Slice title: `Pipeline evasion remediation tranche 3c (pipeline.py first)`

## Objective
- Remove anti-evasion formatter suppression from `src/jfin/pipeline.py`.
- Keep honest formatter-compatible LOC for `src/jfin/pipeline.py` at `<=300`.
- Preserve pipeline behavior/signatures.

## Scope
- In scope:
  - `src/jfin/pipeline.py`
  - optional one adjacent helper module only if required
  - `project/v1-slices-reports/slice-31/*`
- Out of scope:
  - `src/jfin/pipeline_backdrops.py` remediation
  - route-fence, CLI/config semantics redesign
  - Theme A / A-08 closure work

## Acceptance Criteria
- `src/jfin/pipeline.py` has no `# fmt: off/on`.
- `src/jfin/pipeline.py` honest LOC `<=300`.
- No anti-evasion tactics (suppression/packing).
- `verify_governance --check loc` and `--check all` offender set contracts to exactly:
  - `src/jfin/pipeline_backdrops.py`
- `src/jfin/pipeline.py`, `src/jfin/cli_runtime.py`, `src/jfin/cli.py`, `src/jfin/client.py`, `src/jfin/client_http.py` are not flagged.
- `A-08` and Theme A remain open.

## Verification (authoritative)
```powershell
$env:PYTHONPATH='src'
git status --short
git diff --name-only -- src
git ls-files --others --exclude-standard src
rg -n "#\s*fmt:\s*(off|on)" src/jfin/pipeline.py
(Get-Content src/jfin/pipeline.py).Length
.\.venv\Scripts\python.exe -m ruff check src/jfin/pipeline.py --select E701,E702,E703
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
- `Slice-32 Pipeline evasion remediation tranche 3d (pipeline_backdrops.py)` because it will be the sole remaining anti-evasion offender after Slice-31.
