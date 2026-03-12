# Slice 86 Plan v3

Date: 2026-03-12
Branch: `feat/v1-overhaul`
Planning status: v3 (final)

Final planning verdict: PASS - scoped and approved for remediation implementation.

## Review checklist compliance (review-pass-2 evaluated, final)
- PASS - single objective and root-cause alignment are explicit.
- PASS - in-scope/out-of-scope boundaries are explicit.
- PASS - file-touch scope is minimal and bounded.
- PASS - acceptance criteria are measurable and test-backed.
- PASS - implementation steps are ordered and auditable.
- PASS - risks/guardrails/fail-closed triggers are explicit.
- PASS - suggested next slice is explicit.

## 1) Slice ID/title
- Slice 86
- Remediate `config_init|n/a` v1 route dispatch failure causing CI test regression

## 2) Goal/objective
- Resolve the CI failure where `--generate-config` exits with route-fence fail-close because `config_init|n/a` now declares `route=v1`.
- Implement minimal runtime support for `config_init|n/a` when route resolves to `v1`.
- Preserve fail-closed behavior for unimplemented `v1` route keys.

## 3) In-scope / out-of-scope
### In scope
- `src/jfin/cli.py`
- `tests/test_route_fence_runtime.py`
- `project/v1-slices-reports/slice-86/slice-86-plan.md`
- `project/v1-slices-reports/slice-86/slice-86-implementation.md`
- `project/v1-slices-reports/slice-86/slice-86-audit.md`
- Post-audit append-only update to `WORK_ITEMS.md` (one Slice 86 line with next pointer).

### Out of scope
- Any route-fence row mutation (`project/route-fence.md` / `project/route-fence.json`).
- Any parity/workflow/verification-contract/CI workflow mutation.
- Any broad CLI refactor beyond route dispatch gate logic for this failure.
- Any route flip.

## 4) Writable allowlist
- Planning artifact: `project/v1-slices-reports/slice-86/slice-86-plan.md`
- Runtime fix: `src/jfin/cli.py`
- Regression tests: `tests/test_route_fence_runtime.py`
- Implementation artifact: `project/v1-slices-reports/slice-86/slice-86-implementation.md`
- Audit artifact: `project/v1-slices-reports/slice-86/slice-86-audit.md`
- Orchestration post-audit: `WORK_ITEMS.md` append-only one line

## 5) Acceptance criteria
1. CI failure is reproducible pre-fix:
   - `tests/test_jfin.py::test_main_exit_code_classes` fails with route-fence blocked message for `config_init|n/a` `route=v1`.
2. Runtime fix implemented:
   - `_enforce_route` permits `route=v1` for `("config_init", "n/a")`.
3. Fail-closed guard retained:
   - `_enforce_route` still exits non-zero for `v1` keys without declared runtime support.
4. Test coverage updated:
   - `test_generate_config_succeeds_when_route_fence_is_v0` is made deterministic by mocking `resolve_route`.
   - prior “v1 fails closed before implementation” expectation is replaced by success expectation for `config_init|n/a` `v1`.
   - an explicit fail-closed test for an unimplemented `v1` key is present.
5. Targeted regression verification passes:
   - `tests/test_jfin.py::test_main_exit_code_classes`
   - `tests/test_route_fence_runtime.py`
   - `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_generate_config_blocks_operational_flags`
6. Governance checks pass:
   - `project/scripts/verify_governance.py --check readiness`
   - `project/scripts/verify_governance.py --check parity`
   - `project/scripts/verify_governance.py --check all`
7. Forbidden-surface no-diff:
   - no diffs in route-fence/parity/workflow/verification-contract/CI files.

## 6) Implementation steps
1. Reproduce failing test and capture the route-fence blocked stdout evidence.
2. Add explicit v1-supported route-key allowlist in CLI runtime gate.
3. Update `_enforce_route` to allow only listed v1-supported keys.
4. Update route-fence runtime tests for new supported behavior and retained fail-closed behavior.
5. Run targeted regression tests.
6. Run governance checks.
7. Write implementation and audit reports.
8. Append Slice 86 outcome to `WORK_ITEMS.md`.

## 7) Risks / guardrails / fail-closed
Risks:
- Over-broad v1 allowance could disable fail-closed protections.
- Under-scoped fix could pass one test while leaving regression in related route-gate tests.

Guardrails:
- Use explicit `(command, mode)` allowlist for v1 support.
- Add/retain test asserting fail-closed for unimplemented `v1` keys.
- Keep mutation scope to one runtime file + one test file.

Fail-closed triggers:
- Any change to governance truth surfaces outside scope.
- Any targeted regression test failure.
- Governance check failure.

## 8) Suggested next slice
- Slice 87: re-run same-SHA evidence progression for `run|logo` after test remediation, aiming for `required_jobs_all_success=true` and `eligible-for-flip-proposal` gate (still no implicit route mutation).

## 9) Split-if-too-large
- If remediation requires broader route-architecture refactor, stop and split into a dedicated runtime-route-implementation slice.
