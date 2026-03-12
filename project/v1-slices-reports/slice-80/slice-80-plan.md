# Slice 80 Plan v3

Date: 2026-03-12  
Branch: `feat/v1-overhaul`  
Planning status: v3 (final)

Final planning verdict: PASS - scoped and approved for implementation worker.

## Review checklist compliance
- PASS - in/out scope: in-scope and out-of-scope boundaries are explicit and single-objective.
- PASS - limited files touched: role-based writable allowlist keeps mutations tightly bounded.
- PASS - slice ID/title: Slice 80 ID and title are explicit.
- PASS - objective clarity: one objective only (same-SHA decision/evidence remediation, no route flip).
- PASS - measurable acceptance criteria: criteria are tokenized, branch-specific, and metric-based.
- PASS - ordered implementation steps: sequence is explicit and auditable.
- PASS - risks/guardrails/fail-closed presence: risks, protections, and stop triggers are defined.
- PASS - suggested next slice: Slice 81 follow-on is explicit.
- PASS - split-if-too-large: explicit split trigger and containment rule are present.

## 1) Slice ID/title
- Slice 80
- Same-SHA evidence remediation for `run|logo` progression (decision/evidence only, no route flip)

## 2) Goal/objective
- Single objective only: attempt same-SHA CI evidence collection for the local SHA and record one decision/evidence outcome for `run|logo` without changing route/governance/runtime/test truth artifacts.
- Baseline invariants that must remain unchanged through implementation and audit:
  - `run|logo -> v0 | Slice-72 | ready`
  - readiness `5/5`.

## 3) In-scope/out-of-scope
### In scope
- `project/v1-slices-reports/slice-80/slice-80-plan.md`
- `project/v1-slices-reports/slice-80/slice-80-implementation.md`
- `project/v1-slices-reports/slice-80/slice-80-audit.md`
- Post-audit orchestration append-only update to `WORK_ITEMS.md` (exactly one Slice 80 line with next pointer to Slice 81).

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

## 4) Tight writable allowlist by worker role
- Planning worker: `project/v1-slices-reports/slice-80/slice-80-plan.md` only.
- Implementation worker: `project/v1-slices-reports/slice-80/slice-80-implementation.md` only.
- Audit worker: `project/v1-slices-reports/slice-80/slice-80-audit.md` only.
- Orchestration worker (post-audit PASS only): append exactly one Slice 80 line to `WORK_ITEMS.md` with `next: Slice 81`.

## 5) Measurable acceptance criteria
1. Same-SHA evidence attempt for local SHA is recorded exactly once in `slice-80-implementation.md`:
   - `local_sha:` appears exactly once and identifies the local commit SHA under evaluation.
   - anchored key `^same_sha_evidence_token:` appears exactly once.
   - `same_sha_evidence_token:` allowed value:
     - `evidence-complete` OR `evidence-unavailable` OR `evidence-blocked`.
2. Decision gate token is recorded exactly once and is branch-aligned:
   - anchored key `^decision_gate_token:` appears exactly once.
   - `decision_gate_token:` allowed value:
     - `eligible-for-flip-proposal` OR `conditional-no-flip` OR `blocked-no-flip`.
   - Alignment map is enforced:
     - `evidence-complete -> eligible-for-flip-proposal`
     - `evidence-unavailable -> conditional-no-flip`
     - `evidence-blocked -> blocked-no-flip`.
3. Branch-specific evidence fields are complete for `evidence-complete`:
   - exactly one `ci_run_id:`
   - exactly one `ci_run_url:`
   - exactly one required-job status line for each job:
     - `required_job_test:`
     - `required_job_security:`
     - `required_job_quality:`
     - `required_job_governance:`.
4. Branch-specific evidence fields are complete for `evidence-unavailable` or `evidence-blocked`:
   - exactly one `same_sha_inability_reason:`
   - exactly one `residual_risk_note:`.
5. Baseline route row remains unchanged in both route-fence artifacts:
   - `run|logo -> v0 | Slice-72 | ready`.
6. Readiness baseline remains unchanged:
   - `claims/validated = 5/5` before and after implementation/audit checks.
7. Governance checks pass:
   - `project/scripts/verify_governance.py --check readiness`
   - `project/scripts/verify_governance.py --check parity`
   - `project/scripts/verify_governance.py --check all`.
8. Implementation mutation subset is exact before audit/WORK_ITEMS updates:
   - implementation writable set is `{project/v1-slices-reports/slice-80/slice-80-implementation.md}`
   - implementation mutation subset is the intersection of pre-audit changed paths with that implementation writable set
   - `implementation_mutation_subset_count=1`
   - `implementation_mutation_subset_exact_match=true`.
9. Pre-audit `WORK_ITEMS.md` remains unchanged:
   - `pre_audit_work_items_changed_count=0`.
10. Post-audit `WORK_ITEMS.md` append guard passes exactly:
   - `preexisting_slice80_line_count=0`
   - `work_items_line_delta=+1`
   - `work_items_added_lines_count=1`
   - `work_items_removed_lines_count=0`
   - regex matches exactly once: `^- Slice 80 -> .*next:\s*Slice 81\b.*$`
   - `slice80_work_items_next_pointer_match_count=1`.
11. Forbidden-surface no-mutation guard is preserved for implementation/audit phases:
   - changed-path count is zero for route-fence/parity/workflow/verification-contract/CI/runtime/tests surfaces listed in section 3.

## 6) Ordered implementation steps
1. Capture baseline proofs for `run|logo -> v0 | Slice-72 | ready` in `project/route-fence.md` and `project/route-fence.json`.
2. Capture baseline readiness counters and prove `5/5` before implementation evidence capture.
3. Create `slice-80-implementation.md` as evidence-remediation-only report (no route/governance/runtime/test mutation).
4. Record local SHA and exactly one `same_sha_evidence_token`.
5. Record exactly one `decision_gate_token` and prove evidence/decision alignment.
6. Fill required branch-specific evidence fields:
   - `evidence-complete`: run id/url + required-job statuses (`test/security/quality/governance`), or
   - `evidence-unavailable`/`evidence-blocked`: inability reason + residual risk.
7. Run governance checks (`--check readiness`, `--check parity`, `--check all`) and capture results.
8. Prove implementation mutation subset exactness before any audit or `WORK_ITEMS.md` edits.
9. Prove forbidden-surface no-diff guards and pre-audit `WORK_ITEMS.md` unchanged guard.
10. Create `slice-80-audit.md` with explicit PASS/FAIL evidence against every acceptance criterion.
11. After explicit audit PASS only, append one Slice 80 line to `WORK_ITEMS.md` and prove regex guard for `next: Slice 81`.

## 7) Risks/guardrails/fail-closed triggers
Risks and guardrails:
- Risk: accidental route/governance/runtime/test mutation during evidence remediation.
  Guardrail: fail closed unless forbidden-surface changed-path counts remain zero.
- Risk: ambiguous decision/evidence outcome.
  Guardrail: enforce exactly one evidence token and exactly one aligned decision token.
- Risk: incomplete same-SHA branch evidence.
  Guardrail: enforce branch-specific required fields for complete vs unavailable/blocked branches.
- Risk: baseline drift while collecting evidence.
  Guardrail: require unchanged `run|logo -> v0 | Slice-72 | ready` and unchanged readiness `5/5`.
- Risk: malformed `WORK_ITEMS.md` progression update.
  Guardrail: pre-audit no-change and post-audit single-line append + regex checks.

Fail-closed triggers (any trigger => stop and do not claim completion):
- `same_sha_evidence_token_count != 1` or token value outside allowed set.
- `decision_gate_token_count != 1` or token value outside allowed set.
- `decision_evidence_alignment_ok != true`.
- Missing branch-specific required fields for selected evidence branch.
- Any change in baseline route row (`run|logo -> v0 | Slice-72 | ready`).
- Readiness counters differ from `5/5`.
- Any governance check failure (`readiness`, `parity`, `all`).
- `implementation_mutation_subset_count != 1` or `implementation_mutation_subset_exact_match != true`.
- Any forbidden-surface diff during implementation/audit.
- `pre_audit_work_items_changed_count != 0`.
- Post-audit append guard failure, including regex mismatch for `next: Slice 81`.

## 8) Suggested next slice
- Slice 81: branch-driven follow-on for `run|logo` progression based on Slice 80 evidence token:
  - if `evidence-complete` + aligned decision token: progression proposal/approval-gate slice,
  - if `evidence-unavailable` or `evidence-blocked`: continued same-SHA remediation/external-unblock slice,
  - in all cases preserve no-unapproved route flip discipline.

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
$preAuditChanged = @(git diff --name-only)
$implementationWritableSet = @('project/v1-slices-reports/slice-80/slice-80-implementation.md')
$implementationMutationSubset = @($preAuditChanged | Where-Object { $_ -in $implementationWritableSet })
"implementation_mutation_subset_count=$($implementationMutationSubset.Count)"
"implementation_mutation_subset_set=$($implementationMutationSubset -join ',')"
"implementation_mutation_subset_exact_match=$($implementationMutationSubset.Count -eq 1 -and $implementationMutationSubset[0] -eq 'project/v1-slices-reports/slice-80/slice-80-implementation.md')"

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
$impl = 'project/v1-slices-reports/slice-80/slice-80-implementation.md'
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
"pre_audit_work_items_changed_count=$((@(git diff --name-only -- WORK_ITEMS.md)).Count)"
"preexisting_slice80_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 80 -> ').Count)"
$beforeCount = (Get-Content WORK_ITEMS.md).Count
# ...append exactly one Slice 80 line after audit PASS...
$afterCount = (Get-Content WORK_ITEMS.md).Count
"work_items_line_delta=$('{0:+#;-#;0}' -f ($afterCount - $beforeCount))"
$wDiff = git diff --unified=0 -- WORK_ITEMS.md
"work_items_added_lines_count=$((($wDiff | Select-String -Pattern '^\+[^+]').Matches.Count))"
"work_items_removed_lines_count=$((($wDiff | Select-String -Pattern '^\-[^-]').Matches.Count))"
"slice80_work_items_next_pointer_match_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 80 -> .*next:\s*Slice 81\b.*$').Count)"
```

## 10) Evidence/report paths
- Plan: `project/v1-slices-reports/slice-80/slice-80-plan.md`
- Implementation report: `project/v1-slices-reports/slice-80/slice-80-implementation.md`
- Audit report: `project/v1-slices-reports/slice-80/slice-80-audit.md`
- Baseline invariant proof surfaces:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - readiness output from `project/scripts/verify_governance.py --check readiness`
- Post-audit orchestration target:
  - `WORK_ITEMS.md`

## 11) Split-if-too-large rule
Split immediately if any non-documentation mutation is needed beyond the Slice 80 implementation report and post-audit one-line `WORK_ITEMS.md` append.

If split is triggered:
- Keep Slice 80 strictly decision/evidence-remediation only (no route flip, no governance-truth mutation).
- Defer any progression action, governance artifact mutation, runtime/test edits, or broader remediation to Slice 81+.
