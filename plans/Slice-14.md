# Slice-14

## 1. Objective
Implement `COV-05` by correcting blueprint characterization-suite topology in `project/v1-plan.md` and adding a minimal blocking docs-topology governance contract under `--check characterization`.

## 2. In-scope / Out-of-scope
In-scope: canonical suite-list correction in `project/v1-plan.md`, governance docs-topology contract check in `project/scripts/governance_checks.py`, bounded/format-tolerant topology extraction for `project/v1-plan.md` and `docs/TECHNICAL_NOTES.md`, required suite/baseline directory existence checks, and targeted governance tests.
Out-of-scope: README topology enforcement, route flips (`v0 -> v1`), and any changes to COV-01b runtime gate, COV-02 workflow coverage, COV-03 readiness semantics, COV-04 trace contract behavior, or runtime code in `src/jfin`.

## 3. Public interfaces affected
- `project/scripts/governance_checks.py` (`check_docs_topology_contract(repo_root)` + characterization-check aggregation wiring)
- `./.venv/bin/python project/scripts/verify_governance.py --check characterization` (new blocking docs-topology failure mode)
- `project/v1-plan.md` (`### Characterization suites` canonical path set)

## 4. Acceptance criteria
- Governance fails with `docs_topology.contract:` when `project/v1-plan.md` suite topology differs from canonical set.
- Governance fails with `docs_topology.contract:` when `docs/TECHNICAL_NOTES.md` suite topology differs from canonical set.
- Governance fails with `docs_topology.contract:` when any canonical suite directory or `tests/characterization/baselines/` is missing.
- Formatting-only differences (path order, punctuation/backticks, slash style) do not fail the docs-topology check.

## 5. Verification commands (<10 min)
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_governance_docs_topology.py tests/test_governance_checks.py`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` (expect only pre-existing LOC blockers/warnings)
- Full contract checks:
  - `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest`
  - `.\.venv\Scripts\python.exe -m ruff check .`
  - `.\.venv\Scripts\python.exe -m ruff format --check .` (known pre-existing formatting drift in `tests/test_characterization_checks_safety.py`)
  - `.\.venv\Scripts\python.exe -m mypy src`
  - `.\.venv\Scripts\python.exe -m bandit -r src`
  - `.\.venv\Scripts\python.exe -m pip_audit`

## 6. Rollback step
Revert Slice 14 commits in reverse order: slice tracking/doc updates, docs-topology governance tests, docs-topology governance check/wiring, and `project/v1-plan.md` suite-topology correction.

## 7. Behavior-preservation statement
Preserved by default. Slice 14 introduces governance/docs anti-drift enforcement only and does not change runtime behavior in `src/jfin`.
