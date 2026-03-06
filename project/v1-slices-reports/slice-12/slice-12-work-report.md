Implemented Slice 12 COV-03 as requested, including claim-scoped runtime proof and no route flips.

**Code changes**
- Added full readiness semantic gate in [project/scripts/readiness_checks.py#L290](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/readiness_checks.py#L290):
  - readiness predicate (`parity status=ready` or `route=v1`)
  - `route=v1 => parity status=ready`
  - unmapped `ready` blocking
  - parity/baseline/owner linkage validation
  - `future_split_debt.readiness_blocking` enforcement
  - claim-scoped runtime overlay (`runtime_not_green`, `runtime_unmapped_parity`)
  - deterministic `readiness.*` taxonomy and `ReadinessReport`
- Added structured runtime diagnostics in [project/scripts/characterization_checks.py#L66](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/characterization_checks.py#L66) and wired them through runtime warnings for claim filtering.
- Wired readiness into governance CLI/reporting in [project/scripts/governance_checks.py#L25](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/governance_checks.py#L25).
- Enforced route-fence parity status enum (`pending|ready`) in both markdown+JSON paths via:
  - [project/scripts/parity_contract.py#L32](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/parity_contract.py#L32)
  - [project/scripts/parity_checks.py#L106](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/scripts/parity_checks.py#L106)
- Updated governance docs/work tracking:
  - [project/route-fence.md#L5](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/project/route-fence.md#L5)
  - [WORK_ITEMS.md#L17](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/WORK_ITEMS.md#L17)

**Tests added**
- [tests/test_readiness_checks.py#L17](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_readiness_checks.py#L17)
- [tests/test_readiness_runtime_overlay.py#L19](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_readiness_runtime_overlay.py#L19)
- [tests/test_governance_readiness.py#L16](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_governance_readiness.py#L16)
- [tests/test_parity_route_status.py#L13](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/test_parity_route_status.py#L13)
- shared helper: [tests/_readiness_test_helpers.py#L1](C:/Users/akaehler/Proton%20Drive/alex.kahler/My%20files/Projects/Jellyfin%20Image%20Normalizer/tests/_readiness_test_helpers.py#L1)

**Verification results**
- `pytest`: pass (`339 passed`)
- `ruff check .`: pass
- `mypy src`: pass
- `bandit -r src`: pass
- `pip_audit`: pass
- `verify_governance.py --check parity`: pass
- `verify_governance.py --check readiness`: pass
- `verify_governance.py --check all`: fails only on pre-existing LOC contract blockers in `src/jfin/*` (unchanged by this slice)
- `ruff format --check .`: fails on one pre-existing file: `tests/test_characterization_checks_safety.py` (not part of this slice)
