# Slice 28 Implementation

## Slice Id and Title
- Slice id: `Slice-28`
- Slice title: `Runtime evasion remediation tranche 1 (config pair)`

## Scope Executed
- Behavior-preserving runtime evasion remediation for:
  - `src/jfin/config.py`
  - `src/jfin/config_core.py`
- Removed formatter suppression usage in both target files.
- Kept all edits within the config pair scope.
- `A-08` remains open.

## Change Summary
- `src/jfin/config.py`
  - Removed `# fmt: off`.
  - Applied formatter-compatible wrapping adjustments only.
  - Preserved existing public function signatures and behavior.
- `src/jfin/config_core.py`
  - Removed `# fmt: off`.
  - Applied small behavior-preserving structural cleanups in list parsing/override/type-validation helpers.
  - Added `TypeGuard`-based typing helper annotations to restore strict mypy compatibility without behavior change.

## LOC Evidence
- Pre-change (from Slice 26 honest baseline):
  - `src/jfin/config.py`: `301`
  - `src/jfin/config_core.py`: `319`
- Post-change:
  - `src/jfin/config.py`: `300`
  - `src/jfin/config_core.py`: `298`

## Anti-Evasion Evidence
- `git grep -n "# fmt: off\|# fmt: on" -- src/jfin/config.py src/jfin/config_core.py`
  - No matches.
- `ruff` one-line packing checks:
  - `.\.venv\Scripts\python.exe -m ruff check src/jfin/config.py src/jfin/config_core.py --select E701,E702,E703`
  - Result: pass.
- Governance fail-closed checks:
  - `verify_governance --check loc` and `--check all` remain non-zero globally (expected while other runtime files still contain anti-evasion violations).
  - Output no longer reports anti-evasion findings for `src/jfin/config.py` or `src/jfin/config_core.py`.

## Verification Commands and Outcomes
```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m pytest -q tests/test_config.py tests/characterization/config_contract/test_config_contract_characterization.py
# PASS (32 passed)

.\.venv\Scripts\python.exe -m ruff check src/jfin/config.py src/jfin/config_core.py --select E701,E702,E703
# PASS

.\.venv\Scripts\python.exe -m ruff check .
# PASS

.\.venv\Scripts\python.exe -m ruff format --check .
# PASS

.\.venv\Scripts\python.exe -m pytest
# PASS (360 passed)

.\.venv\Scripts\python.exe -m mypy src
# PASS

.\.venv\Scripts\python.exe -m bandit -r src
# PASS

.\.venv\Scripts\python.exe -m pip_audit
# PASS (no known vulnerabilities; local package skip note expected)

.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
# FAIL with expected non-zero due remaining anti-evasion offenders outside this slice; config/config_core not flagged

.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
# FAIL with expected non-zero due loc fail-closed posture; config/config_core not flagged

git diff --numstat -- src/jfin/config.py src/jfin/config_core.py
# Evidence captured
```

## A-08 Status
- `A-08` / `GG-008` is not closed in Slice 28 and remains open.
