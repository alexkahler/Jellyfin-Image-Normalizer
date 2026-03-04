Implemented WI-004 end-to-end (additive only, no `src/jfin` runtime changes).

**What I changed**
- Added WI slice plan: [plans/WI-004.md](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\plans\WI-004.md)
- Added baseline artifacts:
  - [tests/characterization/baselines/cli_contract_baseline.json](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\tests\characterization\baselines\cli_contract_baseline.json)
  - [tests/characterization/baselines/config_contract_baseline.json](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\tests\characterization\baselines\config_contract_baseline.json)
- Added shared harness + characterization suites:
  - [tests/characterization/_harness.py](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\tests\characterization\_harness.py)
  - [tests/characterization/cli_contract/test_cli_contract_characterization.py](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\tests\characterization\cli_contract\test_cli_contract_characterization.py)
  - [tests/characterization/config_contract/test_config_contract_characterization.py](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\tests\characterization\config_contract\test_config_contract_characterization.py)
- Updated parity ownership/linkage for `CLI-*` and `CFG-*` only: [project/parity-matrix.md](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\project\parity-matrix.md)
- Added characterization governance modules:
  - [project/scripts/characterization_contract.py](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\project\scripts\characterization_contract.py)
  - [project/scripts/characterization_checks.py](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\project\scripts\characterization_checks.py)
- Wired new blocking check into governance runner (`--check characterization`, included in `--check all`): [project/scripts/governance_checks.py](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\project\scripts\governance_checks.py)
- Added governance tests:
  - [tests/test_characterization_checks.py](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\tests\test_characterization_checks.py)
  - [tests/test_characterization_checks_links.py](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\tests\test_characterization_checks_links.py)
  - Updated [tests/test_governance_checks.py](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\tests\test_governance_checks.py)
- Updated docs:
  - [README.md](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\README.md)
  - [docs/TECHNICAL_NOTES.md](C:\Users\akaehler\Proton Drive\alex.kahler\My files\Projects\Jellyfin Image Normalizer\docs\TECHNICAL_NOTES.md)

**Verification run**
- `python -m ruff check .` passed.
- `python -m ruff format --check .` passed.
- `PYTHONPATH=src python -m pytest -q tests/test_characterization_checks.py` passed (`3` tests after split).
- `PYTHONPATH=src python -m pytest -q tests/test_characterization_checks_links.py` passed (`3` tests).
- `PYTHONPATH=src python -m pytest -q tests/test_governance_checks.py` passed (`9` tests).
- `PYTHONPATH=src python -m pytest -q tests/characterization/...` skipped under local Python `3.10.10` (guarded for missing `tomllib`); will execute on Python `3.13`.
- `python project/scripts/verify_governance.py --check characterization` passed.
- `python project/scripts/verify_governance.py --check parity` passed.
- `python project/scripts/verify_governance.py --check all` fails only on expected strict LOC baseline in `src/` (plus existing oversized legacy test warnings).

**Full-gate notes**
- `pytest -q` fails collection locally because Python is `3.10.10` and `tomllib` is unavailable in runtime modules.
- `mypy src` fails for the same `tomllib` import reason in local 3.10.
- `bandit -r src` passed.
- `pip_audit` reported existing environment vulnerabilities (not introduced by this slice).

Pre-existing local modification in `WORK_ITEMS.md` was left untouched.

---

Implemented remediation for all three reported issues.

**Fixes Applied**
- Added explicit missing-owner-file negative test:  
  [tests/test_characterization_checks_links.py:77](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_links.py:77)
- Made Milestone 2 harness verification effective by adding harness tests:  
  [tests/characterization/test_harness.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/test_harness.py)
- Updated harness to explicitly reset global state before and after each CLI case:  
  [tests/characterization/_harness.py:158](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/_harness.py:158), [tests/characterization/_harness.py:214](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/_harness.py:214)
- Added harness verification command into WI-004 plan:  
  [plans/WI-004.md:23](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/plans/WI-004.md:23)

**Re-Verification**
- `$env:PYTHONPATH='src'; python -m pytest -q tests/characterization -k harness` -> `7 passed, 13 deselected` (now effective, exit 0)
- `$env:PYTHONPATH='src'; python -m pytest -q tests/test_characterization_checks.py` -> `3 passed`
- `$env:PYTHONPATH='src'; python -m pytest -q tests/test_characterization_checks_links.py` -> `4 passed`
- `$env:PYTHONPATH='src'; python -m pytest -q tests/test_governance_checks.py` -> `9 passed`
- `$env:PYTHONPATH='src'; python -m pytest -q tests/characterization/cli_contract/test_cli_contract_characterization.py` -> `6 skipped` (local Python 3.10)
- `$env:PYTHONPATH='src'; python -m pytest -q tests/characterization/config_contract/test_config_contract_characterization.py` -> `7 skipped` (local Python 3.10)
- `python project/scripts/verify_governance.py --check characterization` -> `PASS`
- `python project/scripts/verify_governance.py --check parity` -> `PASS`
- `python project/scripts/verify_governance.py --check all` -> expected `FAIL` on legacy LOC blockers; includes `PASS` for parity + characterization
- `git diff --name-only -- src/jfin` -> no output (runtime unchanged)

`WORK_ITEMS.md` remains a pre-existing unrelated modification and was not touched.