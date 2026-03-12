# Slice 89 Plan v3

Date: 2026-03-12
Branch: `feat/v1-overhaul`
Inputs used: `project/v1-plan.md`, `WORK_ITEMS.md`, `project/loop-breaker-playbook.md`, Slice 88 artifacts
Planning status: v3 (final)
Final planning verdict: PASS - scoped and approved for implementation worker.

## 1) Slice ID/title
- Slice 89
- `run|logo` route-progression unblock remediation (runtime/readiness diagnostics), no route flip

## 2) Goal/objective
- Remove the runtime/readiness blocker observed in Slice 88 when `run|logo` was transiently routed to `v1`.
- Keep route-fence truth unchanged in this slice (`run|logo` remains `v0`) so progression can be retried safely in a follow-on slice.

## 3) In-scope / out-of-scope
In scope:
- Reproduce the blocker path linked to `run|logo` v1 dispatch/runtime readiness.
- Implement minimal runtime remediation for `run|logo` v1 dispatch viability.
- Add/update focused regression tests proving target v1 dispatch viability while preserving fail-closed behavior on non-target unimplemented v1 rows.
- Produce Slice 89 plan/implementation/audit artifacts and one post-audit append in `WORK_ITEMS.md`.
- Run governance checks: `--check readiness`, `--check parity`, `--check all`.

Out of scope:
- Any route-fence route mutation (`run|logo` must remain `v0`).
- Any changes to parity matrix, workflow coverage index, verification contract, CI workflow.
- Broad refactors unrelated to target dispatch unblock.

## 4) Tight writable allowlist
- `project/v1-slices-reports/slice-89/slice-89-plan.md`
- `project/v1-slices-reports/slice-89/slice-89-implementation.md`
- `project/v1-slices-reports/slice-89/slice-89-audit.md`
- `src/jfin/cli.py`
- `tests/test_route_fence_runtime.py`
- `tests/characterization/cli_contract/test_cli_contract_characterization.py` (only if strictly required)
- `WORK_ITEMS.md` (single append line only, post-audit)

## 5) Measurable acceptance criteria
1. Loop-breaker applicability is explicitly recorded as not-triggered (not a repeated external-unblock continuation/no-route-flip slice).
2. Reproduction evidence is recorded for the target blocker path (`run|logo` v1 dispatch/runtime readiness).
3. Minimal runtime remediation is implemented for target path and does not broaden to unrelated command/mode routes.
4. Focused regression tests prove:
   - target `run|logo` v1 dispatch executes successfully under targeted test conditions,
   - non-target unimplemented v1 rows remain fail-closed.
5. Route-fence files are unchanged in final diff:
   - `project/route-fence.md` changed count = 0
   - `project/route-fence.json` changed count = 0
   - `route_flip_performed: false`
6. Governance checks pass with exit code 0 for readiness, parity, and all.
7. Protected-surface no-diff proof is recorded for parity matrix, workflow coverage index, verification contract, and CI workflow.
8. File-touch set is allowlist-only.
9. Anti-loop guard passes: slice includes new runtime remediation evidence (code+tests), not continuation narrative only.

## 6) Ordered implementation steps
1. Capture baseline target row state (`run|logo -> v0 | Slice-72 | ready`) and route-fence checksum.
2. Reproduce blocker via focused tests/commands and record failure evidence.
3. Implement minimal remediation in `src/jfin/cli.py` for target path.
4. Add/update focused tests in `tests/test_route_fence_runtime.py` (and characterization test only if required).
5. Run targeted tests for repro->fix verification.
6. Run governance checks (`readiness`, `parity`, `all`).
7. Confirm route-fence no-diff and protected-surface no-diff proofs.
8. Write implementation report with repro evidence, fix summary, verification outputs, and verdict.

## 7) Risks / guardrails / fail-closed
Risks:
- Scope creep into unrelated dispatch routes.
- Regressing fail-closed safety for non-target unimplemented v1 rows.
- Hidden accidental route-fence mutation.

Guardrails:
- Single objective: target `run|logo` runtime unblock only.
- No route-fence mutation in this slice.
- Keep edits limited to listed runtime/test files.

Fail-closed:
- If blocker cannot be reproduced with focused evidence, mark slice blocked.
- If remediation requires multi-module refactor beyond this scope, stop and split.
- If route-fence files change, mark `NONCOMPLIANT` and stop.

## 8) Suggested next slice
- If remediation succeeds: Slice 90 retry approval-gated one-row route progression for `run|logo` (`v0 -> v1`).
- If remediation remains blocked: Slice 90 narrower root-cause remediation slice (no route mutation).

## 9) Split-if-too-large
- If more than one runtime module beyond `src/jfin/cli.py` is required, split into dedicated sub-slices.
- Keep test edits constrained to route-fence runtime coverage and only essential characterization adjustments.

## 10) Anti-loop guard
- Slice 89 must include concrete runtime remediation artifacts (code + tests + reproduced blocker evidence).
- Reject continuation-style output with no new remediation evidence.
- If planned/implemented work is materially the same as Slice 88 fail-closed narrative, mark `NONCOMPLIANT` and stop.
- Orchestration stop condition: if Slice 89 output remains materially same as Slice 88 after this guard, stop completely without advancing next-pointer.