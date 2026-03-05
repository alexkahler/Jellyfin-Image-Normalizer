# Slice 8: Runtime Route-Fence Enforcement (Final Replacement)

## Summary
1. Enforce route-fence at runtime for current user-invoked entrypoints before any `v0 -> v1` flips.
2. Keep `project/route-fence.md` canonical, generate and commit `project/route-fence.json`, and parity-gate Markdown↔JSON sync.
3. Use fail-closed behavior for missing/invalid/unresolvable runtime route lookup, mapped to the existing validation/policy failure exit-code class (`OBS-EXITCODE-001`, currently `1`).
4. Apply minimal `src/` changes only for dispatch gating (`src/jfin/route_fence.py` + focused `src/jfin/cli.py` wiring), no broader refactor.
5. Applied skill: `loc-and-complexity-discipline` (small, bounded runtime change).

## Scope
1. In scope:
`project/route-fence.json`, route-fence JSON generator/check script, parity sync checks, runtime route loader/resolver, CLI entrypoint gating, targeted tests, and slice docs.
2. Out of scope:
route flips, new v1 processors/use-cases, CLI UX redesign, and unrelated runtime restructuring.

## Important Interface and Type Additions
1. New committed artifact: `project/route-fence.json`.
2. New script interface:
`python project/scripts/generate_route_fence_json.py --write`
`python project/scripts/generate_route_fence_json.py --check`
3. JSON schema (fixed):
`version: int`
`rows: list[RouteFenceRow]`
`RouteFenceRow = {command, mode, route, owner_slice, parity_status}`.
4. New runtime module API in `src/jfin/route_fence.py`:
`load_route_table()`
`resolve_route(command: str, mode: str) -> str`
`RouteFenceError`.
5. New runtime constant:
`RUNTIME_GATED_ROUTE_KEYS` (explicit set of keys the CLI must gate).

## Canonical Markdown and Marker Contract
1. Keep the human-readable route-fence table in `project/route-fence.md` as canonical.
2. Add explicit machine markers around that table (HTML comment markers), documented in README/TECHNICAL_NOTES.
3. Generator must parse only the marked table block and require exact expected headers.
4. Parity validator remains artifact-level and deterministic; no imports from `src/`.

## Deterministic Repo-Root Resolution
1. Runtime must not use `cwd`.
2. `route_fence.py` resolves repo root by walking upward from `Path(__file__).resolve()` and finding `project/route-fence.json` (or `project/route-fence.md`) within a bounded max depth.
3. If not found, raise `RouteFenceError` and fail closed.

## Runtime Gating Semantics (Slice 8)
1. Gate only user-invoked entrypoints:
`config_init|n/a` for `--generate-config`
`test_connection|n/a` for `--test-jf`
`restore|logo|thumb|backdrop|profile` for restore flows
`run|logo`, `run|thumb`, `run|backdrop`, `run|profile` for processing flows.
2. Do not runtime-gate `config_validate|n/a` in Slice 8; keep it as artifact inventory row.
3. `v0` route executes existing path.
4. `v1` route fails closed with explicit message containing command, mode, and JSON path.

## Implementation Steps
1. Add `project/scripts/generate_route_fence_json.py` with deterministic output and `--check` drift detection.
2. Add committed `project/route-fence.json` from current markdown rows.
3. Extend `project/scripts/parity_checks.py` to validate JSON schema and Markdown↔JSON exact row/value sync.
4. Add `src/jfin/route_fence.py`:
upward repo-root discovery, JSON load/validate, key lookup, typed errors, `RUNTIME_GATED_ROUTE_KEYS`.
5. Wire `src/jfin/cli.py` to resolve route before each gated entrypoint executes side effects.
6. Route-fence failure path in CLI uses existing validation/policy failure behavior (`state.log.critical`, `state.stats.record_error`, exit class currently `1`).
7. Update docs and slice artifacts (`plans/Slice-08.md`, `project/v1-slices-reports/slice-8/*`, README, TECHNICAL_NOTES, WORK_ITEMS).

## Tests and Scenarios
1. Generator writes deterministic JSON from marked markdown block.
2. Generator `--check` fails on drift, missing markers, header drift, and row mismatch.
3. Parity check passes on synchronized artifacts and fails on Markdown↔JSON mismatch.
4. Parity checks remain artifact-only (no dependency on `src` runtime modules).
5. Repo-root discovery succeeds from varied `cwd` and nested invocation contexts.
6. Repo-root discovery fails cleanly when no route-fence artifact exists in ancestor chain.
7. Runtime load fails closed on missing JSON.
8. Runtime load fails closed on malformed JSON and unknown route values.
9. Hard alignment test:
every key in `RUNTIME_GATED_ROUTE_KEYS` must exist in generated JSON rows; missing key fails CI.
10. CLI integration:
representative command succeeds with valid JSON (`--generate-config`).
11. CLI integration:
same command fails closed with expected validation/policy exit class and clear message when JSON is missing.
12. CLI integration:
forced `v1` route for a gated key fails closed with command/mode/path in message.

## Acceptance Criteria
1. Runtime dispatch is route-fence controlled for Slice 8 gated entrypoints.
2. Markdown↔JSON sync is parity-gated.
3. Runtime failure mode is fail-closed and exit-code-class compatible with `OBS-EXITCODE-001` (currently `1`).
4. `RUNTIME_GATED_ROUTE_KEYS` has full row coverage in generated JSON (hard test).
5. No route flips occur.
6. `src/` edits are limited to dispatch gating and route-fence runtime support only.

## Verification Commands (<10 min)
1. `PYTHONPATH=src py -3.13 -m pytest -q tests/test_route_fence_json_sync.py tests/test_route_fence_runtime.py`
2. `PYTHONPATH=src py -3.13 -m pytest -q tests/test_parity_checks.py tests/test_governance_checks.py -k "parity or route_fence"`
3. `PYTHONPATH=src py -3.13 -m pytest -q tests/test_jfin.py -k "generate_config or test_jf or restore_all or exit_code or route_fence"`
4. `python project/scripts/generate_route_fence_json.py --check`
5. `python project/scripts/verify_governance.py --check parity`
6. `python project/scripts/verify_governance.py --check characterization`
7. `python project/scripts/verify_governance.py --check all` (no new failures beyond known pre-existing LOC blockers).

## Rollback
1. Revert CLI route-gating changes.
2. Revert `src/jfin/route_fence.py`.
3. Revert parity sync enforcement and generator script.
4. Remove `project/route-fence.json`.
5. Revert docs/slice artifacts.
6. Re-run parity and characterization checks to confirm baseline restoration.

## Assumptions and Defaults
1. Track 1 remains repo-runtime oriented; installed-package support is out of scope for Slice 8.
2. Existing validation/policy failure exit class remains unchanged (currently `1`).
3. `project/route-fence.md` remains canonical; JSON is generated and committed.
4. Marker contract is part of canonical docs and treated as governance-enforced.
