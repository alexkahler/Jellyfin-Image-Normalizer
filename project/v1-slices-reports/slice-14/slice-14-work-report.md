Implemented. Slice 14 COV-05 is now in place and verified.

**Changes made**
- Added minimal governance-level docs topology contract in [governance_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/governance_checks.py#L335), including:
  - stable blocking prefix `docs_topology.contract`
  - bounded extraction for `v1-plan` section + `TECHNICAL_NOTES` statement
  - path normalization/tolerant matching (slashes/punctuation/order)
  - required on-disk directory checks for canonical suites + baselines
- Wired the new docs check into characterization aggregation in [governance_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/governance_checks.py#L406) and [governance_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/governance_checks.py#L588).
- Corrected suite topology drift in [v1-plan.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/v1-plan.md#L305) to:
  - `cli_contract`, `config_contract`, `imaging_contract`, `safety_contract`
- Added focused docs-topology tests in [test_governance_docs_topology.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_governance_docs_topology.py#L1).
- Updated runtime-gate test fixture for new characterization aggregation in [test_governance_runtime_gate.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_governance_runtime_gate.py#L16).
- Added Slice 14 tracking line in [WORK_ITEMS.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/WORK_ITEMS.md#L19).
- Added planning artifact [Slice-14.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/plans/Slice-14.md#L1).

**Verification run**
- `pytest -q tests/test_governance_docs_topology.py tests/test_governance_checks.py tests/test_governance_runtime_gate.py` -> pass (`24 passed`)
- `verify_governance.py --check characterization` -> pass
- `verify_governance.py --check all` -> expected baseline fail only (`src/jfin/*` LOC blockers + existing test LOC warnings)
- Full `pytest` -> pass (`351 passed, 4 warnings`)
- `ruff check .` -> pass
- `ruff format --check .` -> expected baseline fail only on pre-existing `tests/test_characterization_checks_safety.py`
- `mypy src` -> pass
- `bandit -r src` -> pass (no issues)
- `pip_audit` -> pass (no known vulns; local package `jfin` skipped as non-PyPI)
