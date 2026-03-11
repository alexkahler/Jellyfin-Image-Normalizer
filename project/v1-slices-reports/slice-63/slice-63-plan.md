# Slice 63 Plan v3 (Final) - Same-SHA CI Evidence Remediation Continuation for `config_init|n/a` (Evidence-Only, No Route Mutation)

Date: 2026-03-11  
Branch: `feat/v1-overhaul`  
Planning review status: v1 reviewed, v2 refinements applied, v3 final.

## 1) Slice ID and Title
- Slice 63
- Same-SHA CI evidence remediation continuation for `config_init|n/a` (evidence-only, no route mutation)

## 2) Context and Objective
- Prior slice: Slice 62 closed with `decision_gate: conditional-no-flip`.
- Target row must remain unchanged:
  - `command=config_init`, `mode=n/a`, `route=v0`, `owner_slice=Slice-57`, `parity_status=ready`
- Readiness baseline must remain `claims=4`, `validated=4`.
- Objective: produce an explicit, fail-closed same-SHA CI evidence outcome for the current local SHA while preserving governance truth unchanged.

## 3) Scope
### In scope
- Single-row evidence continuation for `config_init|n/a` only.
- Same-SHA evidence collection and outcome recording for this slice SHA.
- Report artifacts for plan, implementation, and audit.

### Out of scope
- Any governance-truth mutation:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
- Any runtime or test changes under `src/` or `tests/`.
- Any route flip or progression mutation.
- Multi-row evidence work.

## 4) Writable File Allowlist
- Planning worker: `project/v1-slices-reports/slice-63/slice-63-plan.md`
- Implementation worker: `project/v1-slices-reports/slice-63/slice-63-implementation.md`
- Audit worker: `project/v1-slices-reports/slice-63/slice-63-audit.md`
- Orchestration thread only (after audit PASS): `WORK_ITEMS.md`

## 5) Acceptance Criteria
1. Slice is evidence-only/documentation-only.
2. Target row remains unchanged in both route-fence artifacts: `config_init|n/a -> v0 | Slice-57 | ready`.
3. Implementation report records exactly one same-SHA branch outcome:
   - `same_sha_branch: evidence-complete`, or
   - `same_sha_branch: evidence-unavailable`
4. Implementation report records exactly one decision token:
   - `decision_gate: eligible-for-flip-proposal`
   - `decision_gate: conditional-no-flip`
   - `decision_gate: blocked-no-flip`
5. Token uniqueness is proven (exactly one standardized decision token occurrence).
6. If `same_sha_branch: evidence-complete`, report includes same-SHA run id/url and per-required-job statuses for `test`, `security`, `quality`, `governance`.
7. If `same_sha_branch: evidence-unavailable`, report includes explicit inability reason, explicit residual risk, and explicit no-implied-validation statement.
8. Protected-file diff proof is empty for out-of-scope governance-truth files and `WORK_ITEMS.md` before post-audit update.
9. Governance checks pass:
   - `project/scripts/verify_governance.py --check readiness`
   - `project/scripts/verify_governance.py --check parity`
   - `project/scripts/verify_governance.py --check all`
10. Readiness proof lines remain:
   - `INFO: Route readiness claims: 4`
   - `INFO: Route readiness claims validated: 4`
11. Audit report is explicit PASS before `WORK_ITEMS.md` is updated.

## 6) Binary Success Condition
Slice 63 succeeds only if one explicit same-SHA branch outcome and one unique decision token are recorded for `config_init|n/a`, governance truth remains unchanged, required governance checks pass, and independent audit returns PASS before any `WORK_ITEMS.md` mutation.

## 7) Fail-Close Triggers
- Any mutation to out-of-scope governance-truth artifacts.
- Any runtime/test file mutation.
- Missing or ambiguous same-SHA branch outcome.
- Missing/duplicate/ambiguous decision token.
- Same-SHA run exists but required-job summary is missing or unclear.
- Missing audit report or non-PASS audit conclusion.
- `WORK_ITEMS.md` modified before audit PASS.

## 8) Implementation Steps
1. Capture `local_sha` and workflow identity (`CI`, `.github/workflows/ci.yml`).
2. Reconfirm `config_init|n/a` baseline row from route-fence markdown and JSON.
3. Attempt same-SHA evidence via `gh`.
4. Attempt REST fallback when `gh` is unavailable or insufficient.
5. Record one branch outcome (`evidence-complete` or `evidence-unavailable`) and one decision token.
6. Capture decision-token uniqueness evidence.
7. Capture protected-file no-mutation diffs.
8. Run governance checks (`readiness`, `parity`, `all`) and record outputs.
9. Write implementation report and hand off to independent audit worker.

## 9) Risks and Guardrails
- Risk: accidental route-fence/progression mutation.
  - Guardrail: protected-file diff checks must stay empty; fail closed otherwise.
- Risk: ambiguous evidence narration.
  - Guardrail: enforce one branch marker and one token marker with uniqueness proof.
- Risk: context rot from scope growth.
  - Guardrail: single-row, report-only slice with strict allowlist.

## 10) Verification Commands
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
rg -n "decision_gate:" project/v1-slices-reports/slice-63/slice-63-implementation.md

.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

## 11) Evidence and Reporting Outputs
- Plan: `project/v1-slices-reports/slice-63/slice-63-plan.md`
- Implementation: `project/v1-slices-reports/slice-63/slice-63-implementation.md`
- Audit: `project/v1-slices-reports/slice-63/slice-63-audit.md`

## 12) Suggested Next Slice
- Slice 64 (conditional fork, no implicit mutation in this slice):
  - If same-SHA evidence is complete with required-job closure, run a decision/progression slice for `config_init|n/a` (proposal-only unless explicitly approved to mutate route).
  - If same-SHA evidence remains unavailable/incomplete, continue evidence remediation (no route mutation).
