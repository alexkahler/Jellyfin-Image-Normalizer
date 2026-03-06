# Slice-12

## 1. Objective
Implement `COV-03` readiness semantics hardening for route-fence metadata with claim-scoped runtime proof, without route flips or route-table column expansion.

## 2. In-scope / Out-of-scope
In-scope: readiness semantic validation for `parity status` and `route(v0|v1)` consistency, workflow/parity/baseline/owner linkage enforcement for claimed-ready cells, readiness-blocking debt enforcement, claim-scoped runtime overlay checks, deterministic readiness error taxonomy, governance output/reporting updates, and targeted test coverage.
Out-of-scope: route flips (`v0 -> v1`), widening workflow coverage beyond the current `run|backdrop` mapping scope, moving runtime-target authority out of `project/verification-contract.yml`, and broader schema expressiveness expansion (`COV-04`).

## 3. Public interfaces affected
- `project/scripts/readiness_checks.py` (new readiness governance gate)
- `project/scripts/governance_checks.py` (`readiness` check selector + readiness reporting lines)
- `project/scripts/parity_checks.py` / `project/scripts/parity_contract.py` (`parity status` enum enforcement: `pending|ready` for markdown and JSON paths)
- `project/scripts/characterization_checks.py` (structured runtime diagnostics consumed by readiness checks)
- `project/route-fence.md` / `project/route-fence.json` (semantic contract validation path)
- `./.venv/bin/python project/scripts/verify_governance.py --check readiness`

## 4. Acceptance criteria
- Route-fence `parity status` values are enforced as `pending|ready` in both markdown and JSON validation paths.
- Claimed-ready predicate is enforced as `parity status=ready` or `route=v1`, and `route=v1` requires `parity status=ready`.
- Claimed-ready rows fail when unmapped in workflow coverage index or when readiness-blocking debt is open.
- Required parity linkage for claimed-ready rows is enforced: parity ID exists, `status=preserved`, `current_result=matches-baseline`, and `baseline_source` resolves to an existing baseline case.
- Workflow required owner tests resolve and are represented by parity owner evidence via subset-based linkage (no exact-set equality requirement).
- Runtime overlay remains claim-scoped: only runtime diagnostics intersecting the claim target set can block readiness, and unrelated runtime diagnostics do not block the claim.
- Runtime-target authority remains in `project/verification-contract.yml`; no runtime target registry is added to `project/workflow-coverage-index.json`.
- Characterization runtime gate global warn-ratchet behavior from Slice 10 remains unchanged.

## 5. Verification commands (<10 min)
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_parity_route_status.py tests/test_readiness_checks.py tests/test_readiness_runtime_overlay.py tests/test_governance_readiness.py tests/test_characterization_runtime_gate.py tests/test_governance_runtime_gate.py`
- `./.venv/bin/python project/scripts/verify_governance.py --check parity`
- `./.venv/bin/python project/scripts/verify_governance.py --check readiness`
- `./.venv/bin/python project/scripts/verify_governance.py --check all` (expect only known pre-existing LOC blockers)
- `PYTHONPATH=src ./.venv/bin/python -m pytest`
- `./.venv/bin/python -m ruff check .`
- `./.venv/bin/python -m ruff format --check .`
- `./.venv/bin/python -m mypy src`
- `./.venv/bin/python -m bandit -r src`
- `./.venv/bin/python -m pip_audit`

## 6. Rollback step
Revert Slice 12 commits in reverse order: docs/work-item updates, readiness/parity/governance test additions, governance output/selector wiring, parity-status enum enforcement updates, structured runtime diagnostic additions, and readiness check module introduction.

## 7. Behavior-preservation statement
Preserved by default. Slice 12 hardens governance metadata semantics and readiness proof validation only, with no intended runtime behavior changes in `src/jfin`.
