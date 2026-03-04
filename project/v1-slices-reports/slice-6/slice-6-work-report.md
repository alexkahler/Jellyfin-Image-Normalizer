Implemented end-to-end per your Slice 6 plan.

**What I changed**
- Added WI-005 parity IDs and safety ownership links in [project/parity-matrix.md](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/parity-matrix.md) and required-ID inventory in [project/scripts/parity_contract.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/parity_contract.py).
- Extended characterization contracts/checks for WI-005 in:
  - [project/scripts/characterization_contract.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_contract.py)
  - [project/scripts/characterization_checks.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_checks.py)
- Added structured safety baseline:
  - [tests/characterization/baselines/safety_contract_baseline.json](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/baselines/safety_contract_baseline.json)
- Added safety characterization harness/tests:
  - [tests/characterization/safety_contract/_harness.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/safety_contract/_harness.py)
  - [tests/characterization/safety_contract/test_safety_contract_api.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/safety_contract/test_safety_contract_api.py)
  - [tests/characterization/safety_contract/test_safety_contract_pipeline.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/safety_contract/test_safety_contract_pipeline.py)
  - [tests/characterization/safety_contract/test_safety_contract_restore.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/safety_contract/test_safety_contract_restore.py)
- Updated governance test scaffolding:
  - [tests/_characterization_test_helpers.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/_characterization_test_helpers.py)
  - [tests/test_characterization_checks.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks.py)
  - [tests/test_characterization_checks_safety.py](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_safety.py)
- Added WI/slice docs + docs sync:
  - [plans/WI-005.md](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/plans/WI-005.md)
  - [project/v1-slices-reports/slice-6/slice-6-plan.md](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/v1-slices-reports/slice-6/slice-6-plan.md)
  - [README.md](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/README.md)
  - [docs/TECHNICAL_NOTES.md](c:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/docs/TECHNICAL_NOTES.md)

**Behavioral scope outcome**
- No `src/jfin/*` runtime code changes were needed; contracts matched observed behavior.
- Dual-gate coverage now explicitly includes profile endpoint dry-run DELETE+POST path (`API-DRYRUN-002`).
- Restore refusal semantics are explicitly characterized (`SystemExit(1)` on missing backup root) and path semantics are covered (`RST-PATH-001`).

**Verification run**
- `python -m ruff check .` -> pass
- `python -m ruff format --check .` -> pass
- `PYTHONPATH=src python -m pytest -q tests/characterization/safety_contract` -> `7 passed, 2 skipped`
- `PYTHONPATH=src python -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_links.py tests/test_characterization_checks_imaging.py tests/test_characterization_checks_safety.py` -> `19 passed`
- `PYTHONPATH=src python -m pytest -q tests/test_client.py -k "dry_run or delete_image or set_user_profile_image"` -> `8 passed`
- `PYTHONPATH=src python -m pytest -q tests/test_backup.py -k "restore or dry_run"` -> `20 passed`
- `python project/scripts/verify_governance.py --check characterization` -> pass
- `python project/scripts/verify_governance.py --check parity` -> pass
- `python project/scripts/verify_governance.py --check all` -> fails only on pre-existing LOC gate (`src/jfin/*`) with existing oversized test warnings

**Known pre-existing environment limits**
- `python -m mypy src` fails on missing `tomllib` in local Python 3.10.
- Full `PYTHONPATH=src python -m pytest -q` fails collection for same `tomllib` reason.
- `python -m pip_audit` reports pre-existing dependency vulnerabilities in local env.
- I left pre-existing unrelated modification in `project/v1-plan.md` untouched.