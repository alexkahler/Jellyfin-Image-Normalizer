# Slice 78 Plan v3

Date: 2026-03-12  
Branch: `feat/v1-overhaul`  
Planning status: v3 (final)

## Review checklist compliance
- PASS - scope bounded (in/out): in-scope and out-of-scope boundaries are explicit and single-objective.
- PASS - files touched bounded: writable allowlist defines exact role-based file limits.
- PASS - slice id/title: Slice 78 ID and title are explicitly declared.
- PASS - objective clarity: one objective only (`run|logo` readiness activation `pending -> ready`).
- PASS - measurable acceptance criteria: criteria are metric-based with exact invariants and deltas.
- PASS - ordered implementation steps: sequential implementation steps are listed and auditable.
- PASS - risk/guardrails/fail-closed presence: explicit risks, guardrails, and stop triggers are defined.
- PASS - suggested next slice presence: Slice 79 follow-on is explicitly stated.
- PASS - split-if-too-large rule presence: explicit split triggers and containment rule are present.

Final planning verdict: PASS - scoped and approved for implementation worker.

## 1) Slice ID/title
- Slice 78
- Readiness-claim activation for `run|logo` (`pending -> ready`) with route preserved at `v0`

## 2) Goal/objective
- Single objective only: activate readiness for exactly one route-fence row by changing `run|logo` parity status from `pending` to `ready`, while preserving `route=v0` and `owner_slice=Slice-72`.

## 3) In-scope/out-of-scope
### In scope
- `project/route-fence.md` (target row `run|logo` parity-status update only)
- `project/route-fence.json` (matching target row parity-status update only)
- `project/v1-slices-reports/slice-78/slice-78-plan.md`
- `project/v1-slices-reports/slice-78/slice-78-implementation.md`
- `project/v1-slices-reports/slice-78/slice-78-audit.md`
- Post-audit orchestration append-only update to `WORK_ITEMS.md` (one line)

### Out of scope
- Any route flip (`v0 -> v1`) for any row
- Any owner change for any row
- Any route-fence row mutation outside `run|logo`
- Any edits to:
  - `project/verification-contract.yml`
  - `project/workflow-coverage-index.json`
  - `project/parity-matrix.md`
  - `.github/workflows/ci.yml`
  - `src/**`
  - `tests/**` (except writing slice report artifacts)
- Any pre-audit mutation to `WORK_ITEMS.md`

## 4) Writable allowlist
- Planning worker: `project/v1-slices-reports/slice-78/slice-78-plan.md` only.
- Implementation worker:
  - Exactly 3 implementation files before audit/WORK_ITEMS updates:
    - `{project/route-fence.md, project/route-fence.json, project/v1-slices-reports/slice-78/slice-78-implementation.md}`
  - No additional implementation file mutations are allowed.
- Audit worker:
  - `project/v1-slices-reports/slice-78/slice-78-audit.md`
- Orchestration worker (post-audit PASS only):
  - append exactly one Slice 78 line to `WORK_ITEMS.md` with `next: Slice 79`

## 5) Acceptance criteria
1. Target-row parity transition is exact in both route-fence artifacts:
   - `run|logo parity_status: pending -> ready`.
2. Target-row invariants are preserved in both route-fence artifacts:
   - `route` remains `v0`
   - `owner_slice` remains `Slice-72`
   - `command`/`mode` remain `run`/`logo`.
3. Only the target row changes in route-fence markdown and JSON:
   - `route_fence_target_changed_row_count=1`
   - `route_fence_non_target_changed_row_count=0`.
4. Readiness counters advance exactly by `+1` claim and `+1` validated:
   - baseline `claims/validated=4/4`
   - post-change `claims/validated=5/5`
   - `readiness_claims_delta=+1`
   - `readiness_validated_delta=+1`.
5. No verification/workflow/parity contract drift:
   - no diffs for `project/verification-contract.yml`
   - no diffs for `project/workflow-coverage-index.json`
   - no diffs for `project/parity-matrix.md`.
6. Governance checks pass:
   - `project/scripts/verify_governance.py --check readiness`
   - `project/scripts/verify_governance.py --check parity`
   - `project/scripts/verify_governance.py --check all`.
7. Implementation mutation set/count is exact before audit/WORK_ITEMS updates:
   - `implementation_mutated_paths_count=3`
   - exact set equals `{project/route-fence.md, project/route-fence.json, project/v1-slices-reports/slice-78/slice-78-implementation.md}`.
8. Scope guard holds before audit close:
   - `out_of_scope_changed_path_count=0`.
9. Pre-audit `WORK_ITEMS.md` guard holds:
   - `pre_audit_work_items_changed_count=0`.
10. Post-audit `WORK_ITEMS.md` append guards all pass:
   - `preexisting_slice78_line_count=0`
   - `work_items_line_delta=+1`
   - `work_items_added_lines_count=1`
   - `work_items_removed_lines_count=0`
   - regex guard matches exactly once: `^- Slice 78 -> .*next:\s*Slice 79\b.*$`
   - `slice78_work_items_next_pointer_match_count=1`.

## 6) Implementation steps
1. Capture baseline proofs for `run|logo` in `project/route-fence.md` and `project/route-fence.json`.
2. Capture baseline readiness counters (`claims`, `validated`) from `--check readiness`.
3. Update only `run|logo parity_status` from `pending` to `ready` in `project/route-fence.md`.
4. Apply matching single-row update in `project/route-fence.json`.
5. Prove row-level diff cardinality (`target changed=1`, `non-target changed=0`) across both route-fence artifacts.
6. Run governance checks: `--check readiness`, `--check parity`, `--check all`.
7. Capture post-change readiness counters and prove exact deltas (`+1/+1`) and expected post-state (`5/5`).
8. Prove no diffs for `project/verification-contract.yml`, `project/workflow-coverage-index.json`, and `project/parity-matrix.md`.
9. Prove pre-audit `WORK_ITEMS.md` unchanged.
10. Write `slice-78-implementation.md` with explicit PASS/FAIL evidence.
11. Audit worker verifies all acceptance criteria and writes `slice-78-audit.md` with explicit PASS/FAIL verdict.
12. After explicit audit PASS only, append one Slice 78 line to `WORK_ITEMS.md` and prove Slice 79 regex guard.

## 7) Risks/guardrails/fail-closed triggers
### Risks and guardrails
- Risk: accidental route or owner drift while flipping parity.
  - Guardrail: fail closed unless both artifacts prove `route=v0` and `owner_slice=Slice-72` unchanged.
- Risk: multi-row route-fence mutation.
  - Guardrail: enforce row-level diff cardinality (`target=1`, `non-target=0`).
- Risk: hidden scope creep into governance contract artifacts.
  - Guardrail: explicit no-diff proof for verification contract, workflow coverage index, and parity matrix.
- Risk: premature or malformed `WORK_ITEMS.md` update.
  - Guardrail: pre-audit no-change check plus post-audit append and regex guards.

### Fail-closed triggers (any trigger => stop and do not claim completion)
- `run|logo` parity transition is not exactly `pending -> ready` in both route-fence artifacts.
- `run|logo` route is not `v0` or owner is not `Slice-72` after mutation.
- Any non-target route-fence row changes.
- Readiness counters do not move exactly `4/4 -> 5/5` (`+1/+1`).
- Any governance check fails (`readiness`, `parity`, or `all`).
- Any diff is present in `project/verification-contract.yml`, `project/workflow-coverage-index.json`, or `project/parity-matrix.md`.
- `out_of_scope_changed_path_count != 0`.
- `pre_audit_work_items_changed_count != 0`.
- Post-audit WORK_ITEMS guards fail (`preexisting_slice78_line_count != 0`, append counters mismatch, or regex count != 1).
- Missing `slice-78-implementation.md` or missing `slice-78-audit.md`.

## 8) Suggested next slice
- Slice 79: route-progression decision record for `run|logo` (decision-only, no route flip), contingent on Slice 78 audit PASS and preserved same-SHA evidence discipline.

## 9) Verification commands
```powershell
# Baseline target-row proof (before mutation)
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*logo\s*\|\s*v0\s*\|\s*Slice-72\s*\|\s*pending\s*\|'
$rfPre = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$runLogoPre = $rfPre.rows | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'logo' } | Select-Object -First 1
"run_logo_pre_ok=$($null -ne $runLogoPre -and $runLogoPre.route -eq 'v0' -and $runLogoPre.owner_slice -eq 'Slice-72' -and $runLogoPre.parity_status -eq 'pending')"

# Baseline readiness counters
$readPre = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
$claimsPre = [int](($readPre | Select-String -Pattern 'Route readiness claims:\s*(\d+)').Matches[0].Groups[1].Value)
$validatedPre = [int](($readPre | Select-String -Pattern 'Route readiness claims validated:\s*(\d+)').Matches[0].Groups[1].Value)
"readiness_claims_pre=$claimsPre"
"readiness_validated_pre=$validatedPre"

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

# Post-change readiness counters and exact +1/+1 delta
$readPost = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
$claimsPost = [int](($readPost | Select-String -Pattern 'Route readiness claims:\s*(\d+)').Matches[0].Groups[1].Value)
$validatedPost = [int](($readPost | Select-String -Pattern 'Route readiness claims validated:\s*(\d+)').Matches[0].Groups[1].Value)
"readiness_claims_post=$claimsPost"
"readiness_validated_post=$validatedPost"
"readiness_claims_delta=$($claimsPost - $claimsPre)"
"readiness_validated_delta=$($validatedPost - $validatedPre)"

# Post-change target-row proof
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*logo\s*\|\s*v0\s*\|\s*Slice-72\s*\|\s*ready\s*\|'
$rfPost = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$runLogoPost = $rfPost.rows | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'logo' } | Select-Object -First 1
"run_logo_post_ok=$($null -ne $runLogoPost -and $runLogoPost.route -eq 'v0' -and $runLogoPost.owner_slice -eq 'Slice-72' -and $runLogoPost.parity_status -eq 'ready')"

# Out-of-scope diff guard (allows only route-fence + slice-78 artifacts + post-audit WORK_ITEMS)
$allowed = @(
  'project/route-fence.md',
  'project/route-fence.json',
  'project/v1-slices-reports/slice-78/slice-78-plan.md',
  'project/v1-slices-reports/slice-78/slice-78-implementation.md',
  'project/v1-slices-reports/slice-78/slice-78-audit.md',
  'WORK_ITEMS.md'
)
$changed = @(git diff --name-only)
$outOfScope = @($changed | Where-Object { $_ -notin $allowed })
"out_of_scope_changed_path_count=$($outOfScope.Count)"
"out_of_scope_changed_paths=$($outOfScope -join ',')"

# Protected no-diff checks
"verification_contract_changed_count=$((@(git diff --name-only -- project/verification-contract.yml)).Count)"
"workflow_coverage_changed_count=$((@(git diff --name-only -- project/workflow-coverage-index.json)).Count)"
"parity_matrix_changed_count=$((@(git diff --name-only -- project/parity-matrix.md)).Count)"

# Pre-audit WORK_ITEMS guard
"pre_audit_work_items_changed_count=$((@(git diff --name-only -- WORK_ITEMS.md)).Count)"

# Post-audit WORK_ITEMS append + regex guards
"preexisting_slice78_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 78 -> ').Count)"
$beforeCount = (Get-Content WORK_ITEMS.md).Count
# ...append exactly one Slice 78 line...
$afterCount = (Get-Content WORK_ITEMS.md).Count
"work_items_line_delta=$('{0:+#;-#;0}' -f ($afterCount - $beforeCount))"
$wDiff = git diff --unified=0 -- WORK_ITEMS.md
"work_items_added_lines_count=$((($wDiff | Select-String -Pattern '^\+[^+]').Matches.Count))"
"work_items_removed_lines_count=$((($wDiff | Select-String -Pattern '^\-[^-]').Matches.Count))"
"slice78_work_items_next_pointer_match_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 78 -> .*next:\s*Slice 79\b.*$').Count)"
```

## 10) Evidence/report paths
- Plan: `project/v1-slices-reports/slice-78/slice-78-plan.md`
- Implementation report: `project/v1-slices-reports/slice-78/slice-78-implementation.md`
- Audit report: `project/v1-slices-reports/slice-78/slice-78-audit.md`
- Mutation surfaces:
  - `project/route-fence.md`
  - `project/route-fence.json`
- Invariant/protected proof surfaces:
  - `project/verification-contract.yml`
  - `project/workflow-coverage-index.json`
  - `project/parity-matrix.md`
- Post-audit orchestration target:
  - `WORK_ITEMS.md`

## 11) Split-if-too-large rule
Split immediately if any of the following becomes necessary:
- Any edit outside `run|logo` row in route-fence markdown/JSON.
- Any change to route or owner fields.
- Any mutation to verification contract, workflow coverage index, parity matrix, CI workflow, runtime code, or tests.
- Any second objective (including route progression).

If split is triggered, keep Slice 78 limited to one objective: readiness activation for `run|logo` only (`pending -> ready`) with `route=v0` and `owner_slice=Slice-72` preserved.
