## WI-002 Slice Plan: Parity Matrix Skeleton + Behavior Inventory

### Summary
Implement Slice 2 by introducing a concrete parity artifact layer with executable validation, while keeping runtime behavior unchanged in `src/jfin`.

This slice will deliver:
1. `project/parity-matrix.md` with a schema-compliant starter inventory (hybrid core set).
2. `project/route-fence.md` as a separate strangler route-fence artifact.
3. Automated parity validation wired into governance `--check all` (your chosen direction).
4. Unit tests that enforce parity-row schema and route-fence integrity.

### Repo Map Snippet (for this slice)
- Runtime entry points: `src/jfin/__main__.py`, `src/jfin/cli.py`
- Existing governance checks: `project/scripts/governance_contract.py`, `project/scripts/governance_checks.py`, `project/scripts/verify_governance.py`
- Existing governance tests: `tests/test_governance_checks.py`
- Slice 2 artifacts to add: `project/parity-matrix.md`, `project/route-fence.md`
- Slice 2 validator code/tests to add: `project/scripts/parity_contract.py`, `project/scripts/parity_checks.py`, `tests/test_parity_checks.py`

---

## Scope

### In scope
1. Create parity matrix skeleton and behavior IDs (hybrid core set).
2. Create separate route-fence file (not embedded in parity matrix).
3. Add parity schema validation and route-fence validation to governance checks.
4. Add unit tests for parity validation logic.
5. Keep governance/CI behavior drift-safe by running parity checks through existing `verify_governance.py --check all`.

### Out of scope
1. Any refactor or behavior change in `src/jfin/*`.
2. CLI/config characterization harness implementation (Slice 3).
3. Imaging golden harness (Slice 4).
4. Route flips (`v0` to `v1`) or parity status promotion beyond initial baseline.

---

## Public Interfaces / Contract Additions
1. New artifact interface: `project/parity-matrix.md`
2. New artifact interface: `project/route-fence.md`
3. Governance CLI extension: `python project/scripts/verify_governance.py --check parity`
4. Governance `--check all` now includes parity validation (schema + route fence)

No user runtime API changes.

---

## Canonical Artifact Specs (decision-complete)

### 1) `project/parity-matrix.md` format
Use one Markdown table with these exact columns (order fixed):
1. `behavior_id`
2. `baseline_source`
3. `current_result`
4. `status`
5. `owner_test`
6. `approval_ref`
7. `notes`
8. `migration_note`

Rules:
1. Required schema fields from blueprint must exist in every row: `behavior_id`, `baseline_source`, `current_result`, `status`, `owner_test`, `approval_ref`.
2. Allowed `status`: `preserved`, `changed`, `removed`, `suspicious`.
3. `approval_ref` rule:
- Required and non-placeholder if `status` is `changed` or `removed`.
- Required and non-placeholder if `status` is `suspicious` due intentional divergence.
- Allowed value `n/a` for `preserved`.
4. `behavior_id` must be unique.
5. Initial `current_result` value for all WI-002 starter rows: `matches-baseline`.
6. Initial `status` for all WI-002 starter rows: `preserved`.

### 2) `project/route-fence.md` format
Use one Markdown table with these exact columns (order fixed):
1. `command`
2. `mode`
3. `route(v0|v1)`
4. `owner slice`
5. `parity status`

Initial rows (exactly 8, matching blueprint):
1. `run | logo | v0 | WI-00X | pending`
2. `run | thumb | v0 | WI-00X | pending`
3. `run | backdrop | v0 | WI-00X | pending`
4. `run | profile | v0 | WI-00X | pending`
5. `restore | logo|thumb|backdrop|profile | v0 | WI-00X | pending`
6. `test_connection | n/a | v0 | WI-00X | pending`
7. `config_init | n/a | v0 | WI-00X | pending`
8. `config_validate | n/a | v0 | WI-00X | pending`

Rules:
1. `route(v0|v1)` must be either `v0` or `v1`.
2. Row key (`command`,`mode`) must be unique.
3. Required command/mode combinations above must all be present.

---

## Initial Behavior ID Inventory (hybrid core set)

Seed these rows in `project/parity-matrix.md` (status `preserved`, `current_result` `matches-baseline`, `approval_ref` `n/a`):

1. `CLI-RESTORE-001` -> `tests/test_jfin.py::test_validate_restore_all_args_blocks_operational_flags`
2. `CLI-GENCFG-001` -> `tests/test_jfin.py::test_validate_generate_config_args_blocks_operational_flags`
3. `CLI-TESTJF-001` -> `tests/test_jfin.py::test_validate_test_jf_args_blocks_operational_flags`
4. `CLI-SINGLE-001` -> `tests/test_jfin.py::test_single_requires_explicit_mode`
5. `CLI-OVERRIDE-001` -> `tests/test_jfin.py::test_warn_unused_cli_overrides_incompatible_flags`
6. `CLI-ASPECT-001` -> `tests/test_jfin.py::test_warn_unrecommended_aspect_ratios_warns_on_mismatch`

7. `CFG-TOML-001` -> `tests/test_config.py::test_load_config_from_path_rejects_non_toml`
8. `CFG-TOML-002` -> `tests/test_config.py::test_load_config_from_path_parses_toml_and_builds_mode`
9. `CFG-TYPE-001` -> `tests/test_config.py::test_validate_config_types_rejects_invalid_types`
10. `CFG-CORE-001` -> `tests/test_config.py::test_validate_config_types_requires_core_fields`
11. `CFG-OPS-001` -> `tests/test_config.py::test_parse_operations_dedupes_and_orders`
12. `CFG-DISC-001` -> `tests/test_config.py::test_build_discovery_settings_maps_modes_and_filters`
13. `CFG-OVERRIDE-001` -> `tests/test_config.py::test_apply_cli_overrides_applies_target_size_per_mode`

14. `API-QUERY-001` -> `tests/test_client.py::test_query_items_builds_expected_params`
15. `API-WRITE-001` -> `tests/test_client.py::test_post_image_base64_payload`
16. `API-DRYRUN-001` -> `tests/test_client.py::test_dry_run_blocks_post`
17. `API-DELETE-001` -> `tests/test_client.py::test_delete_image_parametrized`
18. `API-GETIMG-001` -> `tests/test_client.py::test_get_item_image_returns_content_type`
19. `API-RETRY-001` -> `tests/test_client.py::test_get_retries_on_failure`

20. `DISC-LIB-001` -> `tests/test_discovery.py::test_discover_libraries_filters_names`
21. `DISC-LIB-002` -> `tests/test_discovery.py::test_discover_libraries_skips_unsupported_collection_types`
22. `DISC-ITEM-001` -> `tests/test_discovery.py::test_discover_library_items_paginates`
23. `DISC-ITEM-002` -> `tests/test_discovery.py::test_discover_library_items_maps_image_types`

24. `IMG-SCALE-001` -> `tests/test_imaging.py::test_make_scale_plan_upscale`
25. `IMG-NOSCALE-001` -> `tests/test_imaging.py::test_handle_no_scale_dry_run_skips_upload`
26. `IMG-LOGO-001` -> `tests/test_imaging.py::test_remove_padding_from_logo_crops_transparent_border`
27. `IMG-CROP-001` -> `tests/test_imaging.py::test_cover_and_crop_respects_target_size`
28. `IMG-ENCODE-001` -> `tests/test_imaging.py::test_encode_image_to_bytes_roundtrip`

29. `PIPE-DRYRUN-001` -> `tests/test_pipeline.py::test_normalize_item_image_api_dry_run_skips_upload`
30. `PIPE-BACKUP-001` -> `tests/test_pipeline.py::test_partial_backup_skips_no_scale`
31. `PIPE-BACKDROP-001` -> `tests/test_pipeline.py::test_normalize_item_backdrops_api_scenarios`
32. `PIPE-SINGLE-001` -> `tests/test_pipeline.py::test_process_single_item_uses_direct_item_id`
33. `PIPE-COUNT-001` -> `tests/test_pipeline.py::test_single_item_counted_once_across_multiple_modes`

34. `BKP-MODE-001` -> `tests/test_backup.py::test_should_backup_for_plan_modes`
35. `BKP-PATH-001` -> `tests/test_backup.py::test_backup_path_for_image`
36. `RST-BULK-001` -> `tests/test_backup.py::test_restore_from_backups_scenarios`
37. `RST-SINGLE-001` -> `tests/test_backup.py::test_restore_single_from_backup_scenarios`

---

## Staged Implementation Plan

### Milestone 1: Add Slice-2 artifacts
Files:
1. `project/parity-matrix.md`
2. `project/route-fence.md`
3. `plans/WI-002.md` (from template, filled for this slice)

Intent:
1. Materialize parity + route artifacts with fixed schemas and starter data.
2. Keep this milestone docs/artifact-only.

Verification:
1. `rg -n "behavior_id|baseline_source|current_result|status|owner_test|approval_ref" project/parity-matrix.md`
2. `rg -n "CLI-RESTORE-001|CFG-TOML-001|API-DRYRUN-001|PIPE-BACKDROP-001|RST-SINGLE-001" project/parity-matrix.md`
3. `rg -n "command|route\\(v0\\|v1\\)|owner slice|parity status|config_validate" project/route-fence.md`

Exit criteria:
1. Parity matrix exists with 37 starter IDs.
2. Route fence exists with 8 required rows.

### Milestone 2: Add parity validation modules
Files:
1. `project/scripts/parity_contract.py`
2. `project/scripts/parity_checks.py`

Intent:
1. Parse markdown tables deterministically (stdlib only).
2. Validate parity row schema and route-fence schema.
3. Expose one callable check result compatible with existing governance check model.

Implementation constraints:
1. Keep each Python file <300 LOC.
2. No new third-party deps.
3. Deterministic, explicit error messages naming row and field.

Verification:
1. `python -c "from project.scripts import parity_contract, parity_checks; print('ok')"` or equivalent import test in repo style.
2. `python project/scripts/verify_governance.py --check parity` (after Milestone 3 wiring).

Exit criteria:
1. Validator code exists and can parse both markdown artifacts.
2. All required rules from this plan are encoded.

### Milestone 3: Wire parity into governance check runner
Files:
1. `project/scripts/governance_checks.py`
2. `project/scripts/verify_governance.py` (only if dispatch adjustment needed)

Intent:
1. Add `parity` to supported checks.
2. Ensure `--check all` includes parity after existing checks.

Verification:
1. `python project/scripts/verify_governance.py --check parity`
2. `python project/scripts/verify_governance.py --check schema`
3. `python project/scripts/verify_governance.py --check ci-sync`
4. `python project/scripts/verify_governance.py --check python-version`

Exit criteria:
1. `--check parity` passes with clean artifact data.
2. `--check all` reports parity pass and still reports expected LOC baseline failure.

### Milestone 4: Add parity validator unit tests
Files:
1. `tests/test_parity_checks.py`

Intent:
1. Test parity schema and route-fence validation comprehensively without inflating `tests/test_governance_checks.py` past 300 LOC.

Required test scenarios:
1. Valid parity matrix + route fence passes.
2. Missing required parity column fails.
3. Invalid `status` fails.
4. `changed/removed` row with placeholder `approval_ref` fails.
5. Duplicate `behavior_id` fails.
6. Missing required starter behavior ID fails.
7. Missing required route-fence row fails.
8. Invalid route value (not `v0|v1`) fails.

Verification:
1. `PYTHONPATH=src python -m pytest -q tests/test_parity_checks.py`
2. `PYTHONPATH=src python -m pytest -q tests/test_governance_checks.py`

Exit criteria:
1. New parity tests pass.
2. Existing governance tests remain green.

### Milestone 5: Docs and WI alignment
Files:
1. `WORK_ITEMS.md` (only if status annotation convention is introduced)
2. `README.md` and/or `docs/TECHNICAL_NOTES.md` (developer governance section)
3. `plans/WI-002.md`

Intent:
1. Document where parity artifacts live and how parity check is run.

Verification:
1. `rg -n "parity-matrix|route-fence|--check parity" README.md docs/TECHNICAL_NOTES.md plans/WI-002.md`

Exit criteria:
1. Human operator can locate parity artifacts and run parity checks from docs.

---

## Test Cases and Acceptance Scenarios (Slice 2)
1. Parity row schema exists and is enforced.
2. Parity matrix starter behavior IDs exist and are unique.
3. Route-fence artifact exists separately and contains required 8 command/mode rows.
4. Governance supports and executes `--check parity`.
5. `--check all` includes parity validation.
6. No runtime behavior changes in `src/jfin`.

---

## Risk Register (Top 5)
1. Risk: Overly granular IDs create maintenance drag.
- Mitigation: Hybrid core set (37 IDs) now, expansion deferred to Slices 3-5.
2. Risk: Markdown parser brittleness causes false failures.
- Mitigation: Strict but narrow table grammar + dedicated unit tests for malformed cases.
3. Risk: Governance checker file-size creep.
- Mitigation: Keep parity logic in separate modules; minimal edits to `governance_checks.py`.
4. Risk: CI remains red due strict LOC baseline.
- Mitigation: Expected Track-1 condition; parity work proceeds independently.
5. Risk: Drift between route fence and parity matrix.
- Mitigation: Separate artifacts but validated together in parity check.

---

## Rollback Plan
1. Commit A: artifact files (`parity-matrix.md`, `route-fence.md`, `plans/WI-002.md`).
2. Commit B: parity validator modules + governance wiring.
3. Commit C: parity tests + docs updates.
4. If issues occur:
- Revert C first (tests/docs).
- Revert B second (logic/wiring).
- Revert A last (artifacts).
5. Use `git revert` only; no destructive reset operations.

---

## Assumptions and Defaults
1. Slice objective remains strictly WI-002.
2. Route-fence remains a separate file: `project/route-fence.md` (your choice).
3. Parity validation is enforced immediately via governance checks (your choice).
4. Initial behavior inventory uses hybrid core granularity (your choice).
5. No change to runtime behavior in `src/jfin`.
6. Full local gates may still fail in Python 3.10 and on strict LOC baseline; Slice-2 targeted checks remain the primary acceptance gate.
