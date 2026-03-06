# Slice-13

## 1. Objective
Implement `COV-04` safety schema expressiveness for `run|backdrop` by introducing structured trace contracts for `PIPE-BACKDROP-001`, while preserving existing Slice 11 sequence warn semantics and Slice 12 readiness behavior.

## 2. In-scope / Out-of-scope
In-scope: safety baseline trace schema support, backdrop trace invariant projection checks (`workflow_coverage.contract_trace_*`), backdrop characterization trace emission and observed-vs-baseline projection comparison, governance reporting lines for trace contract status, and dedicated trace-focused governance tests.
Out-of-scope: route flips (`v0 -> v1`), route-fence mapping expansion beyond `run|backdrop`, readiness semantics changes, and sequence severity ratchet changes for legacy COV-02 evidence fields.

## 3. Public interfaces affected
- `project/scripts/characterization_contract.py` (optional `expected_observations.trace.events` schema for safety rows)
- `project/scripts/characterization_checks.py` (trace taxonomy + backdrop trace projection validation)
- `project/scripts/governance_checks.py` (trace status/counter reporting lines)
- `tests/characterization/baselines/safety_contract_baseline.json` (`PIPE-BACKDROP-001` trace events)

## 4. Acceptance criteria
- `PIPE-BACKDROP-001` fails governance with `workflow_coverage.contract_trace_missing` when structured trace is absent.
- Malformed trace payloads fail as blocking schema errors.
- Backdrop trace invariant mismatches fail with `workflow_coverage.contract_trace_assertion_failed`.
- Legacy COV-02 sequence diagnostics remain unchanged (`workflow_coverage.sequence_gap.*` warn semantics).
- Governance characterization output includes trace required/validated counters and trace contract OK/NOT OK line.

## 5. Verification commands (<10 min)
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_safety.py tests/test_characterization_checks_safety_trace.py tests/test_governance_checks.py tests/characterization/safety_contract/test_safety_contract_pipeline.py`
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization`
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness`
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity`
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` (expect only known baseline LOC blockers in `src/jfin/*` plus existing test LOC warnings)
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m ruff format --check .` (known pre-existing formatting drift in `tests/test_characterization_checks_safety.py`)
- `.\.venv\Scripts\python.exe -m mypy src`
- `.\.venv\Scripts\python.exe -m bandit -r src`
- `.\.venv\Scripts\python.exe -m pip_audit`

## 6. Rollback step
Revert Slice 13 commits in reverse order: docs/work-item updates, trace reporting output tests, trace-focused governance tests, backdrop characterization trace emission updates, safety baseline trace payload changes, and trace schema/check logic additions in characterization scripts.

## 7. Behavior-preservation statement
Preserved by default. Slice 13 strengthens governance characterization contracts and parity evidence depth only; no intended runtime behavior changes in `src/jfin`.
