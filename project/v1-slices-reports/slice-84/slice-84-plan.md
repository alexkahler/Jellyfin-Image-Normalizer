# Slice 84 Plan v3

Date: 2026-03-12  
Branch: `feat/v1-overhaul`  
Planning status: v3 (final)

Final planning verdict: PASS - scoped and approved for implementation worker.

## Review checklist compliance (review-pass-2 evaluated, final)
- PASS - single objective: external-unblock continuation for same-SHA evidence progression on `run|logo` only.
- PASS - explicit scope bounds: in-scope/out-of-scope are concrete and narrow.
- PASS - tight writable allowlist: worker-specific file ownership is explicit.
- PASS - measurable acceptance criteria: token cardinality/alignment and union-model mutation subset proof are required.
- PASS - ordered implementation steps: execution order is explicit and auditable.
- PASS - risk/guardrail/fail-closed coverage: stop conditions are explicit.
- PASS - suggested next slice: branch-conditioned Slice 85 follow-on is defined.

## 1) Slice ID/title
- Slice 84
- External-unblock continuation for same-SHA evidence progression on `run|logo` (decision/evidence only, no route flip)

## 2) Goal/objective
- Single objective only: continue same-SHA CI evidence progression for `run|logo` and record exactly one evidence branch token and exactly one aligned decision token for this slice.
- Route mutation is forbidden in Slice 84. Even if evidence is complete, this slice may only record proposal eligibility (`eligible-for-flip-proposal`), not execute a route flip.
- Baseline invariants that must remain unchanged:
  - `run|logo -> v0 | Slice-72 | ready`
  - readiness `5/5`.

## 3) In-scope/out-of-scope
### In scope
- `project/v1-slices-reports/slice-84/slice-84-plan.md`
- `project/v1-slices-reports/slice-84/slice-84-implementation.md`
- `project/v1-slices-reports/slice-84/slice-84-audit.md`
- Post-audit orchestration append-only update to `WORK_ITEMS.md` (exactly one Slice 84 line with `next: Slice 85`).

### Out of scope
- Any route flip for any route-fence row.
- Any mutation to route-fence artifacts in Slice 84 even if `same_sha_evidence_token=evidence-complete`; Slice 84 may only record eligibility/proposal readiness.
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
- Any scope expansion beyond external-unblock same-SHA continuation evidence recording.

## 4) Tight writable allowlist by worker role
- Planning worker: `project/v1-slices-reports/slice-84/slice-84-plan.md` only.
- Implementation worker: `project/v1-slices-reports/slice-84/slice-84-implementation.md` only.
- Audit worker: `project/v1-slices-reports/slice-84/slice-84-audit.md` only.
- Orchestration worker (post-audit PASS only): append exactly one Slice 84 line to `WORK_ITEMS.md` with `next: Slice 85`.

## 5) Measurable acceptance criteria
1. Local SHA is recorded exactly once in `slice-84-implementation.md`:
   - anchored key `^local_sha:` appears exactly once.
   - `local_sha_count=1`.
2. Same-SHA evidence token is recorded exactly once:
   - anchored key `^same_sha_evidence_token:` appears exactly once.
   - allowed values only: `evidence-complete|evidence-unavailable|evidence-blocked`.
3. Decision gate token is recorded exactly once:
   - anchored key `^decision_gate_token:` appears exactly once.
   - allowed values only: `eligible-for-flip-proposal|conditional-no-flip|blocked-no-flip`.
4. Decision/evidence alignment is exact:
   - `evidence-complete -> eligible-for-flip-proposal`
   - `evidence-unavailable -> conditional-no-flip`
   - `evidence-blocked -> blocked-no-flip`.
5. Branch-specific required fields are present exactly once for the selected branch:
   - If `evidence-complete`: exactly one each of `ci_run_id`, `ci_run_url`, `required_job_test`, `required_job_security`, `required_job_quality`, `required_job_governance`.
   - If `evidence-unavailable` or `evidence-blocked`: exactly one each of `same_sha_inability_reason`, `residual_risk_note`.
6. Route-fence baseline remains unchanged in markdown and JSON:
   - `run|logo -> v0 | Slice-72 | ready`.
   - `run_logo_route_flip_attempted=false`.
7. Readiness remains unchanged:
   - `readiness_claims=5`
   - `readiness_validated=5`.
8. Governance checks pass:
   - `project/scripts/verify_governance.py --check readiness`
   - `project/scripts/verify_governance.py --check parity`
   - `project/scripts/verify_governance.py --check all`.
9. Implementation mutation subset exactness is proven before audit/`WORK_ITEMS.md` updates using the union model:
   - `pre_audit_changed_paths = union(git diff --name-only, git ls-files --others --exclude-standard)`.
   - implementation writable set is exactly `{project/v1-slices-reports/slice-84/slice-84-implementation.md}`.
   - implementation mutation subset = intersection(pre_audit_changed_paths, implementation writable set).
   - `implementation_mutation_subset_count=1`.
   - `implementation_mutation_subset_exact_match=true`.
10. Pre-audit `WORK_ITEMS.md` remains unchanged:
    - `pre_audit_work_items_changed_count=0`.
11. Post-audit `WORK_ITEMS.md` append guard passes exactly:
    - `preexisting_slice84_line_count=0`
    - `work_items_line_delta=+1`
    - `work_items_added_lines_count=1`
    - `work_items_removed_lines_count=0`
    - regex matches exactly once: `^- Slice 84 -> .*next:\s*Slice 85\b.*$`
    - `slice84_work_items_next_pointer_match_count=1`.
12. Forbidden-surface no-mutation guard holds during implementation/audit for all surfaces listed in section 3.

## 6) Ordered implementation steps
1. Capture baseline proofs for `run|logo -> v0 | Slice-72 | ready` in `project/route-fence.md` and `project/route-fence.json`.
2. Capture readiness counters and confirm `5/5`.
3. Create `slice-84-implementation.md` as decision/evidence continuation only (no route mutation).
4. Record exactly one `local_sha`, exactly one `same_sha_evidence_token`, and exactly one aligned `decision_gate_token`.
5. Populate required branch-specific fields for the selected evidence branch.
6. Run governance checks (`--check readiness`, `--check parity`, `--check all`) and capture outputs.
7. Before audit/`WORK_ITEMS.md` updates, compute union-model pre-audit changed paths and prove implementation mutation subset exactness.
8. Prove forbidden-surface no-mutation and pre-audit `WORK_ITEMS.md` unchanged guards.
9. Create `slice-84-audit.md` with explicit PASS/FAIL evidence for every acceptance criterion.
10. After explicit audit PASS only, append one Slice 84 line to `WORK_ITEMS.md` and prove regex guard for `next: Slice 85`.

## 7) Risks/guardrails/fail-closed triggers
Risks and guardrails:
- Risk: same-SHA CI evidence remains unavailable due external factors.
  Guardrail: require exactly one evidence token and branch-complete required fields.
- Risk: ambiguous decision state.
  Guardrail: require exactly one decision token and exact decision/evidence alignment.
- Risk: accidental route mutation during evidence continuation.
  Guardrail: route flip is prohibited in this slice; evidence-complete can only yield proposal eligibility token.
- Risk: accidental mutation of governance/runtime/test truth surfaces.
  Guardrail: fail closed unless all forbidden-surface changed-path counts are zero.
- Risk: malformed `WORK_ITEMS.md` progression line.
  Guardrail: enforce pre-audit no-change and post-audit single-line append with regex proof.

Fail-closed triggers (any trigger stops completion):
- `local_sha_count != 1`.
- `same_sha_evidence_token_count != 1` or token outside allowed set.
- `decision_gate_token_count != 1` or token outside allowed set.
- `decision_evidence_alignment_ok != true`.
- Missing branch-specific required fields for selected evidence branch.
- Any route-fence change for `run|logo` from `v0 | Slice-72 | ready`.
- Any attempted route flip in Slice 84 (`run_logo_route_flip_attempted=true`).
- Readiness differs from `5/5`.
- Any governance check failure (`readiness`, `parity`, `all`).
- `implementation_mutation_subset_count != 1` or `implementation_mutation_subset_exact_match != true`.
- Any forbidden-surface diff during implementation/audit.
- `pre_audit_work_items_changed_count != 0`.
- Post-audit append guard failure, including regex mismatch for `next: Slice 85`.

## 8) Suggested next slice
- Slice 85: branch-conditioned follow-on for `run|logo`.
  - If `same_sha_evidence_token=evidence-complete`: Slice 85 proposal-prep only (still approval-gated and no implicit flip).
  - Else: Slice 85 external-unblock continuation for same-SHA evidence progression (no route flip).

## 9) Verification/evidence commands
```powershell
# Baseline row and readiness invariants
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*logo\s*\|\s*v0\s*\|\s*Slice-72\s*\|\s*ready\s*\|'
$rf = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$runLogo = $rf.rows | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'logo' } | Select-Object -First 1
"run_logo_baseline_ok=$($null -ne $runLogo -and $runLogo.route -eq 'v0' -and $runLogo.owner_slice -eq 'Slice-72' -and $runLogo.parity_status -eq 'ready')"

$read = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
$claims = [int](($read | Select-String -Pattern 'Route readiness claims:\s*(\d+)').Matches[0].Groups[1].Value)
$validated = [int](($read | Select-String -Pattern 'Route readiness claims validated:\s*(\d+)').Matches[0].Groups[1].Value)
"readiness_claims=$claims"
"readiness_validated=$validated"
"readiness_is_5_5=$($claims -eq 5 -and $validated -eq 5)"

# Required governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

# Implementation-phase mutation subset guard (union model; run before audit/WORK_ITEMS updates)
$preAuditTrackedChanged = @(git diff --name-only)
$preAuditUntrackedChanged = @(git ls-files --others --exclude-standard)
$preAuditChangedPaths = @($preAuditTrackedChanged + $preAuditUntrackedChanged | Sort-Object -Unique)
"pre_audit_changed_paths_count=$($preAuditChangedPaths.Count)"
"pre_audit_changed_paths_set=$($preAuditChangedPaths -join ',')"
$implementationWritableSet = @('project/v1-slices-reports/slice-84/slice-84-implementation.md')
$implementationMutationSubset = @($preAuditChangedPaths | Where-Object { $_ -in $implementationWritableSet })
"implementation_mutation_subset_count=$($implementationMutationSubset.Count)"
"implementation_mutation_subset_set=$($implementationMutationSubset -join ',')"
"implementation_mutation_subset_exact_match=$($implementationMutationSubset.Count -eq 1 -and $implementationMutationSubset[0] -eq 'project/v1-slices-reports/slice-84/slice-84-implementation.md')"

# Forbidden-surface no-mutation proofs
"route_fence_md_changed_count=$((@(git diff --name-only -- project/route-fence.md)).Count)"
"route_fence_json_changed_count=$((@(git diff --name-only -- project/route-fence.json)).Count)"
"parity_matrix_changed_count=$((@(git diff --name-only -- project/parity-matrix.md)).Count)"
"workflow_coverage_changed_count=$((@(git diff --name-only -- project/workflow-coverage-index.json)).Count)"
"verification_contract_changed_count=$((@(git diff --name-only -- project/verification-contract.yml)).Count)"
"ci_workflow_changed_count=$((@(git diff --name-only -- .github/workflows/ci.yml)).Count)"
"runtime_src_changed_count=$((@(git diff --name-only -- src)).Count)"
"tests_changed_count=$((@(git diff --name-only -- tests)).Count)"

# Token cardinality + alignment + branch-specific field checks
$impl = 'project/v1-slices-reports/slice-84/slice-84-implementation.md'
$localSha = Select-String -Path $impl -Pattern '^local_sha:\s*[0-9a-f]{7,40}\s*$'
$evidence = Select-String -Path $impl -Pattern '^same_sha_evidence_token:\s*(evidence-complete|evidence-unavailable|evidence-blocked)\s*$'
$decision = Select-String -Path $impl -Pattern '^decision_gate_token:\s*(eligible-for-flip-proposal|conditional-no-flip|blocked-no-flip)\s*$'
"local_sha_count=$($localSha.Count)"
"same_sha_evidence_token_count=$($evidence.Count)"
"decision_gate_token_count=$($decision.Count)"

$evidenceToken = if ($evidence.Count -eq 1) { $evidence.Matches[0].Groups[1].Value } else { '' }
$decisionToken = if ($decision.Count -eq 1) { $decision.Matches[0].Groups[1].Value } else { '' }
$decisionAlignmentOk = $false
if ($evidenceToken -eq 'evidence-complete') { $decisionAlignmentOk = $decisionToken -eq 'eligible-for-flip-proposal' }
if ($evidenceToken -eq 'evidence-unavailable') { $decisionAlignmentOk = $decisionToken -eq 'conditional-no-flip' }
if ($evidenceToken -eq 'evidence-blocked') { $decisionAlignmentOk = $decisionToken -eq 'blocked-no-flip' }
"decision_evidence_alignment_ok=$decisionAlignmentOk"

$hasRunId = (Select-String -Path $impl -Pattern '^ci_run_id:\s*\S+\s*$').Count -eq 1
$hasRunUrl = (Select-String -Path $impl -Pattern '^ci_run_url:\s*https?://\S+\s*$').Count -eq 1
$hasTest = (Select-String -Path $impl -Pattern '^required_job_test:\s*\S+\s*$').Count -eq 1
$hasSecurity = (Select-String -Path $impl -Pattern '^required_job_security:\s*\S+\s*$').Count -eq 1
$hasQuality = (Select-String -Path $impl -Pattern '^required_job_quality:\s*\S+\s*$').Count -eq 1
$hasGovernance = (Select-String -Path $impl -Pattern '^required_job_governance:\s*\S+\s*$').Count -eq 1
$hasReason = (Select-String -Path $impl -Pattern '^same_sha_inability_reason:\s*.+$').Count -eq 1
$hasResidual = (Select-String -Path $impl -Pattern '^residual_risk_note:\s*.+$').Count -eq 1

$branchFieldsOk = $false
if ($evidenceToken -eq 'evidence-complete') {
  $branchFieldsOk = $hasRunId -and $hasRunUrl -and $hasTest -and $hasSecurity -and $hasQuality -and $hasGovernance
}
if ($evidenceToken -eq 'evidence-unavailable' -or $evidenceToken -eq 'evidence-blocked') {
  $branchFieldsOk = $hasReason -and $hasResidual
}
"same_sha_branch_fields_ok=$branchFieldsOk"

# Explicit no-route-flip proof
"run_logo_route_flip_attempted=$((@(git diff --name-only -- project/route-fence.md project/route-fence.json)).Count -gt 0)"

# WORK_ITEMS guards
"pre_audit_work_items_changed_count=$((@($preAuditChangedPaths | Where-Object { $_ -eq 'WORK_ITEMS.md' }).Count))"
"preexisting_slice84_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 84 -> ').Count)"
$beforeCount = (Get-Content WORK_ITEMS.md).Count
# ...append exactly one Slice 84 line after audit PASS...
$afterCount = (Get-Content WORK_ITEMS.md).Count
"work_items_line_delta=$('{0:+#;-#;0}' -f ($afterCount - $beforeCount))"
$wDiff = git diff --unified=0 -- WORK_ITEMS.md
"work_items_added_lines_count=$((($wDiff | Select-String -Pattern '^\+[^+]').Matches.Count))"
"work_items_removed_lines_count=$((($wDiff | Select-String -Pattern '^\-[^-]').Matches.Count))"
"slice84_work_items_next_pointer_match_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 84 -> .*next:\s*Slice 85\b.*$').Count)"
```

## 10) Evidence/report paths
- Plan: `project/v1-slices-reports/slice-84/slice-84-plan.md`
- Implementation report: `project/v1-slices-reports/slice-84/slice-84-implementation.md`
- Audit report: `project/v1-slices-reports/slice-84/slice-84-audit.md`
- Baseline proof surfaces:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - readiness output from `project/scripts/verify_governance.py --check readiness`
- Post-audit orchestration target:
  - `WORK_ITEMS.md`

## 11) Split-if-too-large
- Split immediately if scope expands beyond same-SHA evidence continuation documentation.
- Keep Slice 84 strictly no-route-flip and no mutation of route-fence/parity/workflow/verification-contract/CI/runtime/tests surfaces during implementation/audit.
- Defer any progression proposal mechanics beyond tokenized decision recording to Slice 85+.
