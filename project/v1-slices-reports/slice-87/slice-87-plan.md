# Slice 87 Plan v3

Date: 2026-03-12
Branch: `feat/v1-overhaul`
Inputs used: `project/v1-plan.md`, `WORK_ITEMS.md` (Slice 86 next pointer), `project/loop-breaker-playbook.md`
Planning status: v3 (final)
Final planning verdict: PASS - scoped and approved for implementation worker.

## 1) Slice ID/title
- Slice 87
- Same-SHA CI evidence refresh for `run|logo` after Slice 86 remediation (no route flip)

## 2) Goal/objective
- Refresh same-SHA CI evidence for the post-remediation SHA and produce one terminal decision outcome for `run|logo`.
- Evaluate required jobs `test`, `security`, `quality`, and `governance` and map results to one allowed decision token.
- Preserve `run|logo -> v0 | Slice-72 | ready` and keep readiness counters unchanged.

## 3) In-scope / out-of-scope
In scope:
- Evidence collection for exact same-SHA `CI` workflow runs for one SHA and one target row (`run|logo`).
- Terminal marker recording (`same_sha_branch`, `decision_gate`) with required-job summary.
- Evidence/report artifacts for Slice 87 and one post-audit `WORK_ITEMS.md` append entry.

Out of scope:
- Any route-fence/parity/workflow/verification-contract/CI workflow mutation.
- Any source/runtime/test remediation edits in `src/` or `tests/`.
- Any route flip proposal execution in this slice.
- Any continuation-only write-up with no new terminal evidence.

## 4) Tight writable allowlist
- `project/v1-slices-reports/slice-87/slice-87-plan.md`
- `project/v1-slices-reports/slice-87/slice-87-implementation.md`
- `project/v1-slices-reports/slice-87/slice-87-audit.md`
- `WORK_ITEMS.md` (single append line only, after audit PASS)

## 5) Measurable acceptance criteria
1. Record `local_sha` once and use it as exact same-SHA query target.
2. Record workflow identity (`CI`) and branch context.
3. Execute same-SHA query using exact `head_sha=<local_sha>` and record total matches.
4. If a run exists, record selected `run_id`, `run_url`, run status, and conclusion.
5. Record required-job status/conclusion for `test`, `security`, `quality`, `governance`.
6. Record exactly one terminal marker: `same_sha_branch: evidence-complete` or `same_sha_branch: blocked-external`.
7. Record exactly one decision token: `decision_gate: eligible-for-flip-proposal` or `decision_gate: blocked-no-flip`.
8. Enforce mapping:
   - `evidence-complete` + all required jobs success -> `eligible-for-flip-proposal`
   - `evidence-complete` + any required job non-success -> `blocked-no-flip`
   - `blocked-external` -> `blocked-no-flip`
9. Polling is bounded and explicit: poll until required jobs are terminal or timeout is reached; then branch to `evidence-complete` (terminal data available) or `blocked-external` (timeout/unavailable).
10. If `same_sha_branch: blocked-external` is selected, `inability_reason`, `residual_risk_note`, and `resume_condition` are each present exactly once.
11. `decision_gate: conditional-no-flip` is absent.
12. Uniqueness proofs exist and equal `1`: `decision_token_match_count`, `same_sha_branch_match_count`.
13. Route/readiness invariants remain unchanged (`run|logo` row and readiness totals).
14. Governance checks pass: `--check readiness`, `--check parity`, `--check all`.
15. Protected-surface no-diff proof is recorded for route-fence/parity/workflow/verification-contract/CI/runtime/tests.
16. File-touch bound is enforced: only Slice 87 report files plus post-audit one-line `WORK_ITEMS.md` append are modified.
17. Anti-loop guard passes: output is rejected if it repeats continuation posture without new terminal evidence.

## 6) Ordered implementation steps
1. Capture `local_sha` with `git rev-parse HEAD`.
2. Capture baseline invariants for `run|logo` and readiness totals.
3. Query GitHub Actions same-SHA runs for `CI` with `head_sha=<local_sha>`.
4. Poll within a bounded window until required jobs are terminal or timeout is reached.
5. Branch after polling: select deterministic same-SHA run candidate when terminal evidence exists, otherwise record `blocked-external` timeout/unavailable outcome.
6. Record required-job status for `test`, `security`, `quality`, `governance`.
7. Set terminal markers (`same_sha_branch`, `decision_gate`) from acceptance mapping.
8. Record uniqueness proofs and anti-loop result.
9. Run governance checks (`readiness`, `parity`, `all`) and record exit results.
10. Record protected-surface no-diff proof and finalize implementation + audit artifacts.

## 7) Risks / guardrails / fail-closed
Risks:
- Same-SHA evidence exists but `test` or another required job remains non-success.
- Same-SHA evidence is unavailable and work drifts into repeated continuation text.
- Accidental writes outside evidence/report scope.

Guardrails:
- One target row only (`run|logo`) and one objective only (evidence refresh).
- Evidence-only slice: no route/governance/runtime/test mutation.
- Terminal marker pair and uniqueness proofs are mandatory.
- Required-job summary must always include all four required jobs.

Fail-closed:
- Missing or duplicate terminal markers/tokens.
- Presence of `decision_gate: conditional-no-flip`.
- Missing required-job summary on `evidence-complete`.
- Missing inability reason, residual risk, or resume condition on `blocked-external`.
- Any diff outside allowlist or any governance check failure.
- Anti-loop hard fail if continuation narrative repeats with no new terminal evidence.

## 8) Suggested next slice
- If `decision_gate: eligible-for-flip-proposal`: Slice 88 approval-gated `run|logo` progression proposal (`v0 -> v1`), decision-first and explicit.
- If `decision_gate: blocked-no-flip` due required-job failure: Slice 88 required-job remediation slice (no route flip).
- If `same_sha_branch: blocked-external`: Slice 88 prerequisite-only external-unblock slice before any further evidence refresh.

## 9) Split-if-too-large
- If this slice requires runtime/test or governance-contract edits, stop and split.
- Keep Slice 87 evidence-only; move remediation/mutation to a follow-on slice with its own plan.

## 10) Anti-loop guard
- Reject any Slice 87 implementation/audit output that repeats continuation language from prior slices without new terminal evidence.
- New terminal evidence means at least one of:
  - new exact same-SHA run record (`run_id` + `run_url` + required-job summary), or
  - explicit `blocked-external` outcome with fresh inability reason and concrete resume condition.
- Orchestration stop condition: if planned work/output remains materially the same as Slice 86 after loop-breaker and anti-loop checks, mark the slice `NONCOMPLIANT` and stop without advancing next-pointer.
- If neither appears, mark the slice `NONCOMPLIANT` and do not advance pointer to another continuation-style evidence slice.
