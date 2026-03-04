Implemented Slice 5 end-to-end as requested, with governance-only changes and no runtime edits in `src/jfin`.

**What I changed**
- Added architecture baseline schema/serialization module: [architecture_contract.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/architecture_contract.py)
- Added architecture checks module (ratcheted non-entry exits + conditional boundary guards): [architecture_checks.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/architecture_checks.py)
- Added new governance selector and baseline helper:
  - `--check architecture`
  - `--check architecture --print-baseline`
  - Wired into `--check all`
  - File: [governance_checks.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/governance_checks.py)
- Added baseline artifact: [architecture-baseline.json](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/architecture-baseline.json)
- Added/updated tests:
  - [test_architecture_checks.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_architecture_checks.py)
  - [test_governance_checks_architecture.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_governance_checks_architecture.py)
  - [test_governance_checks.py](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_governance_checks.py)
- Added WI doc: [WI-001.md](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/plans/WI-001.md)
- Updated docs:
  - [README.md](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/README.md)
  - [TECHNICAL_NOTES.md](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/docs/TECHNICAL_NOTES.md)

**Verification**
- `PYTHONPATH=src python -m pytest -q tests/test_architecture_checks.py` -> `11 passed`
- `PYTHONPATH=src python -m pytest -q tests/test_governance_checks.py -k architecture` -> `1 passed`
- `PYTHONPATH=src python -m pytest -q tests/test_architecture_checks.py tests/test_governance_checks.py tests/test_governance_checks_architecture.py` -> `23 passed`
- `python project/scripts/verify_governance.py --check architecture` -> `PASS`
- `python project/scripts/verify_governance.py --check architecture --print-baseline` -> prints valid baseline JSON
- `rg -n "verify_governance.py --check all" .github/workflows/ci.yml project/scripts/governance_checks.py` -> both CI/workflow and checker still enforce `--check all`
- `python project/scripts/verify_governance.py --check all` -> fails only on known pre-existing LOC gate profile; architecture/parity/characterization pass

**Full-gate notes**
- `python -m ruff check .` -> pass
- `python -m ruff format --check .` -> pass
- `python -m bandit -r src` -> pass
- `python -m pytest -q` -> fails in current environment (Python 3.10 missing `tomllib`)
- `python -m mypy src` -> same `tomllib` import issue
- `python -m pip_audit` -> reports pre-existing dependency vulnerabilities in local env

**LOC/complexity note**
- Non-test/docs net new LOC is >150 (roughly ~500, mainly in new architecture governance modules + baseline artifact), justified by introducing a full new check family with explicit contract, AST analysis, and ratchet logic.
- Smaller alternative would be embedding architecture logic directly into `governance_checks.py`, but that would reduce clarity/testability and conflict with separation used by `parity` and `characterization` checks.

---

**Findings**
1. No remaining Slice 5 blockers after re-check and follow-up fixes.
2. `F-001` was valid and is now fixed: `entry_exit_modules` is enforced as an exact fixed list (`["src/jfin/cli.py"]`), not “contains cli”.  
   [architecture_contract.py:146](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/project/scripts/architecture_contract.py:146)
3. `F-002` is now covered with explicit schema-negative tests for:
- extra/missing entry module
- negative counter values
- unknown counter keys  
  [test_architecture_contract_schema.py:40](C:/Users/akaehler/Proton Drive/alex.kahler/My files/Projects/Jellyfin Image Normalizer/tests/test_architecture_contract_schema.py:40)

**Verification rerun**
1. `PYTHONPATH=src python -m pytest -q tests/test_architecture_checks.py tests/test_architecture_contract_schema.py tests/test_governance_checks.py tests/test_governance_checks_architecture.py` -> `27 passed`
2. `PYTHONPATH=src python -m pytest -q tests/test_governance_checks.py -k architecture` -> `1 passed`
3. `python project/scripts/verify_governance.py --check architecture` -> `PASS`
4. `python project/scripts/verify_governance.py --check architecture --print-baseline` -> valid baseline output
5. `python project/scripts/verify_governance.py --check all` -> unchanged pre-existing LOC-only failures; architecture/parity/characterization all pass

**Residual non-Slice-5 limits**
1. Full `pytest`/`mypy` in this local env still hit pre-existing Python 3.10 `tomllib` issues (repo expects 3.13).
2. `pip_audit` reports pre-existing dependency vulnerabilities unrelated to Slice 5 logic.