## Slice ID/title
- **Slice 90**
- **Approval-gated one-row route progression retry for `run|logo` (`v0 -> v1`)**

## Goal/objective
- Execute exactly one objective: attempt a one-row route progression for `run|logo` from `v0` to `v1` under explicit gates.
- This is **not materially the same as Slice 89**:
- Slice 89 objective was runtime remediation (`src/jfin/cli.py`, `tests/test_route_fence_runtime.py`) with mandatory no-route-flip.
- Slice 90 objective is governance-truth route mutation only (`project/route-fence.md` + `project/route-fence.json`) with no runtime/test edits.

## In-scope / out-of-scope
- In scope:
- Baseline capture of target row from `project/route-fence.md` and `project/route-fence.json`.
- Gate evidence capture with explicit source references.
- One-row mutation attempt on `run|logo` only.
- Governance verification: `--check readiness`, `--check parity`, `--check all`.
- Deterministic terminal outcome recording: `route_progression_outcome: progressed|blocked-no-flip`.
- Out of scope:
- Any `src/` edits.
- Any `tests/` edits.
- Any parity/workflow/verification-contract/CI workflow edits.
- Any non-target route-fence row mutation.
- Any same-SHA continuation/evidence-loop activity.
- Any audit authoring/execution in this implementation slice (audit is downstream, separate phase).

## Tight writable allowlist
- Implementation phase allowlist only:
- `project/v1-slices-reports/slice-90/slice-90-plan.md`
- `project/v1-slices-reports/slice-90/slice-90-implementation.md`
- `project/route-fence.md`
- `project/route-fence.json`
- `WORK_ITEMS.md` (single post-audit append only; not during implementation execution)
- Audit phase is separate and out of implementation scope for this plan.

## Measurable acceptance criteria
1. Loop-breaker applicability check is explicit and `not-triggered`, with reason tied to `project/loop-breaker-playbook.md` trigger conditions not being met.
2. Prior-slice pattern evaluation is explicit:
1. Previous slice (Slice 89) is not a repeated `external-unblock continuation ... no route flip` pattern.
2. Therefore loop-breaker flow is not mandatory for Slice 90.
3. Gate tokens are single-valued and evidence-backed:
1. `precondition_token: decision_gate=eligible-for-flip-proposal`
2. `precondition_source_ref: project/v1-slices-reports/slice-87/slice-87-implementation.md`
3. `remediation_source_ref: project/v1-slices-reports/slice-89/slice-89-implementation.md` with `final_implementation_outcome: remediation-complete-no-route-flip`
4. `approval_signal: granted|missing` (exactly one)
5. `approval_source_ref: current explicit user instruction for Slice 90 progression attempt`
4. Exactly one terminal outcome token exists: `route_progression_outcome: progressed|blocked-no-flip`.
5. Mutation proof fields are explicit:
1. `md_target_row_changed_count` = `1` only if `progressed`, else `0`
2. `json_target_row_changed_count` = `1` only if `progressed`, else `0`
3. `md_non_target_row_changed_count=0`
4. `json_non_target_row_changed_count=0`
5. `json_added_row_count=0`
6. `json_removed_row_count=0`
6. Target invariants preserved except route:
1. `command=run`
2. `mode=logo`
3. `owner_slice=Slice-72`
4. `parity_status=ready`
7. Governance checks exit `0` for readiness/parity/all on final state.
8. Protected surfaces unchanged: `src/`, `tests/`, `project/parity-matrix.md`, `project/workflow-coverage-index.json`, `project/verification-contract.yml`, `.github/workflows/ci.yml`.
9. File-touch set is allowlist-only.

## Ordered implementation steps
1. Capture baseline target row snapshots from `project/route-fence.md` and `project/route-fence.json`.
2. Record gate evidence fields with source refs:
1. precondition from Slice 87 implementation artifact
2. remediation completion from Slice 89 implementation artifact
3. approval token from current instruction
3. Evaluate gates and set provisional action path.
4. If gates pass, mutate only target route `run|logo: v0 -> v1` in md/json.
5. Run `--check readiness`, `--check parity`, `--check all`.
6. If checks fail, revert target route to `v0` and set terminal `blocked-no-flip`.
7. Compute and record all mutation/cardinality proofs, including row-key drift proofs.
8. Record protected-surface no-diff and allowlist-only proofs.
9. Write Slice 90 implementation artifact only; audit is downstream and out of implementation scope.

## Risks / guardrails / fail-closed
- Risks:
- Route progression still fails readiness at final verification.
- Accidental non-target edits in route-fence artifacts.
- Hidden scope expansion into runtime/test code.
- Guardrails:
- Single-row contract: `run|logo` only.
- Zero `src/` and `tests/` edits allowed.
- No non-route governance artifact mutation.
- Fail-closed:
- Missing/duplicate gate tokens or missing source refs -> no flip.
- Any required `src/`/`tests/` change to make progression pass -> immediate split/stop.
- Any mutation proof mismatch (`non_target_changed>0`, `json_added_row_count>0`, `json_removed_row_count>0`) -> stop as noncompliant.
- Governance check failure after attempted flip -> rollback to `v0` and terminate as `blocked-no-flip`.

## Suggested next slice
- If `progressed`: Slice 91 post-flip completion-stop snapshot (no route mutation).
- If `blocked-no-flip` with new actionable delta identified: Slice 91 focused remediation (no route mutation).
- If STOP-on-sameness is hit: no next-slice pointer advancement.

## Split-if-too-large
- Immediate split/stop if any `src/` or `tests/` edit is needed.
- Immediate split/stop if more than one route-fence row must change.
- Immediate split/stop if additional governance artifacts must be mutated.

## Loop-breaker applicability + anti-loop guard
- Loop-breaker applicability: **not required** for Slice 90.
- Explicit prior-slice evaluation: Previous slice (Slice 89) is not a repeated `external-unblock continuation ... no route flip` pattern; therefore loop-breaker flow is not mandatory for this slice.
- Anti-loop guard:
- Require explicit operational delta vs Slice 88/89 pattern: this slice must attempt gated one-row route mutation with full mutation proofs.
- **STOP-on-sameness criterion tied to instruction:** if planned/observed work is still materially same as the previous slice after applying required guardrails, record `STOP` and end orchestration with no next-slice pointer advancement.