# Slice 79 Plan v3

Date: 2026-03-12  
Branch: `feat/v1-overhaul`  
Planning status: v3 (final)

Final planning verdict: PASS - scoped and approved for implementation worker.

## Review checklist compliance
- PASS - scoped in/out boundaries: in-scope and out-of-scope boundaries are explicit and single-objective.
- PASS - limited file touch set: role-based writable allowlist bounds file mutations.
- PASS - slice ID/title: Slice 79 ID and title are explicitly declared.
- PASS - clear objective: one objective only (decision-only record for `run|logo` with no route flip).
- PASS - measurable acceptance criteria: token, invariants, mutation, and guard metrics are explicit.
- PASS - ordered implementation steps: sequential implementation steps are listed and auditable.
- PASS - risks/guardrails/fail-closed presence: explicit risks, guardrails, and stop triggers are defined.
- PASS - suggested next slice present: Slice 80 follow-on is explicitly stated.
- PASS - split-if-too-large present: explicit split trigger keeps Slice 79 decision-only.

## 1) Slice ID/title
- Slice 79
- Route-progression decision record for `run|logo` (decision-only, no route flip)

## 2) Goal/objective
- Single objective only: produce a decision record for `run|logo` route progression readiness while preserving all governance truth artifacts and runtime/test code unchanged.
- This slice is documentation-only implementation: decision capture and audit evidence, not route mutation.

## 3) In-scope/out-of-scope
### In scope
- `project/v1-slices-reports/slice-79/slice-79-plan.md`
- `project/v1-slices-reports/slice-79/slice-79-implementation.md`
- `project/v1-slices-reports/slice-79/slice-79-audit.md`
- Post-audit orchestration append-only one-line update to `WORK_ITEMS.md` with next pointer to Slice 80.

### Out of scope
- Any route flip for any route-fence row.
- Any governance-truth mutation to:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
- Any runtime/tests mutation:
  - `src/**`
  - `tests/**`
- Any pre-audit mutation to `WORK_ITEMS.md`.

## 4) Tight writable allowlist by worker role
- Planning worker: `project/v1-slices-reports/slice-79/slice-79-plan.md` only.
- Implementation worker: `project/v1-slices-reports/slice-79/slice-79-implementation.md` only.
- Audit worker: `project/v1-slices-reports/slice-79/slice-79-audit.md` only.
- Orchestration worker (post-audit PASS only): append exactly one Slice 79 line to `WORK_ITEMS.md` with `next: Slice 80`.

## 5) Measurable acceptance criteria
1. Decision gate token is recorded exactly once in `slice-79-implementation.md`:
   - allowed values: `eligible-for-flip-proposal` OR `conditional-no-flip` OR `blocked-no-flip`
   - anchored line key appears exactly once: `^decision_gate_token:`
   - metric: `decision_gate_token_count=1`.
2. Same-SHA evidence branch token is recorded exactly once in `slice-79-implementation.md`:
   - allowed values: `evidence-complete` OR `evidence-unavailable` OR `evidence-blocked`
   - anchored line key appears exactly once: `^same_sha_evidence_token:`
   - metric: `same_sha_evidence_token_count=1`.
3. Same-SHA branch handling is explicit and mutually exclusive:
   - if token is `evidence-complete`: record CI run id + CI run URL + required-job status summary for `test`, `security`, `quality`, `governance`.
   - if token is `evidence-unavailable` or `evidence-blocked`: record inability reason + residual risk note.
4. Baseline route-fence row remains unchanged:
   - `run|logo -> route=v0, owner_slice=Slice-72, parity_status=ready` in both markdown/JSON route-fence artifacts.
5. Baseline readiness counters remain unchanged:
   - `claims/validated = 5/5` before and after implementation/audit checks.
6. No mutation to governance/runtime/test truth surfaces during implementation/audit:
   - changed-path count is zero for `project/route-fence.md`, `project/route-fence.json`, `project/parity-matrix.md`, `project/workflow-coverage-index.json`, `project/verification-contract.yml`, `.github/workflows/ci.yml`, `src/**`, `tests/**`.
7. Governance checks pass at minimum:
   - `project/scripts/verify_governance.py --check readiness`
   - `project/scripts/verify_governance.py --check parity`
   - `project/scripts/verify_governance.py --check all`.
8. Implementation mutation set/count is exact before audit/WORK_ITEMS updates:
   - `implementation_mutated_paths_count=1`
   - exact set equals `{project/v1-slices-reports/slice-79/slice-79-implementation.md}`.
9. Pre-audit WORK_ITEMS guard passes:
   - `pre_audit_work_items_changed_count=0`.
10. Post-audit WORK_ITEMS append guard passes exactly:
   - `preexisting_slice79_line_count=0`
   - `work_items_line_delta=+1`
   - `work_items_added_lines_count=1`
   - `work_items_removed_lines_count=0`
   - regex match exactly once: `^- Slice 79 -> .*next:\s*Slice 80\b.*$`
   - `slice79_work_items_next_pointer_match_count=1`.

## 6) Ordered implementation steps
1. Capture baseline proofs for `run|logo` row and readiness counters (`5/5`).
2. Create `slice-79-implementation.md` as decision-only record with no route/governance truth mutation.
3. Record exactly one `decision_gate_token` value.
4. Record exactly one `same_sha_evidence_token` value.
5. Execute same-SHA branch handling:
   - evidence-complete branch with run id/url + required-job summary, or
   - evidence-unavailable/blocked branch with inability reason + residual risk.
6. Run governance checks (`readiness`, `parity`, `all`) and capture results.
7. Prove implementation-phase mutation set/count is exact (`implementation_mutated_paths_count=1`) before audit/WORK_ITEMS updates.
8. Prove forbidden-surface no-diff guards and pre-audit `WORK_ITEMS.md` no-change guard.
9. Create `slice-79-audit.md` with explicit PASS/FAIL against all acceptance criteria.
10. After explicit audit PASS only, append one Slice 79 line to `WORK_ITEMS.md` and prove Slice 80 regex guard.

## 7) Risks/guardrails/fail-closed triggers
Risks and guardrails:
- Risk: accidental route or readiness drift while writing decision docs.
  Guardrail: fail closed unless route-fence `run|logo` and readiness `5/5` are unchanged.
- Risk: ambiguous decision/evidence state.
  Guardrail: require exactly one decision token and exactly one same-SHA evidence token.
- Risk: undocumented CI evidence branch behavior.
  Guardrail: require complete branch-specific fields (run id/url + required-job summary OR inability reason + residual risk).
- Risk: premature/malformed `WORK_ITEMS.md` update.
  Guardrail: enforce pre-audit no-change and post-audit append/regex checks.

Fail-closed triggers (any trigger => stop and do not claim completion):
- `decision_gate_token_count != 1` or token value outside allowed set.
- `same_sha_evidence_token_count != 1` or token value outside allowed set.
- Missing same-SHA branch fields for the selected evidence token.
- Any change in `run|logo` baseline row (`v0 | Slice-72 | ready`) in either route-fence artifact.
- Readiness counters differ from `5/5`.
- Any diff in forbidden governance/runtime/test surfaces.
- Governance check failure for `readiness`, `parity`, or `all`.
- `implementation_mutated_paths_count != 1` or implementation mutation set differs from `{project/v1-slices-reports/slice-79/slice-79-implementation.md}` before audit/WORK_ITEMS updates.
- `pre_audit_work_items_changed_count != 0`.
- Post-audit append guard failure, including regex mismatch for `next: Slice 80`.

## 8) Suggested next slice
- Slice 80: execute the branch selected by Slice 79 decision token.
  - If `eligible-for-flip-proposal`: proposal-only route-flip prep slice (still guarded).
  - If `conditional-no-flip` or `blocked-no-flip`: targeted evidence/remediation slice without route flip.

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

# Implementation-phase mutation set/count guard (run before audit/WORK_ITEMS updates)
$changed = @(git diff --name-only)
"implementation_mutated_paths_count=$($changed.Count)"
"implementation_mutated_paths_exact=$($changed.Count -eq 1 -and $changed[0] -eq 'project/v1-slices-reports/slice-79/slice-79-implementation.md')"

# Forbidden-surface no-mutation proofs
"route_fence_md_changed_count=$((@(git diff --name-only -- project/route-fence.md)).Count)"
"route_fence_json_changed_count=$((@(git diff --name-only -- project/route-fence.json)).Count)"
"parity_matrix_changed_count=$((@(git diff --name-only -- project/parity-matrix.md)).Count)"
"workflow_coverage_changed_count=$((@(git diff --name-only -- project/workflow-coverage-index.json)).Count)"
"verification_contract_changed_count=$((@(git diff --name-only -- project/verification-contract.yml)).Count)"
"ci_workflow_changed_count=$((@(git diff --name-only -- .github/workflows/ci.yml)).Count)"
"runtime_src_changed_count=$((@(git diff --name-only -- src)).Count)"
"tests_changed_count=$((@(git diff --name-only -- tests)).Count)"

# Token cardinality and same-SHA branch handling checks
$impl = 'project/v1-slices-reports/slice-79/slice-79-implementation.md'
$decision = Select-String -Path $impl -Pattern '^decision_gate_token:\s*(eligible-for-flip-proposal|conditional-no-flip|blocked-no-flip)\s*$'
$evidence = Select-String -Path $impl -Pattern '^same_sha_evidence_token:\s*(evidence-complete|evidence-unavailable|evidence-blocked)\s*$'
"decision_gate_token_count=$($decision.Count)"
"same_sha_evidence_token_count=$($evidence.Count)"

$evidenceToken = if ($evidence.Count -eq 1) { $evidence.Matches[0].Groups[1].Value } else { '' }
$hasRunId = (Select-String -Path $impl -Pattern '^ci_run_id:\s*\S+\s*$').Count -eq 1
$hasRunUrl = (Select-String -Path $impl -Pattern '^ci_run_url:\s*https?://\S+\s*$').Count -eq 1
$hasTest = (Select-String -Path $impl -Pattern '^required_job_test:\s*\S+\s*$').Count -eq 1
$hasSecurity = (Select-String -Path $impl -Pattern '^required_job_security:\s*\S+\s*$').Count -eq 1
$hasQuality = (Select-String -Path $impl -Pattern '^required_job_quality:\s*\S+\s*$').Count -eq 1
$hasGovernance = (Select-String -Path $impl -Pattern '^required_job_governance:\s*\S+\s*$').Count -eq 1
$hasReason = (Select-String -Path $impl -Pattern '^same_sha_inability_reason:\s*.+$').Count -eq 1
$hasResidual = (Select-String -Path $impl -Pattern '^residual_risk_note:\s*.+$').Count -eq 1

$branchOk = $false
if ($evidenceToken -eq 'evidence-complete') {
  $branchOk = $hasRunId -and $hasRunUrl -and $hasTest -and $hasSecurity -and $hasQuality -and $hasGovernance
}
if ($evidenceToken -eq 'evidence-unavailable' -or $evidenceToken -eq 'evidence-blocked') {
  $branchOk = $hasReason -and $hasResidual
}
"same_sha_branch_fields_ok=$branchOk"

# WORK_ITEMS guards
"pre_audit_work_items_changed_count=$((@(git diff --name-only -- WORK_ITEMS.md)).Count)"
"preexisting_slice79_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 79 -> ').Count)"
$beforeCount = (Get-Content WORK_ITEMS.md).Count
# ...append exactly one Slice 79 line after audit PASS...
$afterCount = (Get-Content WORK_ITEMS.md).Count
"work_items_line_delta=$('{0:+#;-#;0}' -f ($afterCount - $beforeCount))"
$wDiff = git diff --unified=0 -- WORK_ITEMS.md
"work_items_added_lines_count=$((($wDiff | Select-String -Pattern '^\+[^+]').Matches.Count))"
"work_items_removed_lines_count=$((($wDiff | Select-String -Pattern '^\-[^-]').Matches.Count))"
"slice79_work_items_next_pointer_match_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 79 -> .*next:\s*Slice 80\b.*$').Count)"
```

## 10) Evidence/report paths
- Plan: `project/v1-slices-reports/slice-79/slice-79-plan.md`
- Implementation report: `project/v1-slices-reports/slice-79/slice-79-implementation.md`
- Audit report: `project/v1-slices-reports/slice-79/slice-79-audit.md`
- Baseline invariant proof surfaces:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - governance readiness output from `project/scripts/verify_governance.py --check readiness`
- Post-audit orchestration target:
  - `WORK_ITEMS.md`

## 11) Split-if-too-large rule
Split immediately if any non-documentation mutation becomes necessary beyond Slice 79 artifacts and post-audit one-line `WORK_ITEMS.md` append.

If split is triggered:
- Keep Slice 79 strictly decision-only (tokenized decision + same-SHA branch evidence handling).
- Defer all route/progression/governance/runtime/test changes to Slice 80+.
