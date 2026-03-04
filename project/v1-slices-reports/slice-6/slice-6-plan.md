# Slice 6 Plan: WI-005 Safety Contracts

## Summary
1. Slice 6 enforces Track 1 safety contracts for dry-run/write gates and restore safety before any strangler route flips.
2. Governance stays in the existing characterization check path (`--check characterization`).
3. Safety coverage includes adapter and app gates, profile write-path dry-run gating, restore refusal semantics, and restore profile/item path semantics.
4. Seeded unit tests remain in place as regression guardrails while parity ownership moves to characterization tests.
5. Python 3.13 verification contract remains authoritative.

## Scope
### In scope
1. Add safety parity IDs where coverage gaps existed (`API-DRYRUN-002`, `RST-REFUSE-001`, `RST-PATH-001`).
2. Add `tests/characterization/baselines/safety_contract_baseline.json`.
3. Add `tests/characterization/safety_contract/` harness and characterization tests.
4. Extend characterization governance schema/link checks for the new safety baseline.
5. Re-link safety parity rows to safety characterization owner tests.

### Out of scope
1. Route-fence flips (`v0` to `v1`).
2. Track 2 CLI/config redesign.
3. Broad runtime refactors.

## Public Interfaces / Types
1. New parity IDs:
- `API-DRYRUN-002`
- `RST-REFUSE-001`
- `RST-PATH-001`
2. New baseline artifact:
- `tests/characterization/baselines/safety_contract_baseline.json`
3. Characterization owner tests:
- `tests/characterization/safety_contract/test_safety_contract_api.py`
- `tests/characterization/safety_contract/test_safety_contract_pipeline.py`
- `tests/characterization/safety_contract/test_safety_contract_restore.py`
4. Governance path:
- `python project/scripts/verify_governance.py --check characterization` now enforces safety baseline linkage/schema.

## Safety Baseline Schema
Each safety case includes:
1. `expected_observations`:
- `result` (`return_value`, `raises`, optional extra scalar fields)
- optional `calls`, `stats`, `filesystem` scalar mappings
- optional `ordering` list
2. `expected_messages` optional stable substrings
3. `notes` required non-empty string

## Required Note
Slice 6 introduces restore safety contracts under `tests/characterization/safety_contract/`; later migration may consolidate or alias these into `tests/characterization/restore_contract/` without changing behavior IDs.

## Verification
1. `$env:PYTHONPATH='src'; python -m pytest -q tests/characterization/safety_contract`
2. `$env:PYTHONPATH='src'; python -m pytest -q tests/test_characterization_checks.py tests/test_characterization_checks_links.py tests/test_characterization_checks_imaging.py tests/test_characterization_checks_safety.py`
3. `$env:PYTHONPATH='src'; python -m pytest -q tests/test_client.py -k "dry_run or delete_image or set_user_profile_image"`
4. `$env:PYTHONPATH='src'; python -m pytest -q tests/test_backup.py -k "restore or dry_run"`
5. `python project/scripts/verify_governance.py --check characterization`
6. `python project/scripts/verify_governance.py --check parity`
7. `python project/scripts/verify_governance.py --check all`

## Rollback
1. Revert docs/WI/slice files.
2. Revert parity ID additions and parity row relinks.
3. Revert characterization governance safety checks.
4. Revert safety baseline/harness/tests.
5. Revert any conditional runtime safety fixes.
