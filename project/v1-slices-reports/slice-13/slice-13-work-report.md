Implemented Slice 13 (COV-04) end-to-end with the dual-proof, backdrop-only trace contract.

**What changed**
- Added safety trace schema validation (optional globally, strict when present) in [characterization_contract.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_contract.py).
- Added backdrop trace projection + blocking taxonomy in [characterization_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_checks.py):
  - `workflow_coverage.contract_trace_missing`
  - `workflow_coverage.contract_trace_schema`
  - `workflow_coverage.contract_trace_assertion_failed`
- Added trace reporting lines in [governance_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/governance_checks.py) (required/validated/assertion-failures + trace contract OK/NOT OK).
- Migrated `PIPE-BACKDROP-001` baseline to structured trace events in [safety_contract_baseline.json](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/baselines/safety_contract_baseline.json).
- Updated backdrop characterization to emit observed trace events and compare projected observed-vs-baseline invariants in [test_safety_contract_pipeline.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/safety_contract/test_safety_contract_pipeline.py).
- Added reusable trace helpers (opt-in, no global default fixture widening) in [_harness.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/characterization/safety_contract/_harness.py) and [_characterization_test_helpers.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/_characterization_test_helpers.py).
- Added dedicated trace governance tests in [test_characterization_checks_safety_trace.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks_safety_trace.py).
- Updated governance output test expectations in [test_governance_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_governance_checks.py) and fixture wiring in [test_characterization_checks.py](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_characterization_checks.py).
- Updated slice tracking in [WORK_ITEMS.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/WORK_ITEMS.md) and added [Slice-13.md](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/plans/Slice-13.md).

**Verification**
- Targeted pytest (trace/governance/backdrop): `42 passed`.
- Additional targeted pytest set: `26 passed`.
- Full pytest: `345 passed, 4 warnings`.
- `ruff check .`: pass.
- `ruff format --check .`: still fails only on pre-existing `tests/test_characterization_checks_safety.py`.
- `mypy src`: pass.
- `bandit -r src`: no issues.
- `pip_audit`: no known vulnerabilities.
- `verify_governance --check characterization`: pass (includes new trace counters and `Workflow trace contract OK`).
- `verify_governance --check parity`: pass.
- `verify_governance --check readiness`: pass.
- `verify_governance --check all`: fails with the same baseline LOC blockers in `src/jfin/*` and existing test LOC warnings (`6 errors, 9 warnings`), with no new persistent LOC warning introduced by this slice.