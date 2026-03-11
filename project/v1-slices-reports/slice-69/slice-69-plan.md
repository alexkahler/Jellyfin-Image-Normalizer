# Slice 69 Plan v3 (Final) - Post-Unblock Same-SHA CI Evidence Collection + Decision Posture for `config_init|n/a`

Date: 2026-03-11  
Branch: `feat/v1-overhaul`  
Planning review status: v3 final.

## 1) Slice ID and Title
- Slice 69
- Post-unblock same-SHA CI evidence collection on a post-unblock SHA (push + run-id/job-status capture) for `config_init|n/a`

## 2) Goal / Objective
Single objective only: collect same-SHA CI evidence for a post-unblock SHA and record fail-closed decision posture for `config_init|n/a` with deterministic run selection and marker consistency proof.

## 3) In-Scope / Out-of-Scope
### In scope
- Capture local post-unblock SHA (`git rev-parse HEAD`) as target SHA.
- Push branch state to `origin/feat/v1-overhaul` and record push outcome.
- Query same-SHA workflow runs for exact `head_sha=<target_sha>`.
- Select deterministic candidate run (latest matching `CI` run by `created_at` descending, tie-break by `id` descending) and record selection rule + selected metadata.
- Capture run id/url and required job outcomes for `test`, `security`, `quality`, `governance`.
- Poll boundedly for job terminality; fail closed if terminal evidence is not complete by timeout.
- Record exactly one `same_sha_branch` and one `decision_gate`, with uniqueness counters.
- Produce slice reports (`plan`, `implementation`, `audit`).

### Out of scope
- Any mutation of route-fence/parity/workflow/verification contract truth:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
- Any runtime/test source changes under `src/` or `tests/`.
- Any route mutation (`v0 -> v1`) in this slice.
- Any objective other than same-SHA evidence collection + decision posture recording for `config_init|n/a`.

## 4) Tight Writable File Allowlist by Role
- Planning worker: `project/v1-slices-reports/slice-69/slice-69-plan.md` only.
- Implementation worker: `project/v1-slices-reports/slice-69/slice-69-implementation.md` only.
- Audit worker: `project/v1-slices-reports/slice-69/slice-69-audit.md` only.
- Orchestrator only (after explicit audit PASS): `WORK_ITEMS.md` only.

## 5) Acceptance Criteria (Measurable)
1. Implementation report records one target SHA from `git rev-parse HEAD` and one push outcome for `feat/v1-overhaul`.
2. Push publication proof is recorded after push:
   - `remote_branch_sha=<sha from git ls-remote origin feat/v1-overhaul>`
   - `push_target_sha_match=true` only when `remote_branch_sha == target_sha`.
3. Same-SHA run query evidence is recorded for exact `head_sha=<target_sha>` and workflow identity `CI`.
4. Run selection rule is recorded explicitly as deterministic (`latest CI run by created_at desc, id desc tie-break`) with candidate count and selected run metadata (`id`, `html_url`, `created_at`, `status`, `conclusion`).
5. `same_sha_branch: evidence-complete` is used only when both are true:
   - selected same-SHA `CI` run id/url exists, and
   - all required jobs (`test`, `security`, `quality`, `governance`) are present with terminal conclusions captured.
6. If selected run exists but required jobs are non-terminal/in-progress at polling timeout, outcome is fail-closed and must not be `eligible-for-flip-proposal`.
7. If push publication is not proven (`push_target_sha_match=false` or unavailable), outcome is fail-closed with `same_sha_branch: blocked-external` and `decision_gate: blocked-no-flip`; no eligibility path is allowed.
8. Implementation report contains an explicit `## Terminal Decision Rationale` section mapping captured evidence to the final marker pair.
9. Implementation report contains exactly one terminal `same_sha_branch` and exactly one `decision_gate`.
10. No duplicate or legacy marker lines remain anywhere else in the report:
   - exactly one `^same_sha_branch:` line total,
   - exactly one `^decision_gate:` line total.
11. Uniqueness proof counters are present and exact:
   - `same_sha_branch_match_count=1`
   - `decision_token_match_count=1`
12. Marker values are from allowed sets and match Section 7 decision policy.
13. Protected-file no-mutation proof is explicit for out-of-scope governance truth files and `WORK_ITEMS.md`.
14. Governance checks pass: `--check readiness`, `--check parity`, and `--check all`.
15. Audit report gives explicit PASS before any `WORK_ITEMS.md` update.

## 6) Implementation Steps (Ordered)
1. Capture target SHA (`git rev-parse HEAD`) and required job list (`test/security/quality/governance`).
2. Capture unchanged baseline row proof for `config_init|n/a` from route-fence markdown and JSON.
3. Execute `git push origin feat/v1-overhaul` and record result.
4. Capture push publication proof via `git ls-remote origin feat/v1-overhaul`; record `remote_branch_sha` and `push_target_sha_match`.
5. If push fails or publication proof does not match target SHA, record blocked-external terminal outcome and stop eligibility evaluation.
6. Poll GitHub Actions runs for exact `head_sha=<target_sha>`.
7. Per poll attempt, build deterministic `CI` candidate set (exact SHA + workflow name `CI`), sorted by `created_at desc`, then `id desc`; record selection rule and candidate count.
8. Select first candidate from sorted set and record selected run metadata; if no candidate by timeout, record fail-closed evidence-unavailable branch.
9. If selected run exists, poll selected run jobs up to bounded timeout; on each attempt, evaluate:
   - required-job presence (all 4 names present),
   - required-job terminality (each required job has terminal conclusion).
10. If required-job evidence becomes complete, derive marker pair per Section 7.
11. If required jobs remain non-terminal at timeout, or workflow/run selection is ambiguous, fail close and record non-eligible decision.
12. Record exactly one marker pair and one `## Terminal Decision Rationale` mapping evidence -> markers.
13. Record marker uniqueness proof counters and total marker-line counts.
14. Record protected-file no-mutation diff proof.
15. Run governance checks (`readiness`, `parity`, `all`) and record outputs.
16. Write `slice-69-implementation.md` and hand off to audit.

## 7) Risk / Guardrails and Fail-Closed Triggers
Decision marker policy (mandatory):
- Allowed `same_sha_branch` values: `evidence-complete`, `blocked-external`.
- Allowed `decision_gate` values: `eligible-for-flip-proposal`, `blocked-no-flip`.
- Marker mapping rules:
  - `same_sha_branch: evidence-complete` is valid only when push publication proof is true (`push_target_sha_match=true`), selected same-SHA `CI` run id/url exists, and all 4 required jobs are present with terminal conclusions.
  - `same_sha_branch: evidence-complete` + `decision_gate: eligible-for-flip-proposal` only when all required jobs conclude `success`.
  - `same_sha_branch: evidence-complete` + `decision_gate: blocked-no-flip` when required jobs are terminal but one or more are non-success.
  - `same_sha_branch: blocked-external` + `decision_gate: blocked-no-flip` when push/publication fails, when no deterministic same-SHA `CI` candidate is available by timeout, or when terminal evidence cannot be completed externally within bounds.
- Exactly one of each marker must be present with:
  - `same_sha_branch_match_count=1`
  - `decision_token_match_count=1`

Fail-closed triggers:
- Duplicate, missing, ambiguous, or legacy marker lines.
- Marker pair inconsistent with evidence availability or required-job outcomes.
- Same-SHA run found but required job set incomplete (missing any of `test/security/quality/governance`).
- Same-SHA run found but required jobs still non-terminal at polling timeout.
- Push failed, or publication proof missing/mismatched (`push_target_sha_match` not true).
- Workflow name mismatch (`CI` not matched) or ambiguous candidate-run selection.
- Any implied same-SHA validation without run id/url + required-job completeness/terminality evidence.
- Any mutation to out-of-scope route-fence/parity/workflow/verification/CI contract files.
- Any runtime/test source change.
- Governance check failure or missing audit PASS.

## 8) Suggested Next Slice
- Slice 70 (conditional on Slice 69 outcome):
  - If `decision_gate: eligible-for-flip-proposal`: one-row progression proposal slice for `config_init|n/a` (`v0 -> v1`) with explicit approval gate.
  - If `decision_gate: blocked-no-flip`: focused blocker-remediation slice (external CI availability, workflow execution timing, or required-job failure remediation) before any re-attempt.

## 9) Verification Commands (PowerShell)
```powershell
$targetSha = (git rev-parse HEAD).Trim()
$requiredJobs = @('test','security','quality','governance')
$terminalConclusions = @('success','failure','cancelled','skipped','timed_out','action_required','neutral','startup_failure','stale')
"target_sha=$targetSha"

# Baseline unchanged proof for target row
Select-String -Path project/route-fence.md -Pattern '^\|\s*config_init\s*\|\s*n/a\s*\|'
$rf = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rf.rows | Where-Object { $_.command -eq 'config_init' -and $_.mode -eq 'n/a' } |
  Select-Object command, mode, route, owner_slice, parity_status

# Push post-unblock SHA
git push origin feat/v1-overhaul

# Push publication proof for target SHA on remote branch
$remoteLine = (git ls-remote origin feat/v1-overhaul | Select-Object -First 1)
if ([string]::IsNullOrWhiteSpace($remoteLine)) { throw "Unable to resolve remote ref for origin/feat/v1-overhaul" }
$remoteBranchSha = ($remoteLine -split '\s+')[0].Trim()
$pushTargetShaMatch = ($remoteBranchSha -eq $targetSha)
"remote_branch_sha=$remoteBranchSha"
"push_target_sha_match=$pushTargetShaMatch"

# Same-SHA query and deterministic run selection
$origin = (git config --get remote.origin.url).Trim()
if ($origin -notmatch 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/.]+)(?:\.git)?$') { throw "Unable to parse GitHub remote: $origin" }
$owner = $Matches.owner
$repo = $Matches.repo
$headers = @{ Accept = 'application/vnd.github+json' }
if ($env:GITHUB_TOKEN) { $headers.Authorization = "Bearer $($env:GITHUB_TOKEN)" }

$selectionRule = 'latest_CI_run_for_exact_head_sha_sorted_created_at_desc_then_id_desc'
"selection_rule=$selectionRule"
$selectedRun = $null
if ($pushTargetShaMatch) {
  for ($i = 1; $i -le 20; $i++) {
    $runsUri = "https://api.github.com/repos/$owner/$repo/actions/runs?head_sha=$targetSha&per_page=100"
    $runs = Invoke-RestMethod -Method Get -Uri $runsUri -Headers $headers
    $candidates = @(
      $runs.workflow_runs |
        Where-Object { $_.head_sha -eq $targetSha -and $_.name -eq 'CI' } |
        Sort-Object -Property @{ Expression = { [datetime]$_.created_at }; Descending = $true },
                              @{ Expression = { [int64]$_.id }; Descending = $true }
    )
    "poll_attempt=$i same_sha_total_runs=$($runs.total_count) ci_candidate_count=$($candidates.Count)"
    if ($candidates.Count -gt 0) {
      $selectedRun = $candidates[0]
      "selected_run_id=$($selectedRun.id)"
      "selected_run_url=$($selectedRun.html_url)"
      "selected_run_created_at=$($selectedRun.created_at)"
      "selected_run_status=$($selectedRun.status)"
      "selected_run_conclusion=$($selectedRun.conclusion)"
      break
    }
    Start-Sleep -Seconds 30
  }
} else {
  "same_sha_query_skipped_due_to_push_publication_mismatch=true"
}

# Required-job presence + terminality checks for selected run
if ($selectedRun) {
  $jobRows = @()
  for ($j = 1; $j -le 20; $j++) {
    $jobsUri = "https://api.github.com/repos/$owner/$repo/actions/runs/$($selectedRun.id)/jobs?per_page=100"
    $jobs = Invoke-RestMethod -Method Get -Uri $jobsUri -Headers $headers
    $jobRows = @(
      $jobs.jobs |
        Where-Object { $requiredJobs -contains $_.name } |
        Select-Object name, status, conclusion, html_url
    )
    $present = @($jobRows.name | Sort-Object -Unique)
    $missing = @($requiredJobs | Where-Object { $_ -notin $present })
    $nonTerminal = @(
      $jobRows |
        Where-Object { $_.status -ne 'completed' -or [string]::IsNullOrWhiteSpace($_.conclusion) -or $_.conclusion -notin $terminalConclusions }
    )
    "jobs_poll_attempt=$j required_jobs_present_count=$($present.Count) required_jobs_missing_count=$($missing.Count) required_jobs_non_terminal_count=$($nonTerminal.Count)"
    if ($missing.Count -eq 0 -and $nonTerminal.Count -eq 0) { break }
    Start-Sleep -Seconds 30
  }
  "required_jobs_present=$([string]::Join(',', $present))"
  "required_jobs_missing=$([string]::Join(',', $missing))"
  "required_jobs_non_terminal_count=$($nonTerminal.Count)"
  $jobRows
} else {
  "same_sha_ci_candidate_unavailable=true"
}

# Marker uniqueness and no-legacy-marker proof
$impl = 'project/v1-slices-reports/slice-69/slice-69-implementation.md'
$decisionAllowed = Select-String -Path $impl -Pattern '^decision_gate:\s*(eligible-for-flip-proposal|blocked-no-flip)\s*$'
$branchAllowed = Select-String -Path $impl -Pattern '^same_sha_branch:\s*(evidence-complete|blocked-external)\s*$'
$decisionAny = Select-String -Path $impl -Pattern '^decision_gate:\s*'
$branchAny = Select-String -Path $impl -Pattern '^same_sha_branch:\s*'
"decision_token_match_count=$($decisionAllowed.Count)"
"same_sha_branch_match_count=$($branchAllowed.Count)"
"decision_gate_any_count=$($decisionAny.Count)"
"same_sha_branch_any_count=$($branchAny.Count)"

# Scope/diff proof
git diff --name-only
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml src tests WORK_ITEMS.md

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

## 10) Evidence / Report Output Paths
- Plan: `project/v1-slices-reports/slice-69/slice-69-plan.md`
- Implementation report: `project/v1-slices-reports/slice-69/slice-69-implementation.md`
- Audit report: `project/v1-slices-reports/slice-69/slice-69-audit.md`

## 11) Split-if-too-large Rule
Stop and split immediately if any of these occur:
- Work expands beyond single objective (same-SHA evidence collection + decision posture for `config_init|n/a`).
- Any out-of-scope governance truth mutation becomes necessary.
- Any runtime/test source edit becomes necessary.
- External prerequisites beyond bounded evidence collection are required (for example, permissions/infrastructure remediation).

If split is triggered, keep Slice 69 as evidence attempt + terminal fail-closed record only, and defer remediation to a dedicated follow-on prerequisite slice.
