# Slice 61 Plan v3 (Final) - Route-Progression Decision Record for `config_init|n/a` (Decision-Only, No Flip, No Governance-Truth Mutation)

Date: 2026-03-11  
Branch: feat/v1-overhaul  
Local SHA: 534d0f78131ac6f6c0294b57ea5be4e373ce9ed6

## Slice ID/title
- Slice 61
- Route-progression decision record for `config_init|n/a` (decision-only, no route flip)

## Goal/objective
- Produce a bounded progression decision record after Slice 60 readiness activation.
- Preserve current governance truth for target row:
  - `command=config_init`, `mode=n/a`, `route=v0`, `owner_slice=Slice-57`, `parity_status=ready`
- Define explicit progression decision-gating required before any later `v0 -> v1` proposal.
- Keep this slice documentation-only and context-rot resistant (single objective, explicit fail-close conditions).

## Planning worker boundary (this turn)
- Planning worker writes only `project/v1-slices-reports/slice-61/slice-61-plan.md`.
- Planning worker does not edit `WORK_ITEMS.md`.

## Worker responsibility split (execution phase)
- Implementation worker:
  - may write only `project/v1-slices-reports/slice-61/slice-61-implementation.md`
  - may collect evidence only; must not mutate governance truth artifacts
- Audit worker:
  - may write only `project/v1-slices-reports/slice-61/slice-61-audit.md`
  - performs independent PASS/FAIL validation of decision-gate evidence and no-mutation proof
- Orchestration thread only:
  - may update `WORK_ITEMS.md` only after explicit Slice 61 audit PASS

## Baseline snapshot (planning time)
- Completed through Slice 60.
- Current target row:
  - `config_init|n/a -> route=v0, owner_slice=Slice-57, parity_status=ready`
- Current readiness counters:
  - `claimed_rows=4`, `validated_rows=4` (from `verify_governance.py --check readiness`)
- Same-SHA CI evidence status for this local SHA is unresolved at plan time and must be explicitly resolved in execution evidence.

## In-scope files (Slice 61 execution)
- `project/v1-slices-reports/slice-61/slice-61-plan.md`
- `project/v1-slices-reports/slice-61/slice-61-implementation.md`
- `project/v1-slices-reports/slice-61/slice-61-audit.md`
- `WORK_ITEMS.md` (orchestration-thread-only, post-audit PASS)

## Out-of-scope files/work
- `project/route-fence.md`
- `project/route-fence.json`
- `project/parity-matrix.md`
- `project/workflow-coverage-index.json`
- `project/verification-contract.yml`
- `.github/workflows/ci.yml`
- `AGENTS.md`
- any runtime code under `src/`
- any tests under `tests/`
- any route/parity/owner mutation for any row
- any `WORK_ITEMS.md` update before explicit audit PASS

## Progression decision-gating (explicit, fail-closed)
Required gating inputs for any later route-flip proposal:
1. Baseline remains unchanged for `config_init|n/a`: `route=v0`, `owner_slice=Slice-57`, `parity_status=ready`.
2. Same-SHA CI evidence for local SHA is explicitly resolved using required closure fields:
   - local SHA
   - workflow identity
   - CI run id/url when same-SHA evidence exists
   - required-job status summary for `test`, `security`, `quality`, `governance`
3. Local governance checks pass for decision integrity (`--check readiness`, `--check parity`, `--check all`).

Decision-gate outcomes (execution must select exactly one):
- `decision_gate: eligible-for-flip-proposal`
  - only if same-SHA run evidence exists for local SHA and required jobs are PASS/green
  - this slice still performs no route mutation; it only authorizes later flip proposal planning
- `decision_gate: conditional-no-flip`
  - if same-SHA evidence cannot be obtained
  - must include explicit inability reason and residual-risk statement
- `decision_gate: blocked-no-flip`
  - if same-SHA evidence exists but one or more required jobs are missing/non-passing, or baseline drift is detected
  - must list blockers and required remediation before any flip proposal

## Acceptance criteria
1. Slice 61 remains decision-only/documentation-only with no governance-truth mutation.
2. Decision record targets only `config_init|n/a`.
3. Exactly one decision gate outcome is recorded (`eligible-for-flip-proposal`, `conditional-no-flip`, or `blocked-no-flip`) with supporting evidence.
4. Same-SHA evidence branch is explicit and complete:
   - either run id/url + required-job summary, or inability reason + residual risk
   - no implied same-SHA validation when evidence is unavailable
5. Route-fence target row remains unchanged (`v0`, `Slice-57`, `ready`) in both md/json artifacts.
6. Governance checks pass: `--check readiness`, `--check parity`, `--check all`.
7. Slice 61 implementation and audit reports exist, and audit is explicitly PASS before any orchestration update to `WORK_ITEMS.md`.

## Binary success condition
Slice 61 is successful only if it produces a complete decision-only progression record for `config_init|n/a`, preserves all governance truth unchanged, records an explicit fail-closed decision gate for later flip proposals with same-SHA branch handling, passes required governance checks, and receives explicit audit PASS before any `WORK_ITEMS.md` update.

## Fail-close criteria
- Any mutation to `project/route-fence.md` or `project/route-fence.json`.
- Any mutation to parity/workflow/verification-contract/CI/runtime/test artifacts.
- Missing or ambiguous decision gate outcome.
- Missing same-SHA branch proof details (or missing inability + residual-risk statement when unavailable).
- If same-SHA run evidence exists but per-required-job summary is missing/ambiguous for required jobs (`test`, `security`, `quality`, `governance`), fail close.
- Any implied route-flip readiness claim without satisfying decision-gate requirements.
- Any `WORK_ITEMS.md` update before explicit audit PASS.

## Implementation steps (for Slice 61 execution worker)
1. Capture baseline proof for `config_init|n/a` from route-fence md/json and readiness counters.
2. Capture local SHA and attempt same-SHA CI evidence collection.
3. Evaluate gate outcome using explicit fail-closed decision rules above.
4. Write `slice-61-implementation.md` with:
   - baseline proof
   - gate outcome + rationale
   - same-SHA branch evidence or inability + residual risk
   - no-mutation scope proof
5. Run required governance checks (`readiness`, `parity`, `all`) and record outputs.
6. Hand off for independent audit (`slice-61-audit.md`).

## Minimum evidence commands (PowerShell)
```powershell
# Local SHA + target-row baseline proof
$sha = (git rev-parse HEAD).Trim()
"local_sha=$sha"
$requiredJobs = @('test','security','quality','governance')
Select-String -Path project/route-fence.md -Pattern '^\|\s*config_init\s*\|\s*n/a\s*\|'
$rf = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rf.rows |
  Where-Object { $_.command -eq 'config_init' -and $_.mode -eq 'n/a' } |
  Format-List command, mode, route, owner_slice, parity_status

# Same-SHA CI evidence attempt (gh branch)
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
    # Per-required-job summary path for the gh branch (`test`, `security`, `quality`, `governance`)
    $ghRunView = gh run view $ghCandidateRun.databaseId --json jobs | ConvertFrom-Json
    $ghRunView.jobs |
      Where-Object { $requiredJobs -contains $_.name } |
      Select-Object name, status, conclusion, startedAt, completedAt
  }
} catch {
  $ghAvailable = $false
  "gh_unavailable_reason=$($_.Exception.Message)"
}

# Fallback: GitHub REST same-SHA query when `gh` is unavailable
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
$sha = (git rev-parse HEAD).Trim()
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
  # Per-required-job summary path for the REST branch (`test`, `security`, `quality`, `governance`)
  $jobsUri = "https://api.github.com/repos/$owner/$repo/actions/runs/$($restCandidateRun.id)/jobs?per_page=100"
  $restJobs = Invoke-RestMethod -Method Get -Uri $jobsUri -Headers $headers
  $restJobs.jobs |
    Where-Object { $requiredJobs -contains $_.name } |
    Select-Object name, status, conclusion, html_url
}

# Scope diff checks (must show no governance-truth mutation)
git diff --name-only
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml WORK_ITEMS.md

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

Expected proof points:
- Baseline row remains `config_init|n/a -> v0 | Slice-57 | ready`.
- Readiness output remains:
  - `INFO: Route readiness claims: 4`
  - `INFO: Route readiness claims validated: 4`
- Decision gate is explicit and supported by one accepted evidence branch:
  - `gh` branch: `gh run list` returns same-SHA evidence; candidate run id is recorded; per-required-job status summary is captured for `test`, `security`, `quality`, `governance`.
  - REST fallback branch: `gh` unavailable/fails, but `Invoke-RestMethod` same-SHA query succeeds; candidate run id is recorded; per-required-job status summary is captured for `test`, `security`, `quality`, `governance`.
  - dual-unavailable branch: both `gh` and REST evidence collection are unavailable/unsuccessful; outcome must be `decision_gate: conditional-no-flip` with explicit inability reason + residual risk.
- When same-SHA evidence exists (either `gh` or REST branch), proof includes an explicit per-required-job summary for `test`, `security`, `quality`, `governance` with unambiguous status/conclusion for each required job.
- Protected governance-truth diffs are empty during implementation/audit phases:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
  - `WORK_ITEMS.md`
- `git diff --name-only` remains limited to Slice 61 report artifacts during implementation/audit phases.

## Risks/guardrails
- Risk: treating readiness activation as implicit authorization for route flip.
  Guardrail: explicit decision gate required; this slice cannot mutate route.
- Risk: incomplete same-SHA evidence causing ambiguous progression posture.
  Guardrail: fail closed unless branch is fully documented (evidence or inability+residual risk).
- Risk: accidental governance-truth mutation while collecting evidence.
  Guardrail: out-of-scope artifact diffs are hard-fail.
- Risk: context drift into implementation work.
  Guardrail: single objective, report-only outputs, and explicit split rule below.

## Suggested next slice
- Slice 62 (conditional by Slice 61 gate outcome):
  - If `eligible-for-flip-proposal`: one-row route-flip proposal slice for `config_init|n/a` (`v0 -> v1`) with parity/owner unchanged.
  - If `conditional-no-flip` or `blocked-no-flip`: same-SHA CI evidence remediation slice (no route mutation) before any flip proposal.

## Explicit split rule if scope grows too large
- Stop and split immediately if any of the following becomes necessary:
  - editing route-fence/parity/workflow/verification-contract/CI artifacts
  - editing runtime or test files
  - handling more than one route row
  - toolchain/auth remediation work that exceeds evidence capture (for example, installing/configuring CI tooling)
- Keep Slice 61 limited to one objective: a fail-closed progression decision record for `config_init|n/a` with no governance-truth mutation.
