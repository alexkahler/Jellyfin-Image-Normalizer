# Slice 24 Plan

## Slice Id and Title
- Slice id: `A-08`
- Slice title: `Same-SHA CI proof + GG-008 gate`

## Objective
Close GG-008 using evidence-only same-SHA CI proof for the current local HEAD, with no runtime behavior changes.

## In-Scope / Out-of-Scope
- In scope: local SHA capture, local governance gate confirmation, GitHub Actions REST API evidence retrieval, validation, and recording of same-SHA CI proof.
- In scope: machine-readable evidence capture and slice audit documentation.
- Out of scope: runtime code refactors, architecture redesign, route-fence changes, CLI/config semantic changes, speculative cleanup.

## Target Files
- `project/v1-slices-reports/slice-24/slice-24-plan.md`
- `project/v1-slices-reports/slice-24/slice-24-audit.md`
- `project/v1-slices-reports/slice-24/a08-ci-evidence.json` (new, machine-readable evidence artifact)
- `WORK_ITEMS.md` (status synchronization only, if needed)

## Public Interfaces Affected
- None expected.
- A-08 is governance evidence only; no `src/` runtime interface changes.

## Acceptance Criteria
- Local `commit_sha` is captured from current HEAD.
- Local `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` passes on that exact SHA.
- GitHub Actions evidence identifies workflow `.github/workflows/ci.yml` (workflow `CI`) for the same `head_sha`.
- Required jobs `test`, `security`, `quality`, `governance` are present and all `success`.
- Evidence table includes: run URL, run ID, workflow identity, head SHA, and per-job conclusions.
- If any required element is missing/ambiguous, result is explicitly `insufficient evidence`, GG-008 remains open, Theme A remains open.
- No runtime behavior changes are introduced.

## Exact Verification Commands
```powershell
# 1) Capture local HEAD SHA
$sha = (git rev-parse HEAD).Trim()
$sha

# 2) Prove local governance gate passes on same SHA
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

# 3) Query GitHub Actions runs for same SHA using REST API fallback (gh unavailable)
$repo = "alexkahler/Jellyfin-Image-Normalizer"
$headers = @{
  Accept = "application/vnd.github+json"
  "X-GitHub-Api-Version" = "2022-11-28"
  "User-Agent" = "jfin-a08-evidence"
}
$runs = Invoke-RestMethod -Headers $headers -Method Get -Uri "https://api.github.com/repos/$repo/actions/runs?head_sha=$sha&per_page=50"

# 4) Select canonical CI workflow run
$ciRuns = @($runs.workflow_runs | Where-Object {
  ($_.name -eq "CI" -or $_.path -eq ".github/workflows/ci.yml")
})
$ciRuns | Select-Object id,name,path,head_sha,status,conclusion,html_url,run_number,created_at,updated_at

# 5) Choose target run (prefer completed run for same SHA)
$run = $ciRuns | Where-Object { $_.head_sha -eq $sha -and $_.status -eq "completed" } | Select-Object -First 1
if (-not $run) { throw "No completed CI run found for same SHA." }

# 6) Pull job-level conclusions
$jobsResp = Invoke-RestMethod -Headers $headers -Method Get -Uri "https://api.github.com/repos/$repo/actions/runs/$($run.id)/jobs?per_page=100"
$jobsResp.jobs | Select-Object id,name,conclusion,status,html_url,started_at,completed_at

# 7) Validate required jobs
$required = @("test","security","quality","governance")
$jobMap = @{}
foreach ($name in $required) {
  $match = $jobsResp.jobs | Where-Object { $_.name -eq $name } | Select-Object -First 1
  $jobMap[$name] = $match
}
$required | ForEach-Object {
  [PSCustomObject]@{
    job = $_
    present = ($null -ne $jobMap[$_])
    conclusion = if ($null -ne $jobMap[$_]) { $jobMap[$_].conclusion } else { $null }
  }
}

# 8) Write machine-readable evidence artifact
$evidence = [PSCustomObject]@{
  local_head_sha = $sha
  local_verify_governance_check_all = "pass"
  workflow = [PSCustomObject]@{
    name = $run.name
    path = $run.path
    run_id = $run.id
    run_url = $run.html_url
    head_sha = $run.head_sha
    status = $run.status
    conclusion = $run.conclusion
  }
  required_jobs = $required | ForEach-Object {
    [PSCustomObject]@{
      name = $_
      present = ($null -ne $jobMap[$_])
      conclusion = if ($null -ne $jobMap[$_]) { $jobMap[$_].conclusion } else { $null }
      url = if ($null -ne $jobMap[$_]) { $jobMap[$_].html_url } else { $null }
    }
  }
}
$evidence | ConvertTo-Json -Depth 8 | Set-Content project/v1-slices-reports/slice-24/a08-ci-evidence.json

# 9) Source diff sanity (A-08 should remain evidence-only for src)
git diff --numstat -- src
```

## Rollback Step
- Revert the A-08 evidence commit and remove/re-mark invalid same-SHA closure claims if any evidence element is later proven incorrect.
- Command form: `git revert <A-08 commit>`.

## Behavior-Preservation Statement
A-08 is evidence-only governance closure work. No intended runtime behavior change and no `src/` logic modification.

## Implementation Steps
1. Capture local HEAD SHA.
2. Run `verify_governance.py --check all` on current HEAD and record pass/fail.
3. Use GitHub REST API to retrieve Actions runs for the same SHA.
4. Identify canonical CI workflow run (`CI` / `.github/workflows/ci.yml`) for that SHA.
5. Retrieve job details for the selected run and validate required jobs (`test`, `security`, `quality`, `governance`) are all successful.
6. Save machine-readable evidence (`a08-ci-evidence.json`) and summarize as table in audit.
7. If any criterion fails or is ambiguous, mark A-08 `insufficient evidence` and keep Theme A open.
8. If all criteria pass, mark A-08 closure recommendation in audit and sync `WORK_ITEMS.md` status.

## Risks / Guardrails
- Risk: missing/ambiguous CI run for same SHA.
- Guardrail: explicitly require exact SHA match and canonical workflow identity.
- Risk: required jobs not present or differently named.
- Guardrail: fail closed (`insufficient evidence`) unless required jobs are unambiguously present and successful.
- Risk: API rate limit or transient GitHub API failure.
- Guardrail: record failure as evidence gap; do not fabricate closure.
- Risk: scope creep into runtime changes.
- Guardrail: keep A-08 to governance evidence artifacts only.

## Expected Commit Title
`a-08: same-sha ci proof + gg-008 gate`

## Execution Status
- Status: `blocked` (as of `2026-03-08`)
- Blocker: canonical same-SHA CI run now exists for local HEAD `7e837f93826e44b3a0a955a7fab2a956192dd58a`, but required job `quality` failed (`Run ruff format check`).
- Next required condition: rerun canonical workflow `.github/workflows/ci.yml` (`CI`) on a closure SHA where `test`, `security`, `quality`, and `governance` all conclude `success`.
