# Slice-11

## 1. Objective
Implement `COV-02` ratchet phase 1 for backdrop workflow sequence governance: enforce workflow contract/linkage as blocking and surface sequence-evidence regressions as deterministic warnings.

## 2. In-scope / Out-of-scope
In-scope: new workflow coverage index for `run|backdrop`, workflow contract/linkage validation in characterization governance, deterministic `count_only_detected` warning logic, backdrop sequence evidence additions in safety baseline/characterization test, governance output line additions, and targeted governance test coverage.
Out-of-scope: warn-to-block severity flip for sequence gaps (phase 2), route flips (`v0 -> v1`), parity-ID split/readiness enforcement (`COV-03`), and schema expressiveness/runtime trace expansion (`COV-04`).

## 3. Public interfaces affected
- `project/workflow-coverage-index.json`
- `project/scripts/characterization_checks.py` (workflow coverage schema/linkage/sequence checks)
- `project/scripts/governance_checks.py` (workflow sequence reporting lines)
- `tests/characterization/baselines/safety_contract_baseline.json`
- `tests/characterization/safety_contract/test_safety_contract_pipeline.py`
- `./.venv/bin/python project/scripts/verify_governance.py --check characterization`
- `./.venv/bin/python project/scripts/verify_governance.py --check all`

## 4. Acceptance criteria
- Workflow contract/linkage checks for `run|backdrop` are blocking and pass when artifacts are valid.
- Sequence regressions are always surfaced through deterministic `workflow_coverage.sequence_gap.*` warnings.
- Count-only evidence for `PIPE-BACKDROP-001` is always detected and reported as `workflow_coverage.sequence_gap.count_only_detected`.
- Backdrop sequence invariants are represented in characterization evidence, including `sequence.delete_index_zero_repeated` and `delete_before_upload` ordering token checks.
- COV-02 full closure is explicitly deferred to phase 2 by flipping `severity.sequence` from `warn` to `block`.

## 5. Verification commands (<10 min)
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_safety.py tests/test_governance_checks.py`
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/characterization/safety_contract/test_safety_contract_pipeline.py -k backdrop`
- `PYTHONPATH=src ./.venv/bin/python project/scripts/verify_governance.py --check characterization`
- `PYTHONPATH=src ./.venv/bin/python project/scripts/verify_governance.py --check all` (expect only known pre-existing LOC blockers)

## 6. Rollback step
Revert Slice 11 commits in reverse order: docs/work-item updates, governance output/test updates, baseline/characterization evidence updates, workflow coverage check logic, and `project/workflow-coverage-index.json` introduction.

## 7. Behavior-preservation statement
Preserved by default. Slice 11 adds governance and characterization contract coverage for backdrop sequence evidence without intended runtime behavior changes in `src/jfin`.