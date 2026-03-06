Implemented Slice 11 (COV-02 warn phase) as requested.

- Added workflow coverage contract index with machine-checkable debt closure and explicit evidence/token layout.
- Implemented workflow coverage validation + taxonomy in characterization checks:
  - contract/linkage findings (`workflow_coverage.contract_*`) as blocking
  - sequence findings (`workflow_coverage.sequence_gap.*`) as warnings
  - deterministic count-only rule (`0 / required_fields` satisfied), including empty-container and counts-only cases
  - route-fence cell existence check and owner-nodeid collectability check
- Updated governance reporting to print separate lines for:
  - `Workflow sequence contract OK|NOT OK`
  - `Workflow sequence evidence warnings: <N>`
- Updated backdrop baseline/test evidence with all required sequence keys, including `sequence.delete_index_zero_repeated`, and `delete_before_upload` ordering token.
- Added/updated tests for missing/invalid workflow index, unknown cell, unresolved owner nodeid, count-only detection (both variants), missing required sequence field, and full-evidence no-warning case.

Changed files:
- [project/workflow-coverage-index.json](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/workflow-coverage-index.json)
- [project/scripts/characterization_checks.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_checks.py)
- [project/scripts/governance_checks.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/governance_checks.py)
- [tests/characterization/baselines/safety_contract_baseline.json](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/baselines/safety_contract_baseline.json)
- [tests/characterization/safety_contract/test_safety_contract_pipeline.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/safety_contract/test_safety_contract_pipeline.py)
- [tests/_characterization_test_helpers.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/_characterization_test_helpers.py)
- [tests/test_characterization_checks.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks.py)
- [tests/test_characterization_checks_safety.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_safety.py)
- [tests/test_governance_checks.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_governance_checks.py)

Validation run:
- `pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_safety.py tests/test_governance_checks.py` -> `29 passed`
- `pytest -q tests/characterization/safety_contract/test_safety_contract_pipeline.py -k backdrop` -> `1 passed, 1 deselected`
- `verify_governance.py --check characterization` -> `PASS` (workflow contract OK, warnings 0, count-only 0)
- `verify_governance.py --check all` -> fails on pre-existing `src/` LOC blockers and test LOC warnings; Slice 11 introduces a new test LOC warning for `tests/test_characterization_checks_safety.py` (>300 lines). This remediation documents that warning and does not remove it.
- `ruff check .` and `ruff format --check .` -> pass

## Post-Audit

Implemented the remediation plan for AUD-002/003/004.

### Changes made
- Added deterministic end-to-end negative-path coverage in [test_characterization_checks_safety.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_safety.py):
  - `workflow_coverage.contract_invalid_json` (malformed `project/workflow-coverage-index.json`)
  - `workflow_coverage.contract_schema` (invalid schema shape: non-object `cells`)
  - `workflow_coverage.contract_owner_nodeid_uncollectable` (valid symbol + mocked non-empty collect-only set missing required nodeid)
  - `workflow_coverage.sequence_gap.missing_ordering_tokens` for:
    - ordering list present but empty
    - ordering container missing
  - Kept/clarified distinct owner symbol-missing path test.

- Updated Slice 11 reporting narrative in [slice-11-work-report.md](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/v1-slices-reports/slice-11/slice-11-work-report.md) to explicitly state:
  - Slice 11 introduced the `tests/test_characterization_checks_safety.py` LOC warning (>300).
  - This remediation documents it and does not remove it.
  - `--check all` hard-fail remains pre-existing `src` LOC blockers.

- Updated work-item tracking in [WORK_ITEMS.md](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/WORK_ITEMS.md) with Slice 11 iterative entry for COV-02 warn-phase scope.

### Verification run
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_characterization_checks_safety.py tests/test_characterization_checks.py tests/test_governance_checks.py`  
  - `34 passed`
- `PYTHONPATH=src ./.venv/bin/python project/scripts/verify_governance.py --check characterization`  
  - `PASS`
- `PYTHONPATH=src ./.venv/bin/python project/scripts/verify_governance.py --check all`  
  - `FAIL` as expected on pre-existing `src` LOC blockers; test LOC warnings include `tests/test_characterization_checks_safety.py` (now `446` lines).