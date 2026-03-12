## Slice ID/title
- **Slice 91**
- **Post-flip completion-stop checkpoint for `run|logo` (evidence-only, no route mutation)**

## Goal/objective
- Execute one objective only: produce a post-Slice-90 checkpoint that proves `run|logo` remains stable at `v1` and governance remains green, without mutating route-fence or runtime/test surfaces.
- This is not a route-progression slice and not a same-SHA continuation slice.
- Orchestration stop criterion: if planned/observed work remains materially same as previous slice after guardrails, record `STOP` and end orchestration with no next-pointer advancement.

## In-scope / out-of-scope
- In scope:
- Read-only snapshot capture for target row state and readiness distribution.
- Governance verification (`--check readiness`, `--check parity`, `--check all`).
- No-mutation proof capture (hash/diff + cardinality) for route-fence artifacts.
- Slice 91 implementation evidence report authoring.
- Out of scope:
- Any edits to `project/route-fence.md` or `project/route-fence.json`.
- Any `src/` or `tests/` edits.
- Any edits to `project/parity-matrix.md`, `project/workflow-coverage-index.json`, `project/verification-contract.yml`, `.github/workflows/ci.yml`.
- Any same-SHA continuation/progression action.
- Any audit execution/content in implementation phase.

## Tight writable allowlist
- Planning phase writable file only:
- `project/v1-slices-reports/slice-91/slice-91-plan.md`
- Implementation phase writable file only:
- `project/v1-slices-reports/slice-91/slice-91-implementation.md`
- Audit phase writable file only (separate worker; not implementation scope):
- `project/v1-slices-reports/slice-91/slice-91-audit.md`
- `WORK_ITEMS.md` update is orchestration post-audit and is excluded from implementation writable scope.

## Measurable acceptance criteria
1. Snapshot target-row tokens are recorded and single-valued:
1. `snapshot_target_row_token_md: run|logo|v1|Slice-72|ready`
2. `snapshot_target_row_token_json: command=run,mode=logo,route=v1,owner_slice=Slice-72,parity_status=ready`
3. `snapshot_target_row_token_md_match_count=1`
4. `snapshot_target_row_token_json_match_count=1`
2. Snapshot readiness distribution token is recorded and single-valued:
1. `snapshot_readiness_distribution_token: ready_v1=5;ready_v0=0;pending_v0=3;pending_v1=0;total_rows=8`
2. `snapshot_readiness_token_match_count=1`
3. Unique terminal checkpoint token pair is recorded:
1. `checkpoint_scope_token: post_flip_checkpoint_no_mutation`
2. `checkpoint_outcome: pass|blocked`
3. `checkpoint_scope_token_match_count=1`
4. `checkpoint_outcome_token_match_count=1`
4. Governance checks exit `0` on final observed state:
1. `project/scripts/verify_governance.py --check readiness`
2. `project/scripts/verify_governance.py --check parity`
3. `project/scripts/verify_governance.py --check all`
5. Route-fence no-mutation evidence is explicit and zero:
1. Hash proofs: `route_fence_md_hash_before`, `route_fence_md_hash_after`, `route_fence_md_hash_match=true`; `route_fence_json_hash_before`, `route_fence_json_hash_after`, `route_fence_json_hash_match=true`
2. Diff proofs: `route_fence_md_diff_line_count=0`, `route_fence_json_diff_line_count=0`
3. Cardinality proofs: `route_fence_md_changed_count=0`, `route_fence_json_changed_count=0`, `json_added_row_count=0`, `json_removed_row_count=0`
6. Protected-surface no-diff proof is explicit for `src/`, `tests/`, and non-target governance artifacts.
7. STOP-on-sameness is explicit:
1. If no new checkpoint value beyond Slice 90 is produced, set `stop_on_sameness_triggered=true`
2. Final status must be `checkpoint_outcome=blocked` plus `STOP`
3. No next-pointer advancement is allowed in that case.

## Ordered implementation steps
1. Capture baseline target row from `project/route-fence.md` and `project/route-fence.json`.
2. Capture baseline readiness distribution from `project/route-fence.json`.
3. Capture pre-check route-fence hashes and initialize no-mutation diff/cardinality probes.
4. Run governance checks: `--check readiness`, `--check parity`, `--check all`.
5. Capture post-check route-fence hashes, diff line counts, and changed-count/cardinality proofs.
6. Compare observed readiness distribution to expected baseline (`ready_v1=5`, `ready_v0=0`, `pending_v0=3`, `pending_v1=0`, `total_rows=8`).
7. Evaluate material-sameness vs Slice 90 and whether new checkpoint value was produced.
8. Record exactly one terminal checkpoint token pair and uniqueness proofs.
9. Write only `project/v1-slices-reports/slice-91/slice-91-implementation.md`.

## Risks / guardrails / fail-closed
- Risks:
- Accidental route-fence mutation during evidence collection.
- Readiness distribution divergence caused by out-of-scope changes.
- Low-value repetition with no new checkpoint signal.
- Guardrails:
- Evidence-only objective; zero route/runtime/test mutation.
- Phase-scoped writable allowlist enforcement.
- Required hash/diff/cardinality proofs and token uniqueness proofs.
- Fail-closed:
- If readiness distribution diverges from expected baseline and cause is outside slice scope, mark `checkpoint_outcome=blocked` and stop with no mutations.
- If route-fence no-mutation proofs are non-zero or mismatched, mark `checkpoint_outcome=blocked` and stop.
- If work remains materially same as previous slice with no new checkpoint value, record `STOP` and end orchestration with no next-pointer advancement.

## Suggested next slice
- Contingent on `checkpoint_outcome=pass` and `stop_on_sameness_triggered=false`:
- Slice 92 one-objective workflow-coverage expansion for `run|thumb` only (coverage artifact scope only; no route mutation).
- If `checkpoint_outcome=blocked` or `STOP` is recorded:
- No next-slice pointer advancement.

## Split-if-too-large
- Split immediately if any route-fence mutation is required.
- Split immediately if any `src/` or `tests/` edits are required.
- Split immediately if non-allowlist governance artifacts must be edited.
- Split immediately if same-SHA evidence continuation/progression work enters scope.

## Loop-breaker applicability + anti-loop guard
- Loop-breaker applicability for Slice 91: not-triggered.
- Previous-slice pattern check: Previous slice (Slice 90) is not repeated `external-unblock continuation ... no route flip`, so loop-breaker flow is not mandatory.
- Trigger-condition evaluation:
- Condition 1 (multiple consecutive same-target `evidence-unavailable` continuation slices): false.
- Condition 2 (repeated `decision_gate: conditional-no-flip` without new external action): false.
- Condition 3 (repeated same inability reason): false.
- Anti-loop guard:
- Do not propose continuation-style evidence slices from this checkpoint.
- If planned/observed work remains materially same as previous slice after guardrails, record `STOP` and end orchestration with no next-pointer advancement.