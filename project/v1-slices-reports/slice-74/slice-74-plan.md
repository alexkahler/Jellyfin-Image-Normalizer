# Slice 74 Plan v3 (Final)

Date: 2026-03-11  
Branch: `feat/v1-overhaul`  
Planning review status: v3 final.

## 1) Slice ID/title
- Slice 74
- One-row ownership/readiness-prep follow-on for `run|profile` (no route flip)

## 2) Goal/objective
- Complete one bounded objective: ownership/readiness-prep follow-on for route-fence row `run|profile`.
- Apply exactly one owner-only mutation in both route-fence artifacts:
  - `owner_slice: WI-00X -> Slice-74`
- Preserve target-row non-owner fields:
  - `route` remains `v0`
  - `parity_status` remains `pending`

## 3) In-scope/out-of-scope
### In scope
- Slice 74 artifacts (`plan`, `implementation`, `audit`).
- Single target-row owner mutation for `run|profile` in:
  - `project/route-fence.md`
  - `project/route-fence.json`
- Evidence capture proving one-row mutation cardinality and no non-target row changes.

### Out of scope
- Any route flip (including `run|profile`).
- Any parity-status change (including `run|profile`).
- Any non-target route-fence row mutation.
- Any runtime/test edits (`src/`, `tests/`).
- Any parity/workflow/verification-contract/CI edits:
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`

## 4) Tight role-based writable allowlist
- Planning worker: `project/v1-slices-reports/slice-74/slice-74-plan.md` only.
- Implementation worker:
  - Always allowed: `project/v1-slices-reports/slice-74/slice-74-implementation.md`.
  - Conditionally allowed: `project/route-fence.md`, `project/route-fence.json` for one-row `run|profile` owner update only (`WI-00X -> Slice-74`).
- Audit worker: `project/v1-slices-reports/slice-74/slice-74-audit.md` only.
- Orchestration worker (post-audit only): `WORK_ITEMS.md` append-only single-line Slice 74 status update with required next-pointer to Slice 75.

## 5) Measurable acceptance criteria
1. Pre-mutation baseline is proven in both route-fence artifacts:
   - `run|profile -> route=v0, owner_slice=WI-00X, parity_status=pending`.
2. Pre-mutation readiness counters are captured:
   - `ready_v0`, `ready_v1`, `pending_v0`, `pending_v1`.
3. Exactly one owner-only mutation is applied in both route-fence artifacts:
   - `run|profile owner_slice: WI-00X -> Slice-74`.
4. Markdown route-fence diff cardinality is exact:
   - one removed target row (`run|profile` old row),
   - one added target row (`run|profile` new row),
   - total markdown table row deltas remain `removed=1`, `added=1`.
5. JSON route-fence mutation cardinality is exact:
   - changed row count is `1`,
   - changed row key is only `run|profile`.
6. JSON row-key-set drift proof is fail-closed:
   - `json_added_row_count=0`
   - `json_removed_row_count=0`
   - counts are computed from `HEAD` vs working-tree `project/route-fence.json` row-key sets.
7. Target-row invariants are preserved post-mutation:
   - `route=v0`, `parity_status=pending`, `owner_slice=Slice-74`.
8. Readiness counters remain unchanged versus pre-mutation snapshot.
9. No non-target route-fence rows change.
10. No out-of-scope file mutations occur (`src/`, `tests/`, parity/workflow/verification-contract/CI files).
11. Governance checks pass:
   - `--check readiness`
   - `--check parity`
   - `--check all`
12. Slice 74 implementation and audit reports exist with explicit PASS/FAIL verdict semantics.
13. Pre-audit `WORK_ITEMS.md` protection is proven measurable:
   - `git diff --name-only -- WORK_ITEMS.md` returns empty until explicit Slice 74 audit PASS.
14. Pre-append duplicate guard for post-audit `WORK_ITEMS.md` update passes:
   - `preexisting_slice74_line_count=0`.
15. Post-append proof is append-only and single-line:
   - `work_items_line_delta=+1`
   - `work_items_added_lines_count=1`
   - `work_items_removed_lines_count=0`
   - `slice74_work_items_line_count=1`
16. Appended Slice 74 line matches required next-pointer regex exactly once:
   - `^- Slice 74 -> .*next:\s*Slice 75\b.*$`
   - `slice74_work_items_next_pointer_match_count=1`

## 6) Ordered implementation steps
1. Capture baseline row evidence for `run|profile` from markdown and JSON route-fence artifacts.
2. Capture pre-mutation readiness counter snapshot (`ready_v0`, `ready_v1`, `pending_v0`, `pending_v1`).
3. Record scope guardrails and out-of-scope no-change baseline.
4. Apply one-row ownership-only mutation in both route-fence artifacts:
   - `owner_slice: WI-00X -> Slice-74` for `run|profile` only.
5. Capture mutation cardinality proofs:
   - markdown diff row counts (`target` and `all-row`),
   - JSON changed-row count/changed-key set and JSON added/removed row-key counts (`HEAD` vs working tree).
6. Verify invariants:
   - `run|profile` remains `v0 | Slice-74 | pending`,
   - readiness counters unchanged.
7. Run governance checks (`readiness`, `parity`, `all`) and capture outputs.
8. Write `slice-74-implementation.md` with evidence and explicit outcome.
9. Audit worker performs independent verification and writes `slice-74-audit.md` with explicit verdict.
10. After explicit audit PASS only, orchestration may append exactly one Slice 74 line to `WORK_ITEMS.md` and prove duplicate/append/regex guards.

## 7) Risks/guardrails + fail-closed triggers
Risks and guardrails:
- Risk: unintended route or parity drift while editing route-fence rows.  
  Guardrail: owner-only mutation proof plus explicit post-change target-row invariant checks.
- Risk: accidental spillover into non-target rows.  
  Guardrail: markdown/json mutation cardinality checks limited to one changed row key (`run|profile`).
- Risk: governance drift in protected artifacts.  
  Guardrail: strict writable allowlist and out-of-scope diff checks.
- Risk: duplicate or malformed `WORK_ITEMS.md` status entry.  
  Guardrail: preexisting line count must be zero, append-only line delta must be `+1`, and required next-pointer regex must match once.

Fail-closed triggers (any trigger => stop and do not claim completion):
- Baseline mismatch for `run|profile` (`v0 | WI-00X | pending` not true pre-mutation).
- Markdown mutation cardinality mismatch (`run|profile` removed/added counts not `1/1`).
- Markdown all-row cardinality mismatch (`md_all_removed_row_count != 1` or `md_all_added_row_count != 1`).
- JSON mutation cardinality mismatch (changed row count not `1` or changed key not exactly `run|profile`).
- JSON row-key-set drift detected (`json_added_row_count != 0` or `json_removed_row_count != 0`).
- Any route change or parity-status change on `run|profile`.
- Any readiness counter drift (`ready_v0`, `ready_v1`, `pending_v0`, `pending_v1`).
- Any non-target route-fence row mutation.
- Any out-of-scope file mutation (`src/`, `tests/`, parity/workflow/verification-contract/CI files).
- Any `WORK_ITEMS.md` edit before explicit Slice 74 audit PASS.
- `WORK_ITEMS.md` pre-append guard fails (`preexisting_slice74_line_count != 0`).
- `WORK_ITEMS.md` append proof fails (`line_delta != +1`, `added_lines != 1`, or `removed_lines != 0`).
- `WORK_ITEMS.md` next-pointer regex proof fails (`slice74_work_items_next_pointer_match_count != 1`).
- Governance check failure (`readiness`, `parity`, or `all`).
- Missing Slice 74 implementation report or audit report.

## 8) Suggested next slice
- Slice 75: one-row ownership/readiness-prep follow-on for `restore|logo|thumb|backdrop|profile` with owner-only mutation intent `owner_slice: WI-00X -> Slice-75` (no route flip, no parity-status change).

## 9) Verification commands (PowerShell)
```powershell
# Baseline snapshot (before mutation; same PowerShell session)
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*profile\s*\|\s*v0\s*\|\s*WI-00X\s*\|\s*pending\s*\|'
$rfPre = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rowsPre = $rfPre.rows
$targetPre = $rowsPre | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'profile' } | Select-Object -First 1
"run_profile_precondition_ok=$($null -ne $targetPre -and $targetPre.route -eq 'v0' -and $targetPre.owner_slice -eq 'WI-00X' -and $targetPre.parity_status -eq 'pending')"
$readyV0Pre = @($rowsPre | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v0' }).Count
$readyV1Pre = @($rowsPre | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v1' }).Count
$pendingV0Pre = @($rowsPre | Where-Object { $_.parity_status -eq 'pending' -and $_.route -eq 'v0' }).Count
$pendingV1Pre = @($rowsPre | Where-Object { $_.parity_status -eq 'pending' -and $_.route -eq 'v1' }).Count
"ready_v0_pre=$readyV0Pre"
"ready_v1_pre=$readyV1Pre"
"pending_v0_pre=$pendingV0Pre"
"pending_v1_pre=$pendingV1Pre"

$preRowsByKey = @{}
foreach ($r in $rowsPre) {
  $k = "$($r.command)|$($r.mode)"
  $preRowsByKey[$k] = (ConvertTo-Json $r -Compress)
}

# Scope + protected-file drift proof
git diff --name-only
$outOfScopeDiff = @(git diff --name-only -- src tests project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml WORK_ITEMS.md)
"out_of_scope_changed_path_count=$($outOfScopeDiff.Count)"
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml src tests WORK_ITEMS.md

# One-row mutation cardinality proof (after mutation)
$mdDiff = git diff --unified=0 -- project/route-fence.md
"md_removed_run_profile_count=$((($mdDiff | Select-String -Pattern '^\-\|\s*run\s*\|\s*profile\s*\|').Matches.Count))"
"md_added_run_profile_count=$((($mdDiff | Select-String -Pattern '^\+\|\s*run\s*\|\s*profile\s*\|').Matches.Count))"
"md_all_removed_row_count=$((($mdDiff | Select-String -Pattern '^\-\|').Matches.Count))"
"md_all_added_row_count=$((($mdDiff | Select-String -Pattern '^\+\|').Matches.Count))"

$rfPost = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rowsPost = $rfPost.rows
$changedKeys = @()
foreach ($r in $rowsPost) {
  $k = "$($r.command)|$($r.mode)"
  if (-not $preRowsByKey.ContainsKey($k)) { continue }
  if ($preRowsByKey[$k] -ne (ConvertTo-Json $r -Compress)) {
    $changedKeys += $k
  }
}
"json_changed_row_count=$($changedKeys.Count)"
"json_changed_row_keys=$($changedKeys -join ',')"
"json_only_run_profile_changed=$($changedKeys.Count -eq 1 -and $changedKeys[0] -eq 'run|profile')"

# JSON add/remove drift proof (HEAD vs working-tree row-key sets)
$rfHead = ((git show HEAD:project/route-fence.json) -join "`n") | ConvertFrom-Json
$headKeys = @($rfHead.rows | ForEach-Object { "$($_.command)|$($_.mode)" } | Sort-Object -Unique)
$postKeys = @($rowsPost | ForEach-Object { "$($_.command)|$($_.mode)" } | Sort-Object -Unique)
$headKeySet = @{}
foreach ($k in $headKeys) { $headKeySet[$k] = $true }
$postKeySet = @{}
foreach ($k in $postKeys) { $postKeySet[$k] = $true }
$jsonAddedKeys = @($postKeys | Where-Object { -not $headKeySet.ContainsKey($_) })
$jsonRemovedKeys = @($headKeys | Where-Object { -not $postKeySet.ContainsKey($_) })
"json_added_row_count=$($jsonAddedKeys.Count)"
"json_removed_row_count=$($jsonRemovedKeys.Count)"
"json_added_row_keys=$($jsonAddedKeys -join ',')"
"json_removed_row_keys=$($jsonRemovedKeys -join ',')"

# Post-change invariants
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*profile\s*\|\s*v0\s*\|\s*Slice-74\s*\|\s*pending\s*\|'
$targetPost = $rowsPost | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'profile' } | Select-Object -First 1
"run_profile_route_is_v0=$($targetPost.route -eq 'v0')"
"run_profile_owner_is_slice74=$($targetPost.owner_slice -eq 'Slice-74')"
"run_profile_parity_is_pending=$($targetPost.parity_status -eq 'pending')"
"ready_v0_post=$(@($rowsPost | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v0' }).Count)"
"ready_v1_post=$(@($rowsPost | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v1' }).Count)"
"pending_v0_post=$(@($rowsPost | Where-Object { $_.parity_status -eq 'pending' -and $_.route -eq 'v0' }).Count)"
"pending_v1_post=$(@($rowsPost | Where-Object { $_.parity_status -eq 'pending' -and $_.route -eq 'v1' }).Count)"
"readiness_counters_unchanged=$($readyV0Pre -eq @($rowsPost | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v0' }).Count -and $readyV1Pre -eq @($rowsPost | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v1' }).Count -and $pendingV0Pre -eq @($rowsPost | Where-Object { $_.parity_status -eq 'pending' -and $_.route -eq 'v0' }).Count -and $pendingV1Pre -eq @($rowsPost | Where-Object { $_.parity_status -eq 'pending' -and $_.route -eq 'v1' }).Count)"

# Governance checks for touched governance artifacts
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

# Guard: WORK_ITEMS.md must remain untouched before audit PASS
git diff --name-only -- WORK_ITEMS.md
Select-String -Path project/v1-slices-reports/slice-74/slice-74-audit.md -Pattern '^Explicit verdict:\s*\*\*PASS\*\*|^Final verdict:\s*\*\*PASS\*\*'

# WORK_ITEMS append guards (post-audit orchestration step only)
"preexisting_slice74_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 74 -> ').Count)"
$beforeCount = (Get-Content WORK_ITEMS.md).Count
# ...append exactly one Slice 74 line...
$afterCount = (Get-Content WORK_ITEMS.md).Count
"work_items_line_delta=$('{0:+#;-#;0}' -f ($afterCount - $beforeCount))"
$wDiff = git diff --unified=0 -- WORK_ITEMS.md
"work_items_added_lines_count=$((($wDiff | Select-String -Pattern '^\+[^+]').Matches.Count))"
"work_items_removed_lines_count=$((($wDiff | Select-String -Pattern '^\-[^-]').Matches.Count))"
"slice74_work_items_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 74 -> ').Count)"
Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 74 -> .*next:\s*Slice 75\b.*$'
"slice74_work_items_next_pointer_match_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 74 -> .*next:\s*Slice 75\b.*$').Count)"
```

## 10) Evidence/report output paths
- Plan: `project/v1-slices-reports/slice-74/slice-74-plan.md`
- Implementation report: `project/v1-slices-reports/slice-74/slice-74-implementation.md`
- Audit report: `project/v1-slices-reports/slice-74/slice-74-audit.md`
- Governance evidence targets: `project/route-fence.md`, `project/route-fence.json`
- Post-audit orchestration update target: `WORK_ITEMS.md`

## 11) Split-if-too-large rule
Split immediately if any of the following becomes necessary:
- More than one route-fence row mutation.
- Any route flip or parity-status change.
- Any runtime/test edit.
- Any parity/workflow/verification-contract/CI edit.
- Any objective beyond one-row owner-only update (`run|profile`, `WI-00X -> Slice-74`).

If split is triggered, keep Slice 74 limited to owner-only readiness-prep evidence for `run|profile` and defer all additional work to Slice 75.
