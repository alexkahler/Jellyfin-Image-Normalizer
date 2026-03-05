Implemented end-to-end.

**Changed**
- Added runtime-gate contract keys in [project/verification-contract.yml](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/verification-contract.yml).
- Extended contract parsing/schema with runtime-gate policy in [project/scripts/governance_contract.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/governance_contract.py).
- Implemented COV-01b runtime gate (collect+run, total budget, timeout precedence, warn taxonomy, parity mapping, mapping-empty info) in [project/scripts/characterization_checks.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/characterization_checks.py).
- Added runtime-gate output reporting + governance CI install enforcement checks in [project/scripts/governance_checks.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/governance_checks.py).
- Hardened governance job dependency install in [.github/workflows/ci.yml](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/.github/workflows/ci.yml).
- Updated work-item tracking for Slice 10 in [WORK_ITEMS.md](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/WORK_ITEMS.md).
- Updated existing governance/characterization fixtures/tests in:
  - [tests/test_characterization_checks.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_characterization_checks.py)
  - [tests/test_governance_checks.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_governance_checks.py)
  - [tests/test_governance_checks_architecture.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_governance_checks_architecture.py)
- Added new focused test modules:
  - [tests/test_characterization_runtime_gate.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_characterization_runtime_gate.py)
  - [tests/test_governance_runtime_gate.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_governance_runtime_gate.py)

**Verification run**
- `PYTHONPATH=src ./.venv/bin/python -m pytest` -> `309 passed, 3 warnings`
- `./.venv/bin/python -m ruff check .` -> pass
- `./.venv/bin/python -m ruff format --check .` -> pass
- `./.venv/bin/python -m mypy src` -> pass
- `./.venv/bin/python -m bandit -r src` -> pass
- `./.venv/bin/python -m pip_audit` -> pass (local `jfin` skipped as non-PyPI)
- `PYTHONPATH=src ./.venv/bin/python project/scripts/verify_governance.py --check characterization` -> pass, includes runtime-gate section and `OK (warn)`
- `PYTHONPATH=src ./.venv/bin/python project/scripts/verify_governance.py --check all` -> fails only on known pre-existing `src/` LOC blockers (same baseline class), while schema/ci-sync/parity/characterization pass.