Implemented end-to-end.

Applied skills: `loc-and-complexity-discipline`, `verification-gates-and-diff-discipline`, `docs-self-healing-update-loop`.

## What changed
- Added runtime route-fence resolver module:
  - `src/jfin/route_fence.py`
- Added runtime dispatch gating in CLI:
  - `src/jfin/cli.py`
- Added canonical markers to route-fence markdown:
  - `project/route-fence.md`
- Added generated runtime artifact:
  - `project/route-fence.json`
- Added route-fence generator/check script:
  - `project/scripts/generate_route_fence_json.py`
- Extended parity checks for marker parsing plus markdown-to-JSON sync:
  - `project/scripts/parity_checks.py`
  - `project/scripts/parity_contract.py`
- Added/updated tests:
  - `tests/test_route_fence_json_sync.py`
  - `tests/test_route_fence_runtime.py`
  - `tests/test_parity_checks.py`
- Updated docs/slice artifacts:
  - `README.md`
  - `docs/TECHNICAL_NOTES.md`
  - `WORK_ITEMS.md`
  - `plans/Slice-08.md`
  - `project/v1-slices-reports/slice-8/slice-8-plan.md`

## Runtime contract implemented
- Runtime-gated entrypoints:
  - `config_init|n/a`
  - `test_connection|n/a`
  - `restore|logo|thumb|backdrop|profile`
  - `run|logo|thumb|backdrop|profile`
- `config_validate|n/a` kept as artifact inventory only (not runtime-gated in Slice 8).
- Fail-closed behavior implemented for missing/invalid/unresolvable route lookups.
- `v1` route values fail closed with explicit command/mode/path message.
- Exit behavior remains validation/policy class (`SystemExit(1)`).

## Verification run
Targeted Slice 8 checks:
1. `PYTHONPATH=src py -3.13 -m pytest -q tests/test_route_fence_json_sync.py tests/test_route_fence_runtime.py`
   - `14 passed`
2. `PYTHONPATH=src py -3.13 -m pytest -q tests/test_parity_checks.py tests/test_governance_checks.py -k "parity or route_fence"`
   - `11 passed, 9 deselected`
3. `PYTHONPATH=src py -3.13 -m pytest -q tests/test_jfin.py -k "generate_config or test_jf or restore_all or exit_code or route_fence"`
   - `33 passed`
4. `python project/scripts/generate_route_fence_json.py --check`
   - `route-fence JSON is synchronized`
5. `python project/scripts/verify_governance.py --check parity`
   - `[PASS] parity`
6. `python project/scripts/verify_governance.py --check characterization`
   - `[PASS] characterization` with zero unmapped counts
7. `python project/scripts/verify_governance.py --check all`
   - Fails only on pre-existing LOC gate violations in `src/jfin/*` plus pre-existing oversized test warnings

Additional full-gate commands from verification contract:
- `py -3.13 -m ruff check .` -> pass
- `py -3.13 -m ruff format --check .` -> fails on pre-existing repo formatting drift (includes files outside Slice 8 scope)
- `py -3.13 -m mypy src` -> pass
- `py -3.13 -m bandit -r src` -> pass
- `py -3.13 -m pip_audit` -> pass (`jfin` package skipped as local/non-PyPI)
- `PYTHONPATH=src py -3.13 -m pytest` -> fails in pre-existing characterization message-capture tests unrelated to Slice 8 route-fence behavior

## Scope and LOC discipline note
- Objective remained single-slice: runtime route-fence enforcement and artifact sync.
- Added minimal new runtime surface (`src/jfin/route_fence.py`) and focused `src/jfin/cli.py` gating hooks.
- No route rows were flipped from `v0` to `v1`.
