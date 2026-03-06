## Slice 11 Plan (Final): COV-02 Backdrop Sequence Gate, Warn Phase

### Summary
1. Implement COV-02 as ratchet phase 1: workflow contract/linkage errors are blocking; sequence-evidence regressions are warnings.
2. Keep scope to `run|backdrop`, keep `PIPE-BACKDROP-001`, and avoid runtime/schema expressiveness expansion.
3. Make three rules explicit and machine-safe now: debt closure predicate, count-only detection rule, and ordering-token storage layout.

### Contract Additions
1. Add `project/workflow-coverage-index.json` with map-keyed cells and strict schema:
```json
{
  "version": 1,
  "cells": {
    "run|backdrop": {
      "command": "run",
      "mode": "backdrop",
      "required_parity_ids": ["PIPE-BACKDROP-001"],
      "required_owner_tests": [
        "tests/characterization/safety_contract/test_safety_contract_pipeline.py::test_pipe_backdrop_001_characterization"
      ],
      "evidence_layout": {
        "field_container": "expected_observations.calls",
        "ordering_container": "expected_observations.ordering"
      },
      "required_evidence_fields": [
        "sequence.fetch_indices_dense_ordered",
        "sequence.normalize_source_index_mapping",
        "sequence.post_delete_404_verified",
        "sequence.upload_indices_dense_ordered",
        "sequence.delete_index_zero_repeated",
        "sequence.staging_retained_partial_failure"
      ],
      "required_ordering_tokens": ["delete_before_upload"],
      "severity": {
        "contract": "block",
        "sequence": "warn"
      },
      "future_split_debt": {
        "id": "DEBT-BACKDROP-ID-SPLIT-001",
        "status": "open",
        "readiness_blocking": true,
        "enforcement_phase": "COV-03",
        "closure": {
          "type": "parity_id_count_min",
          "cell": "run|backdrop",
          "min_required": 2
        }
      }
    }
  }
}
```
2. Count-only definition for checker/tests:
- `count_only_detected` when `required_evidence_fields` satisfaction is `0/len(required)` for the row.
- This includes both empty evidence container and counts-only payloads.
3. Severity schema rules:
- `severity.contract` allowed: `block|warn` (Slice 11 default = `block`).
- `severity.sequence` allowed: `warn|block` (Slice 11 default = `warn`).
- If missing, defaults to `{contract:block, sequence:warn}`.

### Implementation Changes
1. In `project/scripts/characterization_checks.py`:
- validate workflow index schema and unique cell map keys,
- validate each workflow cell exists in route-fence (`run|backdrop` must exist),
- validate `required_owner_tests` resolve deterministically (static symbol + collect-only nodeid resolution),
- validate required parity IDs link to parity matrix row and baseline source,
- read evidence fields from `expected_observations.calls` and ordering tokens from `expected_observations.ordering`,
- emit `workflow_coverage.contract_*` as errors and `workflow_coverage.sequence_gap.*` as warnings,
- emit `workflow_coverage.sequence_gap.count_only_detected` via explicit rule above.
2. In `tests/characterization/baselines/safety_contract_baseline.json` and `tests/characterization/safety_contract/test_safety_contract_pipeline.py`:
- add scalar sequence evidence keys for all required invariants, including `sequence.delete_index_zero_repeated`,
- retain `delete_before_upload` token in `expected_observations.ordering`.
3. In governance reporting (`project/scripts/governance_checks.py`):
- print separate lines:
- `Workflow sequence contract OK|NOT OK`
- `Workflow sequence evidence warnings: <N>`
- avoid single “OK (warn)” phrasing.

### Test Plan
1. Add/extend tests in `tests/test_characterization_checks_safety.py`:
- missing/invalid workflow index => error,
- unknown/non-route-fence cell => error,
- unresolved owner nodeid => error,
- count-only baseline (empty container) => `count_only_detected` warning,
- count-only baseline (counts-only keys) => `count_only_detected` warning,
- missing `sequence.delete_index_zero_repeated` => sequence warning,
- full evidence + ordering token => no sequence warnings.
2. Extend fixture builders in `tests/test_characterization_checks.py` / `tests/_characterization_test_helpers.py` for workflow index + evidence layout defaults.
3. Add output-presence assertions (not full snapshot) in `tests/test_governance_checks.py` for the two new workflow lines.
4. Run:
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_safety.py tests/test_governance_checks.py`
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/characterization/safety_contract/test_safety_contract_pipeline.py -k backdrop`
- `PYTHONPATH=src ./.venv/bin/python project/scripts/verify_governance.py --check characterization`
- `PYTHONPATH=src ./.venv/bin/python project/scripts/verify_governance.py --check all` (expect only known baseline LOC blockers).

### Acceptance and Ratchet
1. Slice 11 acceptance:
- workflow contract/linkage passes blocking checks,
- sequence regressions are always surfaced as deterministic warnings,
- count-only evidence is always detected (`count_only_detected` warning).
2. COV-02 full closure is deferred to ratchet phase 2:
- flip `severity.sequence` from `warn` to `block` for `run|backdrop`,
- then “count-only cannot pass governance” becomes fully enforced.

### Assumptions
1. COV-01a collectability/linkage is already green; if not, Slice 11 is paused or reduced to scaffolding-only.
2. Slice 11 validates baseline evidence structure only; it does not require new runtime trace semantics (COV-04 remains separate).
3. No route flips/readiness-state transitions are performed in Slice 11.
