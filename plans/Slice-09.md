# Slice-09

## 1. Objective
Implement `COV-01a` characterization collectability hardening: deterministic message capture + linkage/collectability governance for parity-owned characterization rows.

## 2. In-scope / Out-of-scope
In-scope: characterization harness capture hardening, collectability checks in governance characterization flow, deterministic collectability status output, targeted safety/CLI characterization test updates, and slice docs updates.
Out-of-scope: route flips, runtime characterization execution gate (COV-01b), and runtime CLI/API behavior changes.

## 3. Public interfaces affected
- `./.venv/bin/python project/scripts/verify_governance.py --check characterization` (now includes collectability gate and explicit collectability status lines)
- `./.venv/bin/python project/scripts/verify_governance.py --check all` (inherits characterization collectability gate)
- Characterization baseline token expectation for `CLI-OVERRIDE-001` in `tests/characterization/baselines/cli_contract_baseline.json`

## 4. Acceptance criteria
- The previously failing 9 characterization tests are green (or targeted rebaseline is explicitly documented).
- Characterization governance fails deterministically when an `owner_test` is non-collectable under `pytest --collect-only`.
- Governance output includes explicit `collectability/linkage OK` signal on pass.
- No `project/verification-contract.yml` schema expansion is introduced in Slice 9.

## 5. Verification commands (<10 min)
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/characterization/cli_contract/test_cli_contract_characterization.py tests/characterization/safety_contract/test_safety_contract_api.py tests/characterization/safety_contract/test_safety_contract_restore.py tests/characterization/test_harness.py`
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_safety.py tests/test_characterization_checks_links.py tests/test_characterization_checks_imaging.py tests/test_governance_checks.py`
- `./.venv/bin/python project/scripts/verify_governance.py --check characterization`
- `./.venv/bin/python project/scripts/verify_governance.py --check all`

## 6. Rollback step
Revert Slice 9 commits in reverse order: docs/slice artifacts, governance output/check wiring, harness/test capture updates, and targeted baseline token update.

## 7. Behavior-preservation statement
Preserved by default. Slice 9 tightens governance/testing reliability only; no runtime behavior changes are introduced in `src/jfin`.
