Implemented.

Applied skills: `plan-first-scope-and-risks`, `loc-and-complexity-discipline`, `verification-gates-and-diff-discipline`, `cli-and-config-contract`, `pytest-characterization-tests-for-imaging`.

**What was added/changed**
- Surface Coverage Gate module: [surface_coverage_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/surface_coverage_checks.py#L646)
- Canonical index artifact: [surface-coverage-index.json](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/surface-coverage-index.json)
- Gate wired into characterization checks: [characterization_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_checks.py#L30)
- Governance output includes required unmapped counters: [governance_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/governance_checks.py#L198)
- Parity contract IDs extended for Slice 7 closures: [parity_contract.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/parity_contract.py)
- New parity IDs/rows for 3 closures: [parity-matrix.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/parity-matrix.md#L47)
- New/updated tests:
  - [test_characterization_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks.py)
  - [test_surface_coverage_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_surface_coverage_checks.py)
  - [test_logging_utils.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_logging_utils.py#L1)
  - [test_imaging.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_imaging.py#L34)
  - [test_jfin.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_jfin.py#L253)
- Slice docs/report updates:
  - [Slice-07.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/plans/Slice-07.md#L1)
  - [slice-7-audit-report.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/v1-slices-reports/slice-7/slice-7-audit-report.md)
  - [WORK_ITEMS.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/WORK_ITEMS.md#L15)
  - [README.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/README.md)
  - [TECHNICAL_NOTES.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/docs/TECHNICAL_NOTES.md)

**Audit (before/after)**
- CLI unmapped: `36 -> 0`
- Config unmapped: `42 -> 0`
- Observability unmapped: `5 -> 0`
- Parity/test linkage gaps: `n/a -> 0`

**Verification commands run**
1. `$env:PYTHONPATH='src'; py -3.13 -m pytest -q tests/test_surface_coverage_checks.py`
2. `$env:PYTHONPATH='src'; py -3.13 -m pytest -q tests/test_characterization_checks.py tests/test_governance_checks.py`
3. `$env:PYTHONPATH='src'; py -3.13 -m pytest -q tests/test_logging_utils.py`
4. `$env:PYTHONPATH='src'; py -3.13 -m pytest -q tests/test_pipeline.py tests/test_imaging.py -k "scale or no_scale or no_upscale or no_downscale"`
5. `$env:PYTHONPATH='src'; py -3.13 -m pytest -q tests/test_jfin.py -k "exit or generate_config or restore_all or test_jf"`
6. `python project/scripts/verify_governance.py --check characterization`
7. `python project/scripts/verify_governance.py --check all`
8. `rg -n "Slice 7|iteratively planned|WI-001" WORK_ITEMS.md plans/Slice-07.md`

Result:
- All targeted Slice 7 tests passed.
- `--check characterization` passed and reports:
  - `Remaining unmapped CLI items: 0`
  - `Remaining unmapped config keys: 0`
  - `Remaining unmapped observability items: 0`
  - `Remaining parity/test linkage gaps: 0`
- `--check all` still fails only on pre-existing LOC gate errors in `src/jfin/*` (not Slice 7 regression).
