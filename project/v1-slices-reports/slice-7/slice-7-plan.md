# Slice 7 Plan (Final Revision): Surface Coverage Gate

## Brief Summary
1. Single objective: implement a machine-checkable Surface Coverage Gate for Track 1 externally observable behavior.
2. Canonical index: `project/surface-coverage-index.json` (one artifact only).
3. Governance wiring: run gate under `--check characterization` and therefore under `--check all`; keep `--check parity` schema-focused.
4. Close 3 high-risk uncovered behavior gaps found by the audit: summary/logging observability, scaling-flag semantics, exit-code classes.
5. Keep scope small: target `0` net `src/` LOC (all primary changes in `project/scripts`, parity artifacts, tests, docs).

## Scope
1. In scope: surface discovery, index validation, parity/test linkage checks, unmapped reporting, 3 gap closures, Slice 7 docs/report updates.
2. Out of scope: route flips, Track 2 CLI/config redesign, extra index artifacts, unrelated refactors.
3. WI attachment: Slice 7 is tracked under WI-001 governance extension; may touch WI-002/WI-004 artifacts.

## Public Interfaces / Artifacts Affected
1. New: `project/surface-coverage-index.json`.
2. Extended behavior: `python project/scripts/verify_governance.py --check characterization`.
3. Extended behavior transitively: `python project/scripts/verify_governance.py --check all`.
4. Updated parity source: `project/parity-matrix.md`.
5. Slice docs: `plans/Slice-07.md`, `WORK_ITEMS.md`, `project/v1-slices-reports/slice-7/slice-7-audit-report.md`.

## Canonical Index Contract
1. Top-level keys: `version`, `cli_items`, `config_items`, `observability_items`.
2. Required item fields: `id`, `parity_ids`, `owner_tests`, `out_of_scope`, `out_of_scope_reason`, `code_refs`, `notes`; CLI items also require `command_path` and `source_token`.
3. Owner test reference format: allow both `path::symbol` and `path`.
4. Owner test validation rules: always require existing file; if `::symbol` is provided, symbol must exist via AST.
5. Out-of-scope rules are strict:
6. If `out_of_scope=true`: `out_of_scope_reason` required and non-empty; `parity_ids` and `owner_tests` must be empty.
7. If `out_of_scope=false`: `parity_ids` and `owner_tests` must be non-empty; `out_of_scope_reason` must be empty.

## Surface Detection Rules
1. CLI source of truth: help output.
2. CLI detection behavior: always inventory root help; if subcommands are detected, also inventory each detected subcommand help.
3. No hard assertion that subcommands do not exist.
4. Determinism controls: fixed width (`COLUMNS=120`), normalized locale, stable token normalization.
5. Extraction strategy: in-process help extraction first; subprocess fallback only if import/introspection path fails.
6. Config source of truth: enumerate every key assignment in `config.example.toml` as flattened `section.key`.
7. Observability blocking scope: only Track-1 stable observability contract items; non-contract prose is report-only.

## Observability Contract Items (Blocking)
1. Final summary counters.
2. Failure list shape/content.
3. Presence/absence of warning/error classes in user-visible summary/log output.
4. Scale decision reporting when user-visible.
5. Exit-code classes for major outcomes: success, validation/policy failure, runtime/unhandled failure.

## Governance Wiring Plan
1. Add `project/scripts/surface_coverage_checks.py`.
2. Merge new gate into `project/scripts/characterization_checks.py`.
3. Keep `project/scripts/parity_checks.py` unchanged in responsibility (schema/route-fence only).
4. Ensure `--check all` prints Surface Coverage Gate report section.
5. Required report lines:
6. `Remaining unmapped CLI items: <n>`
7. `Remaining unmapped config keys: <n>`
8. `Remaining unmapped observability items: <n>`
9. `Remaining parity/test linkage gaps: <n>`

## Gap Closures (Top 3)
1. `OBS-SUMLOG-001`: summary counters, failure-list output shape, warning/error presence, and logging toggle user-visible behavior.
2. `CFG-SCALEFLAGS-001`: scaling flags semantics proven at behavior level (scale decision/processing path), with config-propagation checks only as secondary evidence.
3. `OBS-EXITCODE-001`: major exit-code class behavior (success vs validation/policy failure vs runtime/unhandled failure).

## Implementation Milestones
1. Milestone A: index schema + detector + validator module.
2. Milestone B: governance integration under characterization and stable unmapped reporting.
3. Milestone C: complete CLI/config/observability mapping with explicit out-of-scope handling.
4. Milestone D: add parity rows and tests for 3 closures.
5. Milestone E: Slice docs/report updates and WORK_ITEMS iterative-slice entry.

## Test Cases and Scenarios
1. Pass case: full mapping, valid parity IDs, valid owner tests, all remaining counts zero.
2. Fail case: missing CLI mapping.
3. Fail case: missing config mapping.
4. Fail case: missing observability contract mapping.
5. Fail case: mapped parity ID missing in parity matrix.
6. Fail case: mapped owner test file missing.
7. Fail case: mapped owner test symbol missing for `path::symbol`.
8. Fail case: invalid out-of-scope tuple (flag/reason/parity/tests mismatch).
9. Determinism case: wrapped help text still yields stable token inventory.
10. Exit-code case: tests prove major exit-code classes.

## Acceptance Criteria
1. Surface Coverage Gate is active in `--check characterization` and `--check all`.
2. Gate reports zero unmapped CLI items and zero unmapped config keys at completion; observability contract items also zero.
3. All mapped parity IDs and owner tests are valid.
4. Three high-risk gap closures have parity rows and passing tests.
5. Slice 7 artifacts follow existing report convention under `project/v1-slices-reports/slice-7/` (same root pattern used by slices 1–6).
6. Gate is declared as a prerequisite for subsequent Track-1 route-flip slices.

## Verification Commands (<10 min target)
1. `PYTHONPATH=src py -3.13 -m pytest -q tests/test_surface_coverage_checks.py`
2. `PYTHONPATH=src py -3.13 -m pytest -q tests/test_characterization_checks.py tests/test_governance_checks.py`
3. `PYTHONPATH=src py -3.13 -m pytest -q tests/test_logging_utils.py`
4. `PYTHONPATH=src py -3.13 -m pytest -q tests/test_pipeline.py tests/test_imaging.py -k "scale or no_scale or no_upscale or no_downscale"`
5. `PYTHONPATH=src py -3.13 -m pytest -q tests/test_jfin.py -k "exit or generate_config or restore_all or test_jf"`
6. `python project/scripts/verify_governance.py --check characterization`
7. `python project/scripts/verify_governance.py --check all`
8. `rg -n "Slice 7|iteratively planned|WI-001" WORK_ITEMS.md plans/Slice-07.md`

## Rollback
1. Revert docs/report updates.
2. Revert parity row additions and new tests.
3. Revert characterization-gate integration.
4. Revert coverage checker and index artifact.
5. Re-run characterization/all governance checks to confirm baseline restoration.

## Assumptions and Defaults
1. Governance location is fixed to characterization checks (no new `--check surface` selector).
2. CLI inventory is dynamic (root plus detected subcommands), never hard-coded to "root only."
3. Exit codes are treated as observability contract behavior.
4. Owner test refs accept `path` or `path::symbol`.
5. Target is minimal change footprint with no new `src/` architecture work.
