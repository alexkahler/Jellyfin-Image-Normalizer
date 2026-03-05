# Slice-10

## 1. Objective
Implement `COV-01b` runtime characterization governance for `tests/characterization/safety_contract` with warn-ratchet behavior and deterministic runtime reporting.

## 2. In-scope / Out-of-scope
In-scope: runtime gate policy keys in `project/verification-contract.yml`, runtime gate execution/mapping/reporting in characterization governance checks, governance CI dependency install hardening, targeted governance/runtime tests, and slice docs/work-item updates.
Out-of-scope: route flips (`v0 -> v1`), runtime feature changes in `src/jfin`, and block-mode ratchet promotion (deferred to later slice after CI evidence).

## 3. Public interfaces affected
- `project/verification-contract.yml` (`characterization_runtime_gate_targets`, `characterization_runtime_gate_budget_seconds`)
- `./.venv/bin/python project/scripts/verify_governance.py --check characterization` (runtime gate status/counters)
- `./.venv/bin/python project/scripts/verify_governance.py --check all` (inherits runtime gate signal)
- `.github/workflows/ci.yml` governance job (dependency install before governance checks)

## 4. Acceptance criteria
- Runtime gate runs on every characterization governance run against `tests/characterization/safety_contract`.
- Runtime gate emits deterministic warn-taxonomy signals for:
  - `runtime_gate.target_invalid`
  - `runtime_gate.execution_failed`
  - `runtime_gate.timeout`
  - `runtime_gate.budget_exceeded`
- `runtime_gate.parity_mapping_empty` is surfaced as informational output (not warning/error).
- Governance output includes explicit runtime section and status line: `Characterization runtime gate OK|NOT OK (warn)`.
- Warn-only runtime outcomes do not force nonzero exit code by themselves.
- Governance CI job installs dependencies (including pytest availability) before `verify_governance.py --check all`.

## 5. Verification commands (<10 min)
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_characterization_runtime_gate.py tests/test_governance_runtime_gate.py`
- `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_governance_checks.py tests/test_governance_checks_architecture.py tests/test_characterization_checks.py tests/test_characterization_checks_safety.py tests/test_characterization_checks_links.py tests/test_characterization_checks_imaging.py`
- `./.venv/bin/python project/scripts/verify_governance.py --check characterization`
- `./.venv/bin/python project/scripts/verify_governance.py --check all`

## 6. Rollback step
Revert Slice 10 commits in reverse order: docs/work-item updates, test additions, CI governance install hardening, governance output changes, runtime gate logic, and verification-contract schema extensions.

## 7. Behavior-preservation statement
Preserved by default. Slice 10 adds governance/runtime gate enforcement and CI reliability hardening only, with no intended runtime behavior change in `src/jfin`.
