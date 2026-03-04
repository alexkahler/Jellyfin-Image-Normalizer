# WI-004 Slice 3 Plan (Revised): CLI/Config Characterization Harness

## Summary
Implement slice 3 as `WI-004` (per `WORK_ITEMS.md`) with additive CLI/config characterization coverage, baseline artifacts, and a blocking governance check, while keeping `src/jfin` runtime behavior unchanged.

## Gap Closures Applied
1. Baseline schema is expanded beyond exit/counters to include optional `expected_messages`, `expected_effective_config`, and `expected_preflight`.
2. Route-fence rows will **not** be marked `characterized` unless explicitly covered by new behavior IDs/tests/baselines in this slice.
3. CLI invocation approach is fixed: characterization tests invoke `jfin.cli.main()` in-process through real argparse paths (`sys.argv`), with explicit monkeypatching of network/client boundaries.
4. New `characterization` governance check is scoped to baseline linkage and ownership integrity; full parity schema validation remains in existing `parity` check.
5. `expected_stats` normalization is defined as subset-based and optional; message tokens become the primary stable assertion surface.

## Public Interfaces / Contract Additions
1. New artifacts:
- `tests/characterization/baselines/cli_contract_baseline.json`
- `tests/characterization/baselines/config_contract_baseline.json`
2. New test suites:
- `tests/characterization/cli_contract/test_cli_contract_characterization.py`
- `tests/characterization/config_contract/test_config_contract_characterization.py`
3. New governance check:
- `python project/scripts/verify_governance.py --check characterization`
4. Governance `--check all` includes `characterization` after `parity`.
5. `project/parity-matrix.md` updates for only `CLI-*` and `CFG-*` rows to characterization owners/baseline links.

## Baseline Schema (Decision Complete)
1. Root keys:
- `version` (int, fixed `1`)
- `cases` (object keyed by `behavior_id`)
2. Per-case required key:
- `expected_exit_code` (int)
3. Per-case optional keys:
- `expected_stats` (object subset of `errors`, `warnings`, `successes`; only asserted for provided keys)
- `expected_messages` (list of substring tokens, matched against normalized logs/errors)
- `expected_effective_config` (small dict for CFG expectations, e.g. resolved operations/item types/target sizes)
- `expected_preflight` (`not_reached | mocked_ok | mocked_fail`)
- `notes` (string)

## Canonical Invocation and Test Harness Rules
1. All CLI characterization tests call `jfin.cli.main()` with monkeypatched `sys.argv`, not subprocess.
2. Network boundaries are always mocked by patching client factory/preflight-dependent methods.
3. Preflight expectation is asserted via explicit mock call tracking and `expected_preflight`.
4. Harness resets global state before each case and normalizes captured messages for stable token assertions.
5. Subprocess is optional only for a lightweight `python -m jfin --help` smoke check, not for core characterization.

## Scope
1. In scope:
- Characterization harness and tests for all `CLI-*` and `CFG-*` parity IDs.
- Baseline artifacts and parity linkage updates.
- New governance characterization check and its unit tests.
- Docs and `plans/WI-004.md` alignment.
2. Out of scope:
- Runtime/refactor changes in `src/jfin/*`.
- Imaging goldens (`WI-003` in your execution order).
- Route flips (`v0` to `v1`).
- Marking non-covered route-fence rows as characterized.

## Milestones

### Milestone 1: WI-004 planning + baseline artifacts
1. Files:
- `plans/WI-004.md`
- `tests/characterization/baselines/cli_contract_baseline.json`
- `tests/characterization/baselines/config_contract_baseline.json`
2. Intent:
- Materialize schema-complete baselines for 13 IDs (`CLI-*` + `CFG-*`).
3. Verification:
- `rg -n "CLI-RESTORE-001|CLI-ASPECT-001|CFG-TOML-001|CFG-OVERRIDE-001" tests/characterization/baselines/*.json`
- `rg -n "expected_messages|expected_effective_config|expected_preflight" tests/characterization/baselines/*.json`
- `rg -n "Objective|In-scope|Out-of-scope|Acceptance criteria|Verification commands|Rollback step|Behavior-preservation statement" plans/WI-004.md`
4. Exit criteria:
- Both baseline files exist with all required IDs and schema fields.

### Milestone 2: Shared characterization harness
1. Files:
- `tests/characterization/_harness.py`
2. Intent:
- Provide deterministic runner utilities for CLI/config cases.
3. Implementation constraints:
- No third-party dependencies.
- File remains <300 LOC.
4. Verification:
- `PYTHONPATH=src python -m pytest -q tests/characterization -k harness`
5. Exit criteria:
- Harness supports argv execution, mock preflight modes, message capture, and subset stat assertions.

### Milestone 3: CLI characterization tests
1. Files:
- `tests/characterization/cli_contract/test_cli_contract_characterization.py`
2. Coverage:
- `CLI-RESTORE-001`, `CLI-GENCFG-001`, `CLI-TESTJF-001`, `CLI-SINGLE-001`, `CLI-OVERRIDE-001`, `CLI-ASPECT-001`
3. Verification:
- `PYTHONPATH=src python -m pytest -q tests/characterization/cli_contract/test_cli_contract_characterization.py`
4. Exit criteria:
- All 6 CLI IDs are baseline-backed and passing.

### Milestone 4: Config characterization tests
1. Files:
- `tests/characterization/config_contract/test_config_contract_characterization.py`
2. Coverage:
- `CFG-TOML-001`, `CFG-TOML-002`, `CFG-TYPE-001`, `CFG-CORE-001`, `CFG-OPS-001`, `CFG-DISC-001`, `CFG-OVERRIDE-001`
3. Verification:
- `PYTHONPATH=src python -m pytest -q tests/characterization/config_contract/test_config_contract_characterization.py`
4. Exit criteria:
- All 7 CFG IDs are baseline-backed and passing.

### Milestone 5: Parity updates (no route-fence overclaim)
1. Files:
- `project/parity-matrix.md`
2. Intent:
- Update only `CLI-*` and `CFG-*` rows:
- `baseline_source` -> baseline JSON anchors
- `owner_test` -> characterization node IDs
- keep `status=preserved`, `current_result=matches-baseline`, `approval_ref=n/a`
3. Route-fence handling:
- Keep current rows `pending` unless new explicit route-fence characterization IDs are added in this slice.
4. Verification:
- `rg -n "CLI-|CFG-|tests/characterization/baselines" project/parity-matrix.md`
- `python project/scripts/verify_governance.py --check parity`
5. Exit criteria:
- Parity ownership aligns to characterization tests with no misleading route-fence status upgrades.

### Milestone 6: Governance characterization check wiring
1. Files:
- `project/scripts/characterization_contract.py`
- `project/scripts/characterization_checks.py`
- `project/scripts/governance_checks.py`
- `project/scripts/verify_governance.py` (dispatch only if needed)
2. Check scope:
- Baseline JSON schema and required IDs exist.
- For required `CLI-*`/`CFG-*` parity rows, `owner_test` and `baseline_source` resolve.
- `owner_test` paths/functions exist.
- `baseline_source` anchor key exists in referenced JSON.
- Do not duplicate full parity schema/route schema checks already handled by `parity`.
3. Verification:
- `python project/scripts/verify_governance.py --check characterization`
- `python project/scripts/verify_governance.py --check all`
4. Exit criteria:
- `characterization` is blocking and `--check all` includes it.

### Milestone 7: Unit tests for characterization checker + docs
1. Files:
- `tests/test_characterization_checks.py`
- `tests/test_governance_checks.py` (only dispatch assertion if required)
- `README.md`
- `docs/TECHNICAL_NOTES.md`
2. Required test scenarios:
- valid pass
- missing baseline file
- missing required ID
- bad/missing baseline anchor in parity row
- missing owner test file/function
- owner test outside `tests/characterization/`
3. Verification:
- `PYTHONPATH=src python -m pytest -q tests/test_characterization_checks.py`
- `PYTHONPATH=src python -m pytest -q tests/test_governance_checks.py`
- `rg -n "check characterization|tests/characterization|parity-matrix" README.md docs/TECHNICAL_NOTES.md`
4. Exit criteria:
- Checker tests pass and docs reflect local workflow.

## Acceptance Criteria
1. All 13 `CLI-*`/`CFG-*` parity IDs are backed by characterization tests and baseline entries.
2. `project/parity-matrix.md` links for these IDs resolve to real test nodes and baseline anchors.
3. `verify_governance.py --check characterization` fails on linkage/schema drift and passes on valid state.
4. Existing `parity` check remains the sole full parity/route schema validator.
5. No runtime behavior changes in `src/jfin`.

## Verification Commands (<10 min target)
1. `PYTHONPATH=src python -m pytest -q tests/characterization/cli_contract/test_cli_contract_characterization.py`
2. `PYTHONPATH=src python -m pytest -q tests/characterization/config_contract/test_config_contract_characterization.py`
3. `PYTHONPATH=src python -m pytest -q tests/test_characterization_checks.py`
4. `python project/scripts/verify_governance.py --check characterization`
5. `python project/scripts/verify_governance.py --check parity`
6. `python project/scripts/verify_governance.py --check all` (expected to still fail on strict `src` LOC baseline until later slices)

## Risk Register (Top 5)
1. Baseline drift from log wording changes.
Mitigation: token-based `expected_messages` with stable substrings, not exact full-line snapshots.
2. False instability from global counters.
Mitigation: optional subset `expected_stats`; do not require full counter equality unless case-local deterministic.
3. Overlap between parity and characterization checks.
Mitigation: strict checker boundary; no duplicate parity schema enforcement.
4. Misleading route-fence parity status.
Mitigation: no `characterized` status unless row has explicit WI-004 coverage artifacts.
5. Python 3.10 local mismatch (`tomllib`) obscures results.
Mitigation: slice acceptance is Python 3.13 in CI; local constraints documented.

## Rollback Plan
1. Commit A: WI-004 plan + baseline artifacts.
2. Commit B: harness + characterization tests.
3. Commit C: parity row updates + characterization governance scripts/wiring.
4. Commit D: checker tests + docs updates.
5. Revert in reverse order with `git revert` only.

## Assumptions and Defaults
1. Slice mapping uses `WORK_ITEMS.md`: slice 3 is `WI-004`.
2. Governance remains strict and blocking for new characterization check.
3. Existing `tests/test_jfin.py` and `tests/test_config.py` remain as-is; characterization is additive.
4. Route-fence ownership/status changes are deferred unless explicit coverage is added for those rows.
5. Runtime code changes are forbidden in this slice.
