# Slice-08

## 1. Objective
Enforce route-fence dispatch at runtime for current user entrypoints while keeping all routes on `v0` and adding parity-gated markdown-to-JSON synchronization.

## 2. In-scope / Out-of-scope
In-scope: `project/route-fence.json`, route-fence JSON generator/check script, route-fence markdown markers, parity JSON sync validation, runtime route loader/resolver, CLI entrypoint gating, targeted tests, and docs/slice artifact updates.
Out-of-scope: route flips (`v0 -> v1`), v1 use-case implementations, CLI redesign, and unrelated runtime refactors.

## 3. Public interfaces affected
- `project/route-fence.md` (canonical table with machine markers)
- `project/route-fence.json`
- `./.venv/bin/python project/scripts/generate_route_fence_json.py --write`
- `./.venv/bin/python project/scripts/generate_route_fence_json.py --check`
- `./.venv/bin/python project/scripts/verify_governance.py --check parity`

## 4. Acceptance criteria
- Runtime dispatch is gated for: `config_init|n/a`, `test_connection|n/a`, `restore|logo|thumb|backdrop|profile`, and `run|logo|thumb|backdrop|profile`.
- Runtime route-fence failures are fail-closed and map to existing validation/policy exit class (`1`).
- `project/route-fence.md` and `project/route-fence.json` remain exactly synchronized under parity checks.
- `RUNTIME_GATED_ROUTE_KEYS` is fully covered by generated JSON rows.
- No route row is flipped to `v1` in Slice 8.

## 5. Verification commands (<10 min)
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_route_fence_json_sync.py tests/test_route_fence_runtime.py`
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_parity_checks.py tests/test_governance_checks.py -k "parity or route_fence"`
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_jfin.py -k "generate_config or test_jf or restore_all or exit_code or route_fence"`
- `./.venv/bin/python project/scripts/generate_route_fence_json.py --check`
- `./.venv/bin/python project/scripts/verify_governance.py --check parity`
- `./.venv/bin/python project/scripts/verify_governance.py --check characterization`
- `./.venv/bin/python project/scripts/verify_governance.py --check all`

## 6. Rollback step
Revert Slice 8 commits in reverse order: docs/slice artifacts, CLI/runtime route-fence support, parity sync checks, generator script, and `project/route-fence.json`.

## 7. Behavior-preservation statement
Preserved by default. Slice 8 introduces fail-closed runtime dispatch gating from existing route-fence artifacts without changing active behavior because all current route rows remain `v0`.
