# Slice 85 Plan v3

Date: 2026-03-12
Branch: `feat/v1-overhaul`
Planning status: v3 (final)

Final planning verdict: PASS - loop-breaker scoped and approved for implementation.

## Review checklist compliance (review-pass-2 evaluated, final)
- PASS - in/out scope boundaries are explicit and single-objective.
- PASS - writable allowlist is limited to slice report files (+ post-audit `WORK_ITEMS.md` append).
- PASS - slice ID/title and target row are explicit.
- PASS - objective and terminal outcome requirements are explicit.
- PASS - measurable acceptance criteria include marker uniqueness and branch/decision validity.
- PASS - implementation steps are ordered and auditable.
- PASS - risks/guardrails/fail-closed triggers are explicit.
- PASS - suggested next slice is explicit and branch-conditioned.

## 1) Slice ID/title
- Slice 85
- Loop-breaker terminal same-SHA verification for `run|logo` (no route flip)

## 2) Goal/objective
- Break the repeated `evidence-unavailable + conditional-no-flip` continuation loop for `run|logo` by producing a terminal same-SHA evidence outcome tied to one immutable anchor SHA.
- Preserve baseline invariant:
  - `run|logo -> v0 | Slice-72 | ready`
  - readiness `5/5`.

## 3) In-scope / out-of-scope
### In scope
- `project/v1-slices-reports/slice-85/slice-85-plan.md`
- `project/v1-slices-reports/slice-85/slice-85-implementation.md`
- `project/v1-slices-reports/slice-85/slice-85-audit.md`
- External-unblock action and same-SHA CI evidence collection for one anchor SHA.
- Post-audit append-only update to `WORK_ITEMS.md` with Slice 85 result and next pointer.

### Out of scope
- Any route flip for any route-fence row.
- Any mutation during implementation/audit to:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
  - `src/**`
  - `tests/**`
- Any pre-audit mutation to `WORK_ITEMS.md`.

## 4) Writable allowlist
- Planning worker scope: `project/v1-slices-reports/slice-85/slice-85-plan.md`
- Implementation worker scope: `project/v1-slices-reports/slice-85/slice-85-implementation.md`
- Audit worker scope: `project/v1-slices-reports/slice-85/slice-85-audit.md`
- Orchestration scope after audit PASS: append one Slice 85 line to `WORK_ITEMS.md`

## 5) Measurable acceptance criteria
1. Anchor SHA is recorded exactly once (`^anchor_sha:`).
2. Push/publication evidence is recorded with:
   - `push_exit_code`
   - `remote_branch_sha`
   - `push_anchor_match`.
3. Same-SHA CI query evidence is recorded for exact anchor SHA with run count and selected run metadata (if present).
4. Exactly one terminal branch marker exists:
   - `same_sha_branch: evidence-complete` OR
   - `same_sha_branch: blocked-external`.
5. Exactly one decision token exists:
   - `decision_gate: eligible-for-flip-proposal` OR
   - `decision_gate: blocked-no-flip`.
6. `decision_gate: conditional-no-flip` must not appear.
7. Decision validity map is enforced:
   - `same_sha_branch=blocked-external` => `decision_gate=blocked-no-flip`.
   - `same_sha_branch=evidence-complete` and `required_jobs_all_success=true` => `decision_gate=eligible-for-flip-proposal`.
   - `same_sha_branch=evidence-complete` and `required_jobs_all_success=false` => `decision_gate=blocked-no-flip`.
8. If `same_sha_branch=evidence-complete`, report includes:
   - `run_id`, `run_url`,
   - required job status/conclusion for `test`, `security`, `quality`, `governance`.
9. If `same_sha_branch=blocked-external`, report includes:
   - explicit inability reason,
   - residual risk,
   - concrete resume condition.
10. Marker uniqueness proofs are present:
   - `decision_token_match_count=1`
   - `same_sha_branch_match_count=1`.
11. Baseline invariant unchanged (`run|logo -> v0 | Slice-72 | ready`) in md/json.
12. Readiness remains unchanged (`5/5`).
13. Governance checks pass:
   - `project/scripts/verify_governance.py --check readiness`
   - `project/scripts/verify_governance.py --check parity`
   - `project/scripts/verify_governance.py --check all`.
14. Implementation mutation subset exactness is proven with union model:
   - union(tracked changed paths, untracked changed paths),
   - subset against implementation writable set,
   - exact match true.
15. Pre-audit `WORK_ITEMS.md` unchanged.
16. Post-audit `WORK_ITEMS.md` append guard:
   - exactly one Slice 85 line
   - `next: Slice 86` pointer appears exactly once.

## 6) Ordered implementation steps
1. Freeze anchor SHA (`git rev-parse HEAD`).
2. Capture baseline row proofs from `project/route-fence.md` and `project/route-fence.json`.
3. Execute external-unblock publication action (`git push origin feat/v1-overhaul`) and record result.
4. Query same-SHA runs for exact anchor SHA via GitHub REST.
5. If run exists, capture run metadata and required-job status/conclusion fields.
6. Determine terminal branch marker and decision token per acceptance-criteria map.
7. Record marker uniqueness proof counts.
8. Run governance checks (`readiness`, `parity`, `all`) and record results.
9. Record mutation-subset proof, pre-audit `WORK_ITEMS` guard, and forbidden-surface no-diff proofs.
10. Produce implementation report and independent audit report.

## 7) Risks / guardrails / fail-closed
Risks and guardrails:
- Risk: repeated non-terminal continuation posture.
  Guardrail: terminal branch marker mandatory; `conditional-no-flip` forbidden.
- Risk: evidence exists but required jobs fail.
  Guardrail: enforce explicit `required_jobs_all_success` and block decision (`blocked-no-flip`) when false.
- Risk: accidental governance-truth mutation.
  Guardrail: forbidden-surface no-diff proof required.

Fail-closed triggers:
- Missing or duplicate anchor/branch/decision markers.
- Presence of `decision_gate: conditional-no-flip`.
- Missing run/job details for evidence-complete branch.
- Missing inability/resume fields for blocked-external branch.
- Baseline/readiness drift from expected values.
- Governance command failure.
- Mutation-subset mismatch or pre-audit `WORK_ITEMS` change.

## 8) Suggested next slice
- Slice 86 branch-conditioned follow-on:
  - If evidence-complete + all required jobs success: approval-gated route-progression proposal slice (still no implicit flip).
  - If evidence-complete + required job failure: required-job failure triage/remediation slice for `run|logo` progression gate (no route flip).
  - If blocked-external: prerequisite-only external-unblock slice.

## 9) Split-if-too-large
- If scope expands beyond one-row loop-breaker evidence terminalization, split immediately and keep Slice 85 evidence-only.
