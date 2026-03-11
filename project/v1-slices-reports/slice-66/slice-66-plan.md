# Slice 66 Plan v3 (Final) - Same-SHA CI Evidence Remediation Continuation for `config_init|n/a` (Evidence-Only, No Route Mutation)

Date: 2026-03-11  
Branch: `feat/v1-overhaul`
Planning review status: v1 reviewed, v2 reviewed, v3 final.

## 1) Slice ID and Title
- Slice 66
- Same-SHA CI evidence remediation continuation for `config_init|n/a` (evidence-only, no route mutation)

## 2) Goal / Objective
Continue fail-closed same-SHA CI evidence collection for `config_init|n/a` on the current local SHA and record an explicit evidence outcome while preserving governance truth unchanged.

## 3) In Scope / Out of Scope
### In scope
- Single-row evidence continuation for `config_init|n/a` only.
- Same-SHA evidence attempts (`gh` and REST fallback) and explicit branch outcome recording.
- Slice reporting artifacts (`plan`, `implementation`, `audit`).

### Out of scope
- Any governance-truth mutation:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
- Any runtime/test edits under `src/` or `tests/`.
- Any route mutation/progression flip for any row.
- Multi-row evidence work.

## 4) Writable File Allowlist
- Planning worker: `project/v1-slices-reports/slice-66/slice-66-plan.md` only
- Implementation worker: `project/v1-slices-reports/slice-66/slice-66-implementation.md` only
- Audit worker: `project/v1-slices-reports/slice-66/slice-66-audit.md` only
- Orchestration thread only (after audit PASS): `WORK_ITEMS.md`

## 5) Acceptance Criteria
1. Slice remains evidence-only/documentation-only.
2. Target row remains unchanged in both route-fence artifacts: `config_init|n/a -> v0 | Slice-57 | ready`.
3. Implementation report contains exactly one same-SHA branch marker:
   - `same_sha_branch: evidence-complete`, or
   - `same_sha_branch: evidence-unavailable`
4. Implementation report contains exactly one decision token:
   - `decision_gate: eligible-for-flip-proposal`
   - `decision_gate: conditional-no-flip`
   - `decision_gate: blocked-no-flip`
5. Uniqueness proof output is recorded and exact:
   - `decision_token_match_count=1`
   - `same_sha_branch_match_count=1`
   - Proof-source commands are included in the implementation report and use `Select-String` or `rg`.
6. If evidence-complete branch is used, run id/url and required-job status summary for `test/security/quality/governance` are recorded.
7. If evidence-unavailable branch is used, explicit inability reason + residual risk + no-implied-validation statement are recorded.
8. Protected-file diff proof is empty for out-of-scope governance files and `WORK_ITEMS.md` before post-audit update.
9. Governance checks pass: `--check readiness`, `--check parity`, `--check all`.
10. Readiness remains 4/4 with proof lines:
    - `INFO: Route readiness claims: 4`
    - `INFO: Route readiness claims validated: 4`
11. Audit report returns explicit PASS before any `WORK_ITEMS.md` update.

## 6) Binary Success Condition
Slice 66 is successful only if exactly one same-SHA branch marker and exactly one decision token are recorded with uniqueness proof outputs and proof-source commands, protected governance/work-item files remain unchanged, governance checks pass, and audit returns PASS before any `WORK_ITEMS.md` update.

## 7) Fail-Close Triggers
- Any mutation to out-of-scope governance-truth files.
- Any runtime or test file mutation.
- Missing/ambiguous or duplicate same-SHA branch marker.
- Missing/ambiguous or duplicate decision token.
- Missing uniqueness proof outputs or counts not equal to `1`.
- Missing proof-source commands for uniqueness evidence.
- Same-SHA run exists but required-job status summary is missing/ambiguous.
- Missing audit report or non-PASS audit result.
- `WORK_ITEMS.md` modified before audit PASS.

## 8) Implementation Steps
1. Capture local SHA and workflow identity (`CI`, `.github/workflows/ci.yml`).
2. Reconfirm baseline row from route-fence markdown and JSON.
3. Attempt same-SHA CI evidence via `gh`.
4. Attempt REST fallback using `actions/runs?head_sha=<sha>` when `gh` is unavailable/insufficient.
5. Record exactly one `same_sha_branch` marker and exactly one `decision_gate` marker.
6. Record uniqueness proof for both markers.
7. Capture no-mutation proof (`git diff`) for protected files.
8. Run governance checks (`readiness`, `parity`, `all`) and record outputs.
9. Write implementation report and hand off to audit worker.

## 9) Risk / Guardrails
- Risk: accidental governance-truth or route mutation.
  - Guardrail: fail closed on any protected-file diff.
- Risk: ambiguous branch/token evidence.
  - Guardrail: enforce exactly one branch marker and one decision token with explicit counts.
- Risk: context rot/scope creep.
  - Guardrail: strict single-row objective and report-only writable scope.

## 10) Suggested Next Slice
- Slice 67 (conditional fork, no implicit mutation in Slice 66):
  - If same-SHA evidence is complete with required-job closure, run a progression decision slice for `config_init|n/a` (proposal-only unless explicitly approved).
  - If same-SHA evidence remains unavailable/incomplete, continue evidence remediation with no route mutation.

## 11) Verification Commands
```powershell
$sha = (git rev-parse HEAD).Trim()
"local_sha=$sha"

Select-String -Path project/route-fence.md -Pattern '^\|\s*config_init\s*\|\s*n/a\s*\|'
$rf = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rf.rows | Where-Object { $_.command -eq 'config_init' -and $_.mode -eq 'n/a' } |
  Select-Object command, mode, route, owner_slice, parity_status

# gh evidence attempt
gh run list --limit 200 --json databaseId,headSha,workflowName,url,status,conclusion

# REST fallback
$origin = (git config --get remote.origin.url).Trim()
if ($origin -notmatch 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/.]+)(?:\.git)?$') { throw "Unable to parse GitHub remote: $origin" }
$owner = $Matches.owner; $repo = $Matches.repo
$headers = @{ Accept = 'application/vnd.github+json' }
if ($env:GITHUB_TOKEN) { $headers.Authorization = "Bearer $($env:GITHUB_TOKEN)" }
$uri = "https://api.github.com/repos/$owner/$repo/actions/runs?head_sha=$sha&per_page=100"
$rest = Invoke-RestMethod -Method Get -Uri $uri -Headers $headers
"rest_same_sha_total_runs=$($rest.total_count)"

git diff --name-only
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml WORK_ITEMS.md
rg -n "decision_gate:" project/v1-slices-reports/slice-66/slice-66-implementation.md
rg -n "same_sha_branch:" project/v1-slices-reports/slice-66/slice-66-implementation.md

.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

## 12) Evidence and Reporting Outputs
- Plan: `project/v1-slices-reports/slice-66/slice-66-plan.md`
- Implementation: `project/v1-slices-reports/slice-66/slice-66-implementation.md`
- Audit: `project/v1-slices-reports/slice-66/slice-66-audit.md`

## 13) Split-if-too-large Rule
Stop immediately and split this work into follow-on slices if any of the following occurs:
- Scope expands beyond single-row target (`config_init|n/a`).
- Governance-truth mutation becomes necessary (`route-fence`, parity, workflow index, verification contract, or CI workflow).
- Runtime or test edits under `src/` or `tests/` become necessary.
- Tooling/auth setup beyond evidence capture/reporting is required.
If a split is triggered, this slice remains evidence-only/no-mutation and additional work is deferred to the next explicitly planned slice.
