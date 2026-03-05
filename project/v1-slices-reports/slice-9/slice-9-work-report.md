Implemented end-to-end.

Applied skills: `verification-gates-and-diff-discipline`, `loc-and-complexity-discipline`.

## What changed
- Added deterministic characterization message capture utilities and merge policy:
  - `tests/characterization/_harness.py`
  - `tests/characterization/safety_contract/_harness.py`
- Updated safety characterization tests to use scoped logger capture lifecycle:
  - `tests/characterization/safety_contract/test_safety_contract_api.py`
  - `tests/characterization/safety_contract/test_safety_contract_restore.py`
- Extended characterization governance with parity-owner collectability checks and deterministic error taxonomy:
  - `project/scripts/characterization_checks.py`
- Extended governance output with explicit collectability counters/status:
  - `project/scripts/governance_checks.py`
- Added governance/collectability and harness precision tests:
  - `tests/test_characterization_checks.py`
  - `tests/test_governance_checks.py`
  - `tests/characterization/test_harness.py`
- Updated slice/governance docs:
  - `plans/Slice-09.md`
  - `WORK_ITEMS.md`
  - `README.md`
  - `docs/TECHNICAL_NOTES.md`
  - `project/v1-slices-reports/slice-9/slice-9-plan.md`

## Normalization policy implemented
- Normalize captured messages by:
  - stripping ANSI escapes,
  - trimming outer whitespace,
  - deduplicating exact duplicate lines.
- Do not normalize semantic content or token meaning.
- Added a negative-control harness test to ensure near-match message text still fails expected-token assertions.

## Targeted rebaseline summary
- Baseline file updated: `tests/characterization/baselines/cli_contract_baseline.json`
- Case: `CLI-OVERRIDE-001`
- Token diff:
  - before: `--thumb-jpeg-quality has no effect without 'thumb' mode selected.`
  - after: `--thumb-jpeg-quality has no effect because 'thumb' mode is not selected.`
- Rationale: align baseline token with current runtime warning phrasing while preserving semantic intent.

## Verification run
Targeted checks:
1. `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/characterization/test_harness.py tests/characterization/safety_contract/test_safety_contract_api.py tests/characterization/safety_contract/test_safety_contract_restore.py tests/characterization/cli_contract/test_cli_contract_characterization.py`
   - `22 passed`
2. `PYTHONPATH=src ./.venv/bin/python -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_safety.py tests/test_characterization_checks_links.py tests/test_characterization_checks_imaging.py tests/test_governance_checks.py`
   - `32 passed`

Full/contract checks:
1. `PYTHONPATH=src ./.venv/bin/python -m pytest`
   - `296 passed, 3 warnings`
2. `./.venv/bin/python -m ruff check .`
   - pass
3. `./.venv/bin/python -m ruff format --check .`
   - pass
4. `./.venv/bin/python -m mypy src`
   - pass
5. `./.venv/bin/python -m bandit -r src`
   - pass
6. `./.venv/bin/python -m pip_audit`
   - pass (local `jfin` package skipped as non-PyPI)
7. `./.venv/bin/python project/scripts/verify_governance.py --check characterization`
   - pass, includes `collectability/linkage OK`
8. `./.venv/bin/python project/scripts/verify_governance.py --check all`
   - fails only on known pre-existing `src/jfin/*` LOC blockers; no new blocking governance failures introduced by Slice 9
