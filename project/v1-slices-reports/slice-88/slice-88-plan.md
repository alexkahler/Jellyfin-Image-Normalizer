# Slice 88 Plan v3

Date: 2026-03-12
Branch: `feat/v1-overhaul`
Inputs used: `project/v1-plan.md`, `WORK_ITEMS.md`, `project/loop-breaker-playbook.md`, Slice 87 artifacts
Planning status: v3 (final)
Final planning verdict: PASS - scoped and approved for implementation worker.

## 1) Slice ID/title
- Slice 88
- Approval-gated one-row route progression for `run|logo` (`v0 -> v1`)

## 2) Goal/objective
- Execute the next objective after Slice 87: progress only `run|logo` from `route=v0` to `route=v1` when gate conditions are satisfied.
- Keep all non-target route-fence rows and non-route governance artifacts unchanged.

## 3) In-scope / out-of-scope
In scope:
- Validate progression precondition from Slice 87 (`decision_gate: eligible-for-flip-proposal`).
- Resolve approval gate from current orchestration request and record `approval_signal` + `approval_source`.
- Apply exactly one route mutation (`run|logo` only) in `project/route-fence.md` and `project/route-fence.json` when gates pass.
- Produce Slice 88 plan/implementation/audit artifacts and one post-audit append in `WORK_ITEMS.md`.
- Run governance checks: `--check readiness`, `--check parity`, `--check all`.

Out of scope:
- Any changes to `src/`, `tests/`, parity matrix, workflow coverage index, verification contract, CI workflow.
- Any non-target route-fence row mutation.
- Same-SHA evidence refresh/continuation work (already resolved in Slice 87).

## 4) Tight writable allowlist
- `project/v1-slices-reports/slice-88/slice-88-plan.md`
- `project/v1-slices-reports/slice-88/slice-88-implementation.md`
- `project/v1-slices-reports/slice-88/slice-88-audit.md`
- `project/route-fence.md`
- `project/route-fence.json`
- `WORK_ITEMS.md` (single append line only, post-audit)

## 5) Measurable acceptance criteria
1. Loop-breaker applicability is explicitly evaluated and recorded as not-triggered for Slice 88 (previous slice is not repeated external-unblock continuation/no-route-flip).
2. Progression precondition is recorded exactly once from Slice 87 as `decision_gate: eligible-for-flip-proposal`.
3. Approval gate evidence is explicit and single-valued:
   - `approval_signal: granted|missing`
   - `approval_source: <exact reference to current user instruction used>`
4. Exactly one terminal progression token is present:
   - `route_progression_outcome: progressed` or
   - `route_progression_outcome: blocked-no-flip`
5. If terminal outcome is `progressed`, target row `run|logo` changes `route v0 -> v1` in both markdown and JSON route-fence artifacts.
6. If terminal outcome is `blocked-no-flip`, route-fence artifacts remain unchanged and target row stays `route=v0`.
7. Mutation cardinality proof is explicit:
   - target-row changed count is `1` only when `progressed`
   - target-row changed count is `0` only when `blocked-no-flip`
   - non-target-row changed count is always `0`
8. Target-row invariants remain unchanged except route:
   - `command=run`, `mode=logo`, `owner_slice=Slice-72`, `parity_status=ready`.
9. Governance checks pass with exit code `0` for readiness, parity, and all.
10. Protected-surface no-diff proof is recorded for `src/`, `tests/`, `project/verification-contract.yml`, `.github/workflows/ci.yml`, `project/workflow-coverage-index.json`, and `project/parity-matrix.md`.
11. File-touch set is allowlist-only.
12. Terminal-token uniqueness proofs equal `1` for both `route_progression_outcome` and `approval_signal`.
13. Anti-loop guard passes: output is rejected if it repeats Slice 87 same-SHA evidence behavior instead of a route progression or deterministic blocked-no-flip outcome.

## 6) Ordered implementation steps
1. Capture baseline target row and full-row snapshots from both route-fence artifacts.
2. Record loop-breaker applicability decision from previous slice context.
3. Record progression precondition from Slice 87 and approval gate (`approval_signal`, `approval_source`).
4. Determine terminal progression outcome (`progressed` or `blocked-no-flip`).
5. If `progressed`, mutate only `run|logo` route in markdown and JSON `v0 -> v1`; if `blocked-no-flip`, perform no route-fence mutation.
6. Re-read route-fence artifacts and compute target/non-target mutation counts.
7. Run governance checks (`readiness`, `parity`, `all`) and record exit codes.
8. Record protected-surface no-diff and allowlist file-touch proofs.
9. Write implementation report with gate evidence, terminal outcome, proofs, and verdict.

## 7) Risks / guardrails / fail-closed
Risks:
- Accidental non-target row edits in route-fence files.
- Ambiguous approval interpretation.
- Hidden out-of-scope diff drift.

Guardrails:
- Single target row contract: `run|logo` only.
- Route-fence is the only governance-truth surface permitted for mutation in this slice.
- Gates are recorded before any mutation.
- Terminal outcome token must be unique and deterministic.

Fail-closed:
- Missing/duplicate gate tokens or terminal progression token.
- Gate mismatch (`decision_gate` not eligible or `approval_signal=missing`) with any route mutation present.
- Cardinality proof mismatch.
- Governance check failure.
- Any out-of-scope diff.

## 8) Suggested next slice
- If `route_progression_outcome: progressed`: Slice 89 post-flip completion-stop/readiness snapshot and route-distribution checkpoint.
- If `route_progression_outcome: blocked-no-flip`: Slice 89 approval-gate resolution (decision-only, no mutation).

## 9) Split-if-too-large
- If implementation requires runtime/test/governance-contract updates, stop and split to a separate slice.
- Keep Slice 88 constrained to one-row route progression gate + route-fence proof + governance verification.

## 10) Anti-loop guard
- Slice 88 must not degrade into same-SHA continuation work.
- If planned/implemented work materially repeats Slice 87 after loop-breaker evaluation, mark `NONCOMPLIANT` and stop orchestration.
- Orchestration stop condition: if Slice 88 output remains materially same as Slice 87 even after this guard, stop completely without advancing next-pointer.