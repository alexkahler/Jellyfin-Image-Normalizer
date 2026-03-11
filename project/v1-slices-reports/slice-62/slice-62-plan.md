# Slice 62 Plan v3 (Final) - Same-SHA CI Evidence Remediation for `config_init|n/a` (Evidence-Only, No Route Mutation)

Date: 2026-03-11  
Branch: feat/v1-overhaul  
Local SHA: 5dd2bb82be967463b32e088bf374df4d52a9707c

## Slice ID/title
- Slice 62
- Same-SHA CI evidence remediation for `config_init|n/a` progression (evidence-only, no route mutation)

## Goal/objective
- Remediate the unresolved same-SHA CI evidence branch from Slice 61 for `config_init|n/a` and record a complete, fail-closed outcome.
- Preserve governance truth for target row unchanged:
  - `command=config_init`, `mode=n/a`, `route=v0`, `owner_slice=Slice-57`, `parity_status=ready`
- Keep scope small and bounded to avoid context rot: evidence capture and report artifacts only.

## Planning worker boundary (this turn)
- Planning worker writes only `project/v1-slices-reports/slice-62/slice-62-plan.md`.
- Planning worker does not edit `WORK_ITEMS.md`.

## Worker responsibility split (execution phase)
- Implementation worker:
  - writes only `project/v1-slices-reports/slice-62/slice-62-implementation.md`
  - collects/records evidence only; must not mutate governance-truth/runtime/test artifacts
- Audit worker:
  - writes only `project/v1-slices-reports/slice-62/slice-62-audit.md`
  - performs independent PASS/FAIL validation of evidence completeness and no-mutation scope
- Orchestration thread only:
  - may update `WORK_ITEMS.md` only after explicit Slice 62 audit PASS

## Baseline snapshot (planning time)
- Prior slice state: Slice 61 completed decision-only with `decision_gate: conditional-no-flip` for `config_init|n/a`.
- Current target row remains:
  - `command=config_init`, `mode=n/a`, `route=v0`, `owner_slice=Slice-57`, `parity_status=ready`
- Mandatory scope intent for this slice:
  - remediate same-SHA evidence branch and record outcome
  - no route-fence/parity/workflow/verification-contract/CI/runtime/test mutation
  - no route flip

## In-scope
- Evidence collection and reporting for same-SHA CI closure fields:
  - local SHA
  - workflow identity
  - CI run id/url when same-SHA run exists
  - per-required-job summary for `test`, `security`, `quality`, `governance`
- Explicit fail-closed branch outcome recording:
  - evidence-complete branch (same-SHA run exists with required-job summary), or
  - inability branch (explicit inability reason + residual risk, no implied validation)
- Slice report artifacts only:
  - `project/v1-slices-reports/slice-62/slice-62-plan.md`
  - `project/v1-slices-reports/slice-62/slice-62-implementation.md`
  - `project/v1-slices-reports/slice-62/slice-62-audit.md`

## Out-of-scope
- Any mutation to governance-truth artifacts:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
- Any runtime/test mutation under `src/` or `tests/`
- Any route flip proposal or route mutation (`v0 -> v1`) for any row
- Any `WORK_ITEMS.md` edit during planning/implementation/audit phases

## Acceptance criteria
1. Slice 62 remains evidence-only/documentation-only with no governance-truth mutation.
2. Target is only `config_init|n/a`; baseline row remains unchanged (`v0`, `Slice-57`, `ready`).
3. Same-SHA evidence branch is explicit and unambiguous.
4. Exactly one standardized decision outcome token is recorded in implementation evidence:
   - `decision_gate: eligible-for-flip-proposal`
   - `decision_gate: conditional-no-flip`
   - `decision_gate: blocked-no-flip`
5. When same-SHA run exists, implementation records run id/url and per-required-job statuses for `test`, `security`, `quality`, `governance`.
6. When same-SHA run is unavailable/incomplete, implementation records explicit inability reason and residual risk, with no implied same-SHA validation.
7. Protected-file diff proof is empty for governance-truth artifacts and `WORK_ITEMS.md`.
8. Governance checks pass: `--check readiness`, `--check parity`, `--check all`.
9. Readiness remains `4/4` with explicit proof lines:
   - `INFO: Route readiness claims: 4`
   - `INFO: Route readiness claims validated: 4`
10. Implementation and audit reports exist; audit is explicit PASS before any orchestration-thread update.

## Binary Success Condition
Slice 62 is successful only if it produces a complete same-SHA CI evidence outcome record for `config_init|n/a` (either evidence-complete or inability+residual-risk branch), preserves all governance truth unchanged, passes required governance checks, and receives explicit audit PASS before any `WORK_ITEMS.md` update.

## Fail-close criteria
- Any governance-truth mutation (`route-fence`, parity/workflow/verification-contract/CI artifacts).
- Any runtime/test mutation.
- Ambiguous or missing same-SHA branch outcome.
- Same-SHA run exists but required-job summary for `test`, `security`, `quality`, `governance` is missing or ambiguous.
- Missing Slice 62 audit report or audit not explicit PASS.
- Any `WORK_ITEMS.md` mutation before explicit audit PASS.

## Implementation steps
1. Capture local SHA and workflow identity; restate required jobs (`test`, `security`, `quality`, `governance`).
2. Reconfirm baseline row from `project/route-fence.md` and `project/route-fence.json` (read-only proof).
3. Attempt same-SHA evidence via `gh` branch.
4. Attempt REST fallback when `gh` is unavailable or insufficient.
5. Record exactly one explicit outcome branch:
   - evidence-complete, or
   - inability+residual-risk.
6. Capture protected-file diff proof showing no out-of-scope mutation.
7. Run governance checks (`readiness`, `parity`, `all`) and record outputs.
8. Write `slice-62-implementation.md`; hand off for independent audit in `slice-62-audit.md`.

## Minimum evidence commands (PowerShell)
```powershell
# Local SHA + required jobs
$sha = (git rev-parse HEAD).Trim()
"local_sha=$sha"
$requiredJobs = @('test','security','quality','governance')

# Baseline row proof (must remain unchanged)
Select-String -Path project/route-fence.md -Pattern '^\|\s*config_init\s*\|\s*n/a\s*\|'
$rf = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rf.rows |
  Where-Object { $_.command -eq 'config_init' -and $_.mode -eq 'n/a' } |
  Format-List command, mode, route, owner_slice, parity_status

# Same-SHA CI evidence attempt: gh branch
$ghAvailable = $true
try {
  $ghRuns = gh run list --limit 200 --json databaseId,headSha,workflowName,url,status,conclusion | ConvertFrom-Json
  $ghSameSha = @($ghRuns | Where-Object { $_.headSha -eq $sha })
  "gh_same_sha_total_runs=$($ghSameSha.Count)"
  $ghCandidateRun = $ghSameSha | Select-Object -First 1
  if ($ghCandidateRun) {
    "gh_candidate_run_id=$($ghCandidateRun.databaseId)"
    "gh_candidate_workflow=$($ghCandidateRun.workflowName)"
    "gh_candidate_url=$($ghCandidateRun.url)"

    # Per-required-job summary path when run exists
    $ghRunView = gh run view $ghCandidateRun.databaseId --json jobs | ConvertFrom-Json
    $ghRunView.jobs |
      Where-Object { $requiredJobs -contains $_.name } |
      Select-Object name, status, conclusion, startedAt, completedAt
  }
} catch {
  $ghAvailable = $false
  "gh_unavailable_reason=$($_.Exception.Message)"
}

# REST fallback branch (when gh unavailable/insufficient)
$origin = (git config --get remote.origin.url).Trim()
if ($origin -notmatch 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/.]+)(?:\.git)?$') {
  throw "Unable to parse GitHub owner/repo from remote.origin.url: $origin"
}
$owner = $Matches.owner
$repo = $Matches.repo
$headers = @{ Accept = 'application/vnd.github+json' }
if ($env:GITHUB_TOKEN) {
  $headers.Authorization = "Bearer $($env:GITHUB_TOKEN)"
}
$uri = "https://api.github.com/repos/$owner/$repo/actions/runs?head_sha=$sha&per_page=100"
$rest = Invoke-RestMethod -Method Get -Uri $uri -Headers $headers
"rest_same_sha_total_runs=$($rest.total_count)"
$restSameSha = @($rest.workflow_runs | Where-Object { $_.head_sha -eq $sha })
$restSameSha |
  Select-Object id, name, head_sha, status, conclusion, html_url
$restCandidateRun = $restSameSha | Select-Object -First 1
if ($restCandidateRun) {
  "rest_candidate_run_id=$($restCandidateRun.id)"
  "rest_candidate_workflow=$($restCandidateRun.name)"
  "rest_candidate_url=$($restCandidateRun.html_url)"

  # Per-required-job summary path when run exists
  $jobsUri = "https://api.github.com/repos/$owner/$repo/actions/runs/$($restCandidateRun.id)/jobs?per_page=100"
  $restJobs = Invoke-RestMethod -Method Get -Uri $jobsUri -Headers $headers
  $restJobs.jobs |
    Where-Object { $requiredJobs -contains $_.name } |
    Select-Object name, status, conclusion, html_url
}

# Protected-file diff checks (must be empty)
git diff --name-only
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml WORK_ITEMS.md

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

Expected proof points:
- Baseline row remains `config_init|n/a -> v0 | Slice-57 | ready` in both route-fence artifacts.
- Same-SHA evidence branch is explicit:
  - `gh` branch yields same-SHA run evidence, or explicit `gh_unavailable_reason`.
  - REST fallback yields same-SHA run evidence or explicit `rest_same_sha_total_runs=0`.
- When same-SHA run exists (via either branch), proof includes per-required-job summary for `test`, `security`, `quality`, `governance` with unambiguous status/conclusion.
- Protected-file diff checks are empty for governance-truth artifacts and `WORK_ITEMS.md`.
- Governance checks pass for `readiness`, `parity`, and `all`.

## Risk/guardrails
- Risk: accidental route/progression mutation while performing evidence work.
  Guardrail: fail closed on any governance-truth/runtime/test mutation.
- Risk: incomplete or unclear same-SHA evidence reporting.
  Guardrail: require exactly one explicit branch outcome with complete supporting evidence.
- Risk: scope creep.
  Guardrail: keep writable scope to Slice 62 report artifacts only.

## Suggested next slice
- Slice 63 progression fork based on Slice 62 audited evidence outcome:
  - if same-SHA evidence is complete and required jobs pass, route-progression proposal slice for `config_init|n/a`
  - if same-SHA evidence remains unavailable/incomplete, additional evidence-remediation slice (no route mutation)

## Explicit split rule if scope grows
- Stop and split immediately if any of the following becomes necessary:
  - editing route-fence/parity/workflow/verification-contract/CI artifacts
  - editing runtime or test files
  - handling more than one route row
  - performing tooling/auth setup beyond evidence capture/reporting
- Keep Slice 62 limited to one objective: same-SHA CI evidence remediation and outcome recording for `config_init|n/a`, with no route flip and no governance-truth mutation.
