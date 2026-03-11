# Slice 67 Plan v3 (Final) - Loop-Breaker Same-SHA CI Evidence Acquisition for `config_init|n/a` (External-Unblock Gate)

Date: 2026-03-11  
Branch: `feat/v1-overhaul`  
Planning review status: v1 reviewed, v2 reviewed, v3 final (loop-breaker override approved).

## 1) Slice ID and Title
- Slice 67
- Loop-breaker same-SHA CI evidence acquisition for `config_init|n/a` (external-unblock gate)

## 2) Goal / Objective
Break the repeated `evidence-unavailable -> conditional-no-flip` cycle by anchoring evidence collection to one immutable SHA and executing an external-unblock action (`git push` + CI run polling) before any further continuation slicing.

Anchor SHA for this slice (frozen target):
- `deb1635730ea381eb438d74014c65b1a8e11e480`

## 3) In Scope / Out of Scope
### In scope
- Single-row target only: `config_init|n/a`.
- External-unblock action for anchored SHA:
  - push branch to origin,
  - query GitHub Actions runs for exact `head_sha=deb1635730ea381eb438d74014c65b1a8e11e480`,
  - if run exists, collect required-job outcomes (`test`, `security`, `quality`, `governance`).
- Produce slice reports (`plan`, `implementation`, `audit`) with explicit terminal branch outcome.

### Out of scope
- Any governance-truth mutation:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
- Any runtime/test edits under `src/` or `tests/`.
- Any route mutation/progression flip in this slice.
- Repeating identical continuation objective (`same_sha_branch: evidence-unavailable`) without new external action.

## 4) Writable File Allowlist
- Planning worker: `project/v1-slices-reports/slice-67/slice-67-plan.md` only
- Implementation worker: `project/v1-slices-reports/slice-67/slice-67-implementation.md` only
- Audit worker: `project/v1-slices-reports/slice-67/slice-67-audit.md` only
- Orchestration thread only (after audit PASS): `WORK_ITEMS.md`

## 5) Acceptance Criteria
1. Slice objective is loop-breaker external-unblock for anchored SHA `deb1635730ea381eb438d74014c65b1a8e11e480`.
2. Implementation records explicit push attempt outcome for `feat/v1-overhaul -> origin`.
3. Implementation records exact same-SHA query evidence for anchored SHA (`same_sha_total_runs` and selected run metadata when present).
4. Implementation records exactly one branch marker:
   - `same_sha_branch: evidence-complete`, or
   - `same_sha_branch: blocked-external`
5. Implementation records exactly one decision token:
   - `decision_gate: eligible-for-flip-proposal`, or
   - `decision_gate: blocked-no-flip`
6. Uniqueness proof outputs are recorded and exact:
   - `decision_token_match_count=1`
   - `same_sha_branch_match_count=1`
   - proof-source commands use `Select-String` or `rg`.
7. If `same_sha_branch: evidence-complete`, report includes run id/url and required-job status summary for `test/security/quality/governance`.
8. If `same_sha_branch: blocked-external`, report includes explicit inability reason, terminal-block note, and concrete resume condition.
9. Protected-file diff proof is empty for out-of-scope governance files and `WORK_ITEMS.md` before post-audit update.
10. Governance checks pass: `--check readiness`, `--check parity`, `--check all`.
11. Audit report returns explicit PASS before any `WORK_ITEMS.md` update.

## 6) Binary Success Condition
Slice 67 succeeds only if it produces one of two terminal outcomes for anchored SHA evidence:
- evidence-complete -> decision may move to `eligible-for-flip-proposal`, or
- blocked-external -> decision is `blocked-no-flip` with explicit resume condition.

A repeated non-terminal continuation outcome is not an acceptable success state for this loop-breaker slice.

## 7) Fail-Close Triggers
- Any mutation to out-of-scope governance-truth files.
- Any runtime/test mutation.
- Missing/duplicate/ambiguous branch marker or decision token.
- Missing anchored-SHA reference or querying the wrong SHA.
- Same-SHA run exists but required-job status summary is missing/ambiguous.
- Reporting `conditional-no-flip` as final outcome for this slice.
- Missing audit report or non-PASS audit result.
- `WORK_ITEMS.md` updated before audit PASS.

## 8) Implementation Steps
1. Capture frozen anchor SHA (`deb1635730ea381eb438d74014c65b1a8e11e480`) and required jobs list.
2. Record baseline row proof for `config_init|n/a` from route-fence markdown + JSON.
3. Execute external-unblock action: `git push origin feat/v1-overhaul`; record success/failure.
4. Query same-SHA runs for anchor SHA via REST (and `gh` branch if available); poll up to 15 minutes.
5. If run appears, capture run id/url and required-job statuses.
6. Record exactly one terminal branch marker and one decision token.
7. Record marker uniqueness proof outputs.
8. Capture protected-file no-mutation proof.
9. Run governance checks (`readiness`, `parity`, `all`) and record outputs.
10. Write implementation report and hand off to audit.

## 9) Risk / Guardrails
- Risk: CI evidence remains unavailable even after push.
  - Guardrail: use terminal `blocked-external` branch with explicit resume condition; no repeated continuation slice.
- Risk: accidental governance-truth mutation while running loop-breaker.
  - Guardrail: protected diff checks must remain empty; fail closed otherwise.
- Risk: ambiguous decision narrative.
  - Guardrail: exactly one branch marker + exactly one decision token + uniqueness proof.

## 10) Suggested Next Slice
- Slice 68 decision fork (no implicit mutation in Slice 67):
  - If `evidence-complete` with required-job closure: progression-decision slice for `config_init|n/a` (proposal-only unless explicitly approved to mutate route).
  - If `blocked-external`: external-unblock prerequisite slice only (CI/permissions/runner availability), and pause further same-objective continuation slices.

## 11) Verification Commands
```powershell
$anchorSha = 'deb1635730ea381eb438d74014c65b1a8e11e480'
$requiredJobs = @('test','security','quality','governance')
"anchor_sha=$anchorSha"

Select-String -Path project/route-fence.md -Pattern '^\|\s*config_init\s*\|\s*n/a\s*\|'
$rf = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rf.rows | Where-Object { $_.command -eq 'config_init' -and $_.mode -eq 'n/a' } |
  Select-Object command, mode, route, owner_slice, parity_status

# External-unblock action
git push origin feat/v1-overhaul

# Same-SHA REST polling (up to 15 minutes)
$origin = (git config --get remote.origin.url).Trim()
if ($origin -notmatch 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/.]+)(?:\.git)?$') { throw "Unable to parse GitHub remote: $origin" }
$owner = $Matches.owner; $repo = $Matches.repo
$headers = @{ Accept = 'application/vnd.github+json' }
if ($env:GITHUB_TOKEN) { $headers.Authorization = "Bearer $($env:GITHUB_TOKEN)" }
$runFound = $false
for ($i = 1; $i -le 30; $i++) {
  $uri = "https://api.github.com/repos/$owner/$repo/actions/runs?head_sha=$anchorSha&per_page=100"
  $rest = Invoke-RestMethod -Method Get -Uri $uri -Headers $headers
  "poll_attempt=$i rest_same_sha_total_runs=$($rest.total_count)"
  if ($rest.total_count -gt 0) {
    $runFound = $true
    $candidate = $rest.workflow_runs | Where-Object { $_.head_sha -eq $anchorSha } | Select-Object -First 1
    if ($candidate) {
      "run_id=$($candidate.id)"
      "run_name=$($candidate.name)"
      "run_url=$($candidate.html_url)"
      $jobsUri = "https://api.github.com/repos/$owner/$repo/actions/runs/$($candidate.id)/jobs?per_page=100"
      $jobs = Invoke-RestMethod -Method Get -Uri $jobsUri -Headers $headers
      $jobs.jobs | Where-Object { $requiredJobs -contains $_.name } | Select-Object name,status,conclusion,html_url
    }
    break
  }
  Start-Sleep -Seconds 30
}
if (-not $runFound) { 'terminal_block=blocked-external' }

git diff --name-only
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml WORK_ITEMS.md
rg -n "decision_gate:" project/v1-slices-reports/slice-67/slice-67-implementation.md
rg -n "same_sha_branch:" project/v1-slices-reports/slice-67/slice-67-implementation.md

.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

## 12) Evidence and Reporting Outputs
- Plan: `project/v1-slices-reports/slice-67/slice-67-plan.md`
- Implementation: `project/v1-slices-reports/slice-67/slice-67-implementation.md`
- Audit: `project/v1-slices-reports/slice-67/slice-67-audit.md`

## 13) Split-if-too-large Rule
Stop and split immediately if:
- scope expands beyond single-row target (`config_init|n/a`),
- any governance-truth/runtime/test mutation becomes necessary,
- external prerequisites require infrastructure/tooling work beyond evidence capture.

If split is triggered, retain this slice as loop-breaker evidence capture only and defer prerequisite work to a dedicated external-unblock slice.
