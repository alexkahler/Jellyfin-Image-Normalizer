# Slice 30 Implementation (Slice-29a)

Date: 2026-03-08

## Slice Id and Title
- Slice id: `Slice-29a`
- Slice title: `Runtime evasion remediation tranche 2a (client_http first, decomposed)`

## Execution Summary
- Implemented the approved Slice-29a plan objective: clear anti-evasion suppression from `src/jfin/client_http.py` while preserving behavior.
- Initial direct suppression removal + formatter pass raised `client_http.py` to 317 LOC (>300).
- Applied the plan-allowed minimal tightly-coupled adjustment with `client.py`:
  - moved JSON decode helper behavior from `client_http.get_json_payload(...)` into `JellyfinClient._get_json(...)`.
  - removed `GetFn` alias and `get_json_payload(...)` from `client_http.py`.
- Final LOC state:
  - `src/jfin/client_http.py`: 293
  - `src/jfin/client.py`: 298

## Files Changed
- `src/jfin/client_http.py`
- `src/jfin/client.py`
- `project/v1-slices-reports/slice-30/slice-30-plan.md`

## Behavior Preservation Notes
- No Jellyfin API contract changes were introduced.
- Retry/backoff logic, timeout handling, TLS behavior, write/delete dry-run gate behavior, and fail-fast behavior remain unchanged.
- JSON decode behavior in `_get_json` is preserved with equivalent exception handling and log message shape.

## Verification Evidence
### Slice-29a required checks
- `rg -n "#\s*fmt:\s*(off|on)" src/jfin/client_http.py src/jfin/client.py`
  - Result: only `src/jfin/client.py:1` remains (expected for 29b).
- Honest LOC check:
  - `client_http.py LOC=293` (pass `<=300`).
- `\.venv\Scripts\python.exe -m ruff check src/jfin/client_http.py src/jfin/client.py --select E701,E702,E703`
  - Result: pass.
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_client.py tests/test_discovery.py tests/characterization/safety_contract/test_safety_contract_api.py`
  - Result: `26 passed`.
- `\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`
  - Result: expected non-zero; offender set exactly:
    - `src/jfin/cli.py`
    - `src/jfin/cli_runtime.py`
    - `src/jfin/client.py`
    - `src/jfin/pipeline.py`
    - `src/jfin/pipeline_backdrops.py`
  - `src/jfin/client_http.py` no longer flagged.
- `\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`
  - Result: expected non-zero; same exact offender set.
- Scope proof:
  - `git diff --numstat -- src`
  - Runtime scope limited to `client.py` and `client_http.py`.

### AGENTS verification contract
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest` -> pass (`360 passed, 4 warnings`).
- `\.venv\Scripts\python.exe -m ruff check .` -> pass.
- `\.venv\Scripts\python.exe -m ruff format --check .` -> pass.
- `\.venv\Scripts\python.exe -m mypy src` -> pass.
- `\.venv\Scripts\python.exe -m bandit -r src` -> pass.
- `\.venv\Scripts\python.exe -m pip_audit` -> pass.

## A-08 Status
- `A-08` remains open.
- No GG-008 same-SHA closure claim is made in this slice.

## Pending
- Independent slice audit report (`project/v1-slices-reports/slice-30/slice-30-audit.md`) required before closure commit.
