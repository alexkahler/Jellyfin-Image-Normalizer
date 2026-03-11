# Slice 75 Plan v3 (Final)

Date: 2026-03-11  
Branch: `feat/v1-overhaul`  
Planning review status: v3 final.

## 1) Slice ID/title
- Slice 75
- One-row ownership/readiness-prep follow-on for `restore|logo|thumb|backdrop|profile` (no route flip)

## 2) Goal/objective
- Complete one bounded objective: ownership/readiness-prep follow-on for route-fence row `restore|logo|thumb|backdrop|profile`.
- Apply exactly one owner-only mutation in both route-fence artifacts:
  - `owner_slice: WI-00X -> Slice-75`
- Preserve target-row invariants:
  - `route` remains `v0`
  - `parity_status` remains `pending`

## 3) In-scope/out-of-scope
### In scope
- Slice 75 artifacts (`plan`, `implementation`, `audit`).
- Single target-row owner mutation for `restore|logo|thumb|backdrop|profile` in:
  - `project/route-fence.md`
  - `project/route-fence.json`
- Evidence capture proving exact one-row mutation cardinality and no non-target row changes.

### Out of scope
- Any route flip (including target row).
- Any parity-status change (including target row).
- Any non-target route-fence row mutation.
- Any runtime/test edits (`src/`, `tests/`).
- Any parity/workflow/verification-contract/CI edits:
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
- Any pre-audit `WORK_ITEMS.md` mutation.

## 4) Tight role-based writable allowlist
- Planning worker: `project/v1-slices-reports/slice-75/slice-75-plan.md` only.
- Implementation worker:
  - Always allowed: `project/v1-slices-reports/slice-75/slice-75-implementation.md`.
  - Conditionally allowed: `project/route-fence.md`, `project/route-fence.json` for one-row owner update only (`restore|logo|thumb|backdrop|profile`, `WI-00X -> Slice-75`).
- Audit worker: `project/v1-slices-reports/slice-75/slice-75-audit.md` only.
- Orchestration worker (post-audit only): `WORK_ITEMS.md` append-only single-line Slice 75 status update with required next-pointer to Slice 76.

## 5) Measurable acceptance criteria
1. Pre-mutation baseline is proven in both route-fence artifacts:
   - `restore|logo|thumb|backdrop|profile -> route=v0, owner_slice=WI-00X, parity_status=pending`.
2. Pre-mutation readiness counters are captured:
   - `ready_v0`, `ready_v1`, `pending_v0`, `pending_v1`.
3. Exactly one owner-only mutation is applied in both route-fence artifacts:
   - `owner_slice: WI-00X -> Slice-75` for target row only.
4. Markdown target-row mutation cardinality is exact:
   - `md_removed_target_row_count=1`
   - `md_added_target_row_count=1`
5. Markdown total-row mutation cardinality is exact:
   - `md_all_removed_row_count=1`
   - `md_all_added_row_count=1`
6. JSON changed-key mutation cardinality is exact:
   - `json_changed_row_count=1`
   - `json_changed_row_keys=restore|logo|thumb|backdrop|profile`
7. JSON key-set drift guard is fail-closed:
   - `json_added_row_count=0`
   - `json_removed_row_count=0`
8. Target-row invariants are preserved post-mutation:
   - `route=v0`, `parity_status=pending`, `owner_slice=Slice-75`.
9. Pre/post readiness counters remain unchanged.
10. No non-target route-fence row changes occur.
11. Out-of-scope protection is proven measurable from the counted out-of-scope diff set (explicitly excluding `WORK_ITEMS.md`):
   - `out_of_scope_changed_path_count=0`.
12. Dedicated pre-audit `WORK_ITEMS.md` guard remains explicit and measurable:
   - `pre_audit_work_items_changed_count=0` until explicit Slice 75 audit PASS.
13. Governance checks pass:
   - `--check readiness`
   - `--check parity`
   - `--check all`
14. Slice 75 implementation and audit reports exist with explicit PASS/FAIL verdict semantics.
15. Post-audit append duplicate guard passes:
   - `preexisting_slice75_line_count=0`
16. Post-audit append-only guard passes:
   - `work_items_line_delta=+1`
   - `work_items_added_lines_count=1`
   - `work_items_removed_lines_count=0`
   - `slice75_work_items_line_count=1`
17. Appended Slice 75 line matches required next-pointer regex exactly once:
   - `^- Slice 75 -> .*next:\s*Slice 76\b.*$`
   - `slice75_work_items_next_pointer_match_count=1`

## 6) Ordered implementation steps
1. Capture baseline evidence for target row from `project/route-fence.md` and `project/route-fence.json`.
2. Capture pre-mutation readiness counters (`ready_v0`, `ready_v1`, `pending_v0`, `pending_v1`).
3. Capture pre-mutation row-key snapshots and out-of-scope/pre-audit `WORK_ITEMS.md` no-change baseline.
4. Apply one-row owner-only mutation in both route-fence artifacts:
   - `owner_slice: WI-00X -> Slice-75` on `restore|logo|thumb|backdrop|profile` only.
5. Capture markdown mutation cardinality proofs (target-row and total-row counts).
6. Capture JSON mutation proofs:
   - changed-key cardinality (`count=1`, exact key match),
   - key-set add/remove counts (`0/0` fail-closed).
7. Verify post-mutation invariants:
   - target row remains `v0 | Slice-75 | pending`,
   - readiness counters unchanged.
8. Run governance checks (`readiness`, `parity`, `all`) and capture outputs.
9. Write `slice-75-implementation.md` with evidence and explicit outcome.
10. Audit worker performs independent verification and writes `slice-75-audit.md` with explicit verdict.
11. After explicit audit PASS only, orchestration appends exactly one Slice 75 line to `WORK_ITEMS.md` and proves duplicate/append/regex guards.

## 7) Risks/guardrails + fail-closed triggers
Risks and guardrails:
- Risk: unintended route/parity drift while editing route-fence rows.  
  Guardrail: owner-only mutation proof plus explicit target-row invariants (`route=v0`, `parity_status=pending`) before/after.
- Risk: accidental spillover to non-target rows.  
  Guardrail: markdown total-row cardinality and JSON changed-key cardinality must both prove single-row scope.
- Risk: hidden JSON structure drift.  
  Guardrail: JSON row-key add/remove counts must remain `0/0` (fail-closed).
- Risk: premature or malformed orchestration update in `WORK_ITEMS.md`.  
  Guardrail: pre-audit no-change proof plus post-audit duplicate/append/regex guards.

Fail-closed triggers (any trigger => stop and do not claim completion):
- Baseline mismatch for `restore|logo|thumb|backdrop|profile` (`v0 | WI-00X | pending` not true pre-mutation).
- Markdown target-row cardinality mismatch (`md_removed_target_row_count != 1` or `md_added_target_row_count != 1`).
- Markdown total-row cardinality mismatch (`md_all_removed_row_count != 1` or `md_all_added_row_count != 1`).
- JSON changed-key cardinality mismatch (`json_changed_row_count != 1` or changed key not exactly `restore|logo|thumb|backdrop|profile`).
- JSON row-key-set drift (`json_added_row_count != 0` or `json_removed_row_count != 0`).
- Any target-row route/parity drift (`route != v0` or `parity_status != pending`).
- Any readiness counter drift (`ready_v0`, `ready_v1`, `pending_v0`, `pending_v1` changed).
- Any non-target route-fence row mutation.
- Out-of-scope counter mismatch (`out_of_scope_changed_path_count != 0`).
- Pre-audit `WORK_ITEMS.md` counter mismatch (`pre_audit_work_items_changed_count != 0`).
- `WORK_ITEMS.md` pre-append guard fails (`preexisting_slice75_line_count != 0`).
- `WORK_ITEMS.md` append-only guard fails (`work_items_line_delta != +1`, `work_items_added_lines_count != 1`, or `work_items_removed_lines_count != 0`).
- `WORK_ITEMS.md` next-pointer regex guard fails (`slice75_work_items_next_pointer_match_count != 1` for `^- Slice 75 -> .*next:\s*Slice 76\b.*$`).
- Governance check failure (`readiness`, `parity`, or `all`).
- Missing Slice 75 implementation report or audit report.

## 8) Suggested next slice
- Slice 76: one-objective, single-target follow-on for `run|logo` only, with strict file-discipline (no route flip, no parity-status change, no out-of-scope edits).

## 9) Verification commands (PowerShell)
```powershell
# Baseline snapshot (before mutation; same PowerShell session)
Select-String -Path project/route-fence.md -Pattern '^\|\s*restore\s*\|\s*logo\\\|thumb\\\|backdrop\\\|profile\s*\|\s*v0\s*\|\s*WI-00X\s*\|\s*pending\s*\|'
$rfPre = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rowsPre = $rfPre.rows
$targetKey = 'restore|logo|thumb|backdrop|profile'
$targetPre = $rowsPre | Where-Object { "$($_.command)|$($_.mode)" -eq $targetKey } | Select-Object -First 1
"target_precondition_ok=$($null -ne $targetPre -and $targetPre.route -eq 'v0' -and $targetPre.owner_slice -eq 'WI-00X' -and $targetPre.parity_status -eq 'pending')"
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

# Scope + pre-audit guards (`out_of_scope_changed_path_count` excludes `WORK_ITEMS.md`)
git diff --name-only
$outOfScopeDiff = @(git diff --name-only -- src tests project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml)
"out_of_scope_changed_path_count=$($outOfScopeDiff.Count)"
# Dedicated `WORK_ITEMS.md` pre-audit guard (separate from out-of-scope counted set)
$preAuditWorkItemsDiff = @(git diff --name-only -- WORK_ITEMS.md)
"pre_audit_work_items_changed_count=$($preAuditWorkItemsDiff.Count)"
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml src tests WORK_ITEMS.md

# One-row mutation cardinality proof (after mutation)
$mdDiff = git diff --unified=0 -- project/route-fence.md
"md_removed_target_row_count=$((($mdDiff | Select-String -Pattern '^\-\|\s*restore\s*\|\s*logo\\\|thumb\\\|backdrop\\\|profile\s*\|').Matches.Count))"
"md_added_target_row_count=$((($mdDiff | Select-String -Pattern '^\+\|\s*restore\s*\|\s*logo\\\|thumb\\\|backdrop\\\|profile\s*\|').Matches.Count))"
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
"json_only_target_changed=$($changedKeys.Count -eq 1 -and $changedKeys[0] -eq $targetKey)"

# JSON add/remove key-set drift proof (HEAD vs working-tree)
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

# Post-change invariants + readiness counters unchanged
Select-String -Path project/route-fence.md -Pattern '^\|\s*restore\s*\|\s*logo\\\|thumb\\\|backdrop\\\|profile\s*\|\s*v0\s*\|\s*Slice-75\s*\|\s*pending\s*\|'
$targetPost = $rowsPost | Where-Object { "$($_.command)|$($_.mode)" -eq $targetKey } | Select-Object -First 1
"target_route_is_v0=$($targetPost.route -eq 'v0')"
"target_owner_is_slice75=$($targetPost.owner_slice -eq 'Slice-75')"
"target_parity_is_pending=$($targetPost.parity_status -eq 'pending')"
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
$preAuditWorkItemsDiff = @(git diff --name-only -- WORK_ITEMS.md)
"pre_audit_work_items_changed_count=$($preAuditWorkItemsDiff.Count)"
Select-String -Path project/v1-slices-reports/slice-75/slice-75-audit.md -Pattern '^Explicit verdict:\s*\*\*PASS\*\*|^Final verdict:\s*\*\*PASS\*\*'

# WORK_ITEMS append guards (post-audit orchestration step only)
"preexisting_slice75_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 75 -> ').Count)"
$beforeCount = (Get-Content WORK_ITEMS.md).Count
# ...append exactly one Slice 75 line...
$afterCount = (Get-Content WORK_ITEMS.md).Count
"work_items_line_delta=$('{0:+#;-#;0}' -f ($afterCount - $beforeCount))"
$wDiff = git diff --unified=0 -- WORK_ITEMS.md
"work_items_added_lines_count=$((($wDiff | Select-String -Pattern '^\+[^+]').Matches.Count))"
"work_items_removed_lines_count=$((($wDiff | Select-String -Pattern '^\-[^-]').Matches.Count))"
"slice75_work_items_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 75 -> ').Count)"
Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 75 -> .*next:\s*Slice 76\b.*$'
"slice75_work_items_next_pointer_match_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 75 -> .*next:\s*Slice 76\b.*$').Count)"
```

## 10) Evidence/report output paths
- Plan: `project/v1-slices-reports/slice-75/slice-75-plan.md`
- Implementation report: `project/v1-slices-reports/slice-75/slice-75-implementation.md`
- Audit report: `project/v1-slices-reports/slice-75/slice-75-audit.md`
- Governance evidence targets: `project/route-fence.md`, `project/route-fence.json`
- Post-audit orchestration update target: `WORK_ITEMS.md`

## 11) Split-if-too-large rule
Split immediately if any of the following becomes necessary:
- More than one route-fence row mutation.
- Any route flip or parity-status change.
- Any runtime/test edit.
- Any parity/workflow/verification-contract/CI edit.
- Any objective beyond one-row owner-only update for `restore|logo|thumb|backdrop|profile` (`WI-00X -> Slice-75`).

If split is triggered, keep Slice 75 limited to owner-only readiness-prep evidence for `restore|logo|thumb|backdrop|profile` and defer all additional work to Slice 76.
