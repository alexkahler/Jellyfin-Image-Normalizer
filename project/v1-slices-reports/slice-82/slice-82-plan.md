# Slice 82 Plan v3

Date: 2026-03-12  
Branch: `feat/v1-overhaul`  
Planning status: v3 (final)

Final planning verdict: PASS - scoped and approved for implementation worker.

## Review checklist compliance
- PASS - in/out scope: in-scope and out-of-scope boundaries are explicit and single-objective.
- PASS - limited files touched: writable allowlist keeps mutation scope tightly bounded.
- PASS - slice ID/title: Slice 82 ID and title are explicit.
- PASS - objective clarity: one objective only (external-unblock same-SHA evidence progression, no route flip).
- PASS - measurable acceptance criteria: token, branch, invariants, mutation-subset, and guard metrics are explicit.
- PASS - ordered implementation steps: sequence is explicit and auditable.
- PASS - risks/guardrails/fail-closed: risks, controls, and stop triggers are explicit.
- PASS - suggested next slice: Slice 83 follow-on is explicit.
- PASS - split-if-too-large: explicit split trigger and containment rule are present.

## 1) Slice ID/title
- Slice 82
- External-unblock continuation for same-SHA evidence progression on `run|logo` (no route flip)

## 2) Goal/objective
- Single objective only: continue external-unblock same-SHA evidence progression for `run|logo`, recording exactly one evidence branch token and exactly one aligned decision gate token without flipping routes.
- Baseline invariants that must remain unchanged:
  - `run|logo -> v0 | Slice-72 | ready`
  - readiness `5/5`.

## 3) In-scope/out-of-scope
### In scope
- `project/v1-slices-reports/slice-82/slice-82-plan.md`
- `project/v1-slices-reports/slice-82/slice-82-implementation.md`
- `project/v1-slices-reports/slice-82/slice-82-audit.md`
- Post-audit orchestration append-only update to `WORK_ITEMS.md` (exactly one Slice 82 line with `next: Slice 83`).

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
- Any scope expansion beyond decision/evidence progression continuation.

## 4) Tight writable allowlist
- Planning worker: `project/v1-slices-reports/slice-82/slice-82-plan.md` only.
- Implementation worker: `project/v1-slices-reports/slice-82/slice-82-implementation.md` only.
- Audit worker: `project/v1-slices-reports/slice-82/slice-82-audit.md` only.
- Orchestration worker (post-audit PASS only): append exactly one Slice 82 line to `WORK_ITEMS.md` with `next: Slice 83`.

## 5) Measurable acceptance criteria
1. Local SHA under evaluation is recorded exactly once in `slice-82-implementation.md`:
   - anchored key `^local_sha:` appears exactly once.
   - `local_sha_count=1`.
2. Same-SHA evidence progression token is recorded exactly once in `slice-82-implementation.md`:
   - anchored key `^same_sha_evidence_token:` appears exactly once.
   - allowed values only:
     - `evidence-complete`
     - `evidence-unavailable`
     - `evidence-blocked`.
3. Decision gate token is recorded exactly once in `slice-82-implementation.md`:
   - anchored key `^decision_gate_token:` appears exactly once.
   - allowed values only:
     - `eligible-for-flip-proposal`
     - `conditional-no-flip`
     - `blocked-no-flip`.
4. Decision/evidence alignment map is enforced exactly:
   - `evidence-complete -> eligible-for-flip-proposal`
   - `evidence-unavailable -> conditional-no-flip`
   - `evidence-blocked -> blocked-no-flip`.
5. Branch-specific required fields are present exactly once for the selected evidence branch:
   - If `evidence-complete`: exactly one each of
     - `ci_run_id:`
     - `ci_run_url:`
     - `required_job_test:`
     - `required_job_security:`
     - `required_job_quality:`
     - `required_job_governance:`.
   - If `evidence-unavailable` or `evidence-blocked`: exactly one each of
     - `same_sha_inability_reason:`
     - `residual_risk_note:`.
6. Baseline row remains unchanged in route-fence artifacts:
   - `run|logo -> v0 | Slice-72 | ready`.
7. Readiness remains unchanged:
   - readiness stays `5/5`.
8. Governance checks pass:
   - `project/scripts/verify_governance.py --check readiness`
   - `project/scripts/verify_governance.py --check parity`
   - `project/scripts/verify_governance.py --check all`.
9. Implementation mutation subset exactness is proven before audit/WORK_ITEMS updates, using the union model:
   - pre-audit changed paths = union(`git diff --name-only`, `git ls-files --others --exclude-standard`).
   - implementation writable set is exactly `{project/v1-slices-reports/slice-82/slice-82-implementation.md}`.
   - implementation mutation subset = intersection(pre-audit changed paths, implementation writable set).
   - `implementation_mutation_subset_count=1`.
   - `implementation_mutation_subset_exact_match=true`.
10. Pre-audit `WORK_ITEMS.md` is unchanged:
   - `pre_audit_work_items_changed_count=0`.
11. Post-audit `WORK_ITEMS.md` single-line append guard passes:
   - `preexisting_slice82_line_count=0`
   - `work_items_line_delta=+1`
   - `work_items_added_lines_count=1`
   - `work_items_removed_lines_count=0`
   - regex matches exactly once: `^- Slice 82 -> .*next:\s*Slice 83\b.*$`
   - `slice82_work_items_next_pointer_match_count=1`.
12. Forbidden-surface no-mutation guard is preserved during implementation/audit for the surfaces listed in section 3.

## 6) Implementation steps
1. Capture baseline proofs for `run|logo -> v0 | Slice-72 | ready` in `project/route-fence.md` and `project/route-fence.json`.
2. Capture baseline readiness counters and confirm `5/5`.
3. Create `slice-82-implementation.md` as an evidence-progression continuation report only.
4. Record exactly one `local_sha` value, exactly one `same_sha_evidence_token` value, and exactly one aligned `decision_gate_token` value.
5. Fill branch-specific required fields for the selected evidence branch.
6. Run governance checks (`readiness`, `parity`, `all`) and capture outputs.
7. Before audit/WORK_ITEMS updates, compute pre-audit changed paths via union(tracked diff, untracked files), then prove implementation mutation subset exactness.
8. Prove forbidden-surface no-mutation and pre-audit `WORK_ITEMS.md` unchanged guards.
9. Create `slice-82-audit.md` with explicit PASS/FAIL evidence for every acceptance criterion.
10. After explicit audit PASS only, append one Slice 82 line to `WORK_ITEMS.md` and prove regex guard for `next: Slice 83`.

## 7) Risks/guardrails/fail-closed triggers
Risks and guardrails:
- Risk: external same-SHA evidence remains unavailable or blocked.
  Guardrail: require one explicit evidence token with branch-specific required fields.
- Risk: ambiguous decision/evidence outcome.
  Guardrail: require exactly one evidence token and exactly one aligned decision token.
- Risk: accidental mutation of governance/runtime/test truth surfaces.
  Guardrail: fail closed unless forbidden-surface changed-path counts remain zero.
- Risk: baseline drift during evidence progression.
  Guardrail: enforce unchanged baseline row and unchanged readiness `5/5`.
- Risk: malformed `WORK_ITEMS.md` progression update.
  Guardrail: enforce pre-audit no-change and post-audit single-line append with regex proof.

Fail-closed triggers (any trigger stops completion):
- `local_sha_count != 1`.
- `same_sha_evidence_token_count != 1` or value outside allowed set.
- `decision_gate_token_count != 1` or value outside allowed set.
- `decision_evidence_alignment_ok != true`.
- Missing branch-specific required fields for the selected evidence branch.
- Any change in `run|logo -> v0 | Slice-72 | ready`.
- Readiness differs from `5/5`.
- Any governance check failure (`readiness`, `parity`, `all`).
- `implementation_mutation_subset_count != 1` or `implementation_mutation_subset_exact_match != true`.
- Any forbidden-surface diff during implementation/audit.
- `pre_audit_work_items_changed_count != 0`.
- Post-audit append guard failure, including regex mismatch for `next: Slice 83`.

## 8) Suggested next slice
- Slice 83: consume Slice 82 decision/evidence branch outcome.
  - If `evidence-complete` with aligned decision: eligible flip-proposal preparation slice (still no unapproved route flip).
  - If `evidence-unavailable` or `evidence-blocked`: continued external-unblock same-SHA progression slice.

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

# Implementation-phase mutation subset guard (run before audit/WORK_ITEMS updates)
$preAuditTrackedChanged = @(git diff --name-only)
$preAuditUntrackedChanged = @(git ls-files --others --exclude-standard)
$preAuditChangedPaths = @($preAuditTrackedChanged + $preAuditUntrackedChanged | Sort-Object -Unique)
"pre_audit_changed_paths_count=$($preAuditChangedPaths.Count)"
"pre_audit_changed_paths_set=$($preAuditChangedPaths -join ',')"
$implementationWritableSet = @('project/v1-slices-reports/slice-82/slice-82-implementation.md')
$implementationMutationSubset = @($preAuditChangedPaths | Where-Object { $_ -in $implementationWritableSet })
"implementation_mutation_subset_count=$($implementationMutationSubset.Count)"
"implementation_mutation_subset_set=$($implementationMutationSubset -join ',')"
"implementation_mutation_subset_exact_match=$($implementationMutationSubset.Count -eq 1 -and $implementationMutationSubset[0] -eq 'project/v1-slices-reports/slice-82/slice-82-implementation.md')"

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
$impl = 'project/v1-slices-reports/slice-82/slice-82-implementation.md'
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

# WORK_ITEMS guards
"pre_audit_work_items_changed_count=$((@($preAuditChangedPaths | Where-Object { $_ -eq 'WORK_ITEMS.md' }).Count))"
"preexisting_slice82_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 82 -> ').Count)"
$beforeCount = (Get-Content WORK_ITEMS.md).Count
# ...append exactly one Slice 82 line after audit PASS...
$afterCount = (Get-Content WORK_ITEMS.md).Count
"work_items_line_delta=$('{0:+#;-#;0}' -f ($afterCount - $beforeCount))"
$wDiff = git diff --unified=0 -- WORK_ITEMS.md
"work_items_added_lines_count=$((($wDiff | Select-String -Pattern '^\+[^+]').Matches.Count))"
"work_items_removed_lines_count=$((($wDiff | Select-String -Pattern '^\-[^-]').Matches.Count))"
"slice82_work_items_next_pointer_match_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 82 -> .*next:\s*Slice 83\b.*$').Count)"
```

## 10) Evidence/report paths
- Plan: `project/v1-slices-reports/slice-82/slice-82-plan.md`
- Implementation report: `project/v1-slices-reports/slice-82/slice-82-implementation.md`
- Audit report: `project/v1-slices-reports/slice-82/slice-82-audit.md`
- Baseline proof surfaces:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - readiness output from `project/scripts/verify_governance.py --check readiness`
- Post-audit orchestration target:
  - `WORK_ITEMS.md`

## 11) Split-if-too-large
- Split immediately if scope expands beyond decision/evidence progression continuation.
- Keep Slice 82 strictly no-route-flip and no mutation of route-fence/parity/workflow/verification-contract/CI/runtime/tests surfaces.
- Defer any broader progression mechanics or route-change actions to Slice 83+.
