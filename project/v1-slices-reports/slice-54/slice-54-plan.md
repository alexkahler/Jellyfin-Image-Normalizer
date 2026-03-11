# Slice 54 Plan v3 (Final) - Same-SHA CI Evidence Remediation/Collection for `config_validate|n/a`

Date: 2026-03-11
Branch: feat/v1-overhaul
Local SHA: be9fa48a618adf9ce00b090044ce797c7e5224fb

## Slice ID + Title
- Slice 54
- Same-SHA CI evidence remediation/collection for `config_validate|n/a`

## Goal / Objective
- Resolve the same-SHA CI evidence branch for local SHA `be9fa48a618adf9ce00b090044ce797c7e5224fb` and `config_validate|n/a`.
- Produce explicit, policy-compliant evidence records for either:
- same-SHA run available with required-job outcomes, or
- same-SHA run unavailable with inability reason + residual-risk statement.

## Baseline State (Pre-Mutation Snapshot)
- Route row `config_validate|n/a` currently: `route=v0`, `owner=Slice-49`, `parity=ready`.
- Readiness counters currently: `claimed_rows=3`, `validated_rows=3`.
- This slice is evidence-only and must not mutate route/governance truth.

## Worker Split + File Scope (Exact)
- Implementation worker writable scope:
- `project/v1-slices-reports/slice-54/slice-54-implementation.md`
- Audit worker writable scope:
- `project/v1-slices-reports/slice-54/slice-54-audit.md`
- Plan record (this slice contract):
- `project/v1-slices-reports/slice-54/slice-54-plan.md`
- Explicitly out of implementation-worker scope:
- `WORK_ITEMS.md`
- Orchestration-thread allowance:
- post-audit `WORK_ITEMS.md` sequence update may be done separately, only after Slice 54 audit evidence is recorded.

## In-Scope / Out-of-Scope (Tight Files)
- In-scope files for Slice 54 artifacts:
- `project/v1-slices-reports/slice-54/slice-54-plan.md`
- `project/v1-slices-reports/slice-54/slice-54-implementation.md`
- `project/v1-slices-reports/slice-54/slice-54-audit.md`
- Out-of-scope files (no mutation):
- `project/route-fence.md`
- `project/route-fence.json`
- `project/parity-matrix.md`
- `project/workflow-coverage-index.json`
- `project/verification-contract.yml`
- `.github/workflows/ci.yml`
- `WORK_ITEMS.md` (implementation worker)
- all `src/` and `tests/` files

## Acceptance Criteria
- Slice 54 artifacts capture local SHA, workflow identity, and same-SHA CI query method/result.
- If same-SHA CI run exists, record:
- CI run id/url,
- required-job status summary for `test`, `security`, `quality`, `governance`.
- If same-SHA CI run is unavailable, record:
- explicit inability reason,
- explicit residual risk,
- no implied same-SHA validation claim.
- No route/progression/governance-truth mutation is performed in this slice.

## Binary Success Condition
- Slice 54 is PASS only if evidence artifacts are complete for exactly one explicit same-SHA branch (available or unavailable) and all out-of-scope governance-truth files remain unchanged.

## Fail-Close Criteria (Blocks Closure)
- If same-SHA CI evidence status cannot be determined unambiguously, mark Slice 54 FAIL.
- If required fields are missing (local SHA, workflow identity, and either run id/url + required-job summary or inability + residual risk), mark Slice 54 FAIL.
- If any route/parity/readiness/workflow governance-truth file is modified, mark Slice 54 FAIL.
- If implementation worker scope expands beyond `slice-54-implementation.md`, stop and split/re-scope before closure.

## Minimum Evidence Commands (PowerShell; `gh` with REST Fallback)
```powershell
# baseline context
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD

# preferred path (if gh is available)
gh run list --limit 200 --json databaseId,headSha,workflowName,url,status,conclusion
# then for a selected same-SHA run id:
gh run view <run_id> --json headSha,workflowName,url,status,conclusion,jobs

# fallback path when gh is unavailable
$sha = (git rev-parse HEAD).Trim()
$repo = "alexkahler/Jellyfin-Image-Normalizer"
$headers = @{
  "Accept" = "application/vnd.github+json"
  "X-GitHub-Api-Version" = "2022-11-28"
  "User-Agent" = "jfin-slice-54"
}
if ($env:GITHUB_TOKEN) { $headers["Authorization"] = "Bearer $env:GITHUB_TOKEN" }

# same-SHA run discovery
$runsUri = "https://api.github.com/repos/$repo/actions/runs?head_sha=$sha&per_page=20"
$runs = Invoke-RestMethod -Method Get -Uri $runsUri -Headers $headers

# required-job status source for selected run id
$runId = <run_id>
$jobsUri = "https://api.github.com/repos/$repo/actions/runs/$runId/jobs?per_page=100"
$jobs = Invoke-RestMethod -Method Get -Uri $jobsUri -Headers $headers
```
- Record explicit inability reason + residual risk if neither `gh` nor REST path can produce same-SHA evidence.

## Implementation Steps
1. Confirm local SHA and branch for evidence targeting.
2. Query GitHub Actions for `head_sha=<local_sha>` using available tooling (`gh` or REST API).
3. Filter results to repository CI workflow and extract run metadata if a same-SHA run exists.
4. Record one of two explicit branches in `slice-54-implementation.md`:
5. available branch: workflow identity + run id/url + required-job summary, or
6. unavailable branch: inability reason + residual risk.
7. Confirm no diffs in out-of-scope governance truth files.

## Post-Implementation Orchestration Steps
1. Audit worker reviews `slice-54-implementation.md` and produces `slice-54-audit.md` with explicit PASS/FAIL against acceptance and fail-close criteria.
2. If audit result is PASS, orchestration thread may perform a post-audit `WORK_ITEMS.md` sequence update as a separate action outside implementation-worker scope.
3. If audit result is FAIL, stop closure and carry forward the blocker without route/parity/workflow truth mutation.

## Risk / Guardrails
- Risk: local governance checks alone can overstate confidence when remote same-SHA CI is missing.
- Guardrail: this is remediation/collection only, not a route-flip or readiness-truth mutation slice.
- Guardrail: keep scope to Slice 54 report artifacts only; no opportunistic cleanup.
- Guardrail: fail closed on ambiguous CI evidence; never infer required-job pass state without direct evidence.

## Suggested Next Slice
- Slice 55 (bounded): one-row progression action for `config_validate|n/a` only (`route v0 -> v1` candidate), contingent on Slice 54 evidence branch recording; do not include additional rows or unrelated governance-truth edits.

## Split Rule If Scope Grows
- If work expands beyond same-SHA evidence remediation/collection (for example, route-fence edits or broader governance updates), stop and split:
- keep Slice 54 evidence-only,
- defer route/progression mutation or governance updates to a new dedicated slice.
