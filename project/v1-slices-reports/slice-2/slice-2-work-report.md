Implemented WI-002 end-to-end with no changes under `src/jfin`.

**What I changed**
- Added parity artifacts:
  - [project/parity-matrix.md](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/parity-matrix.md:1)
  - [project/route-fence.md](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/route-fence.md:1)
- Added parity contract/check logic:
  - [project/scripts/parity_contract.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/parity_contract.py:1)
  - [project/scripts/parity_checks.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/parity_checks.py:1)
- Wired governance runner to support `parity`:
  - [project/scripts/governance_checks.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/governance_checks.py:19)
- Added parity unit tests (8 required scenarios):
  - [tests/test_parity_checks.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_parity_checks.py:103)
- Added WI slice doc:
  - [plans/WI-002.md](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/plans/WI-002.md:1)
- Updated docs for parity check usage:
  - [README.md](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/README.md:433)
  - [docs/TECHNICAL_NOTES.md](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/docs/TECHNICAL_NOTES.md:163)

**Verification**
- `python project/scripts/verify_governance.py --check parity` -> PASS
- `python project/scripts/verify_governance.py --check schema` -> PASS
- `python project/scripts/verify_governance.py --check ci-sync` -> PASS
- `python project/scripts/verify_governance.py --check python-version` -> PASS
- `PYTHONPATH=src python -m pytest -q tests/test_parity_checks.py` -> `8 passed`
- `PYTHONPATH=src python -m pytest -q tests/test_governance_checks.py` -> `8 passed`
- `python -m ruff check .` -> PASS
- `python -m ruff format --check .` -> PASS
- `python project/scripts/verify_governance.py --check all` -> FAIL on expected strict LOC baseline (`src` >300), but parity check itself passes
- Full gates:
  - `pytest` and `mypy src` fail in current local Python 3.10 due `tomllib` (repo targets 3.13)
  - `pip_audit` fails on existing environment vulnerabilities
  - `bandit -r src` passes

**LOC policy note**
- Non-test/docs net-new code is >150 LOC (primarily parity validator modules).
- Justification: WI-002 explicitly requires executable parity schema and route-fence validation plus governance integration.
- Smaller alternative: split into two PRs:
  1. parity artifacts + docs + WI file,
  2. parity validator modules + governance wiring + tests.