# Slice 74 Implementation Report (v3 final)

Date: 2026-03-11  
Scope: One-row owner-only route-fence mutation for `run|profile` (`WI-00X -> Slice-74`) with no route flip and no parity-status change.

## 1) Baseline precondition evidence in md/json (pre-mutation)

Command evidence:

```powershell
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*profile\s*\|\s*v0\s*\|\s*WI-00X\s*\|\s*pending\s*\|'
$rfPre = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rowsPre = $rfPre.rows
$targetPre = $rowsPre | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'profile' } | Select-Object -First 1
"run_profile_precondition_ok=$($null -ne $targetPre -and $targetPre.route -eq 'v0' -and $targetPre.owner_slice -eq 'WI-00X' -and $targetPre.parity_status -eq 'pending')"
"run_profile_json_pre=$($targetPre | ConvertTo-Json -Compress)"
```

Output:

```text
project\route-fence.md:16:| run | profile | v0 | WI-00X | pending |
run_profile_precondition_ok=True
run_profile_json_pre={"command":"run","mode":"profile","route":"v0","owner_slice":"WI-00X","parity_status":"pending"}
```

## 2) Pre/post readiness counters + unchanged assertion

Command evidence:

```powershell
# pre
"ready_v0_pre=$readyV0Pre"
"ready_v1_pre=$readyV1Pre"
"pending_v0_pre=$pendingV0Pre"
"pending_v1_pre=$pendingV1Pre"

# post
"ready_v0_post=$readyV0Post"
"ready_v1_post=$readyV1Post"
"pending_v0_post=$pendingV0Post"
"pending_v1_post=$pendingV1Post"
"readiness_counters_unchanged=$($readyV0Pre -eq $readyV0Post -and $readyV1Pre -eq $readyV1Post -and $pendingV0Pre -eq $pendingV0Post -and $pendingV1Pre -eq $pendingV1Post)"
```

Output:

```text
ready_v0_pre=0
ready_v1_pre=4
pending_v0_pre=4
pending_v1_pre=0
ready_v0_post=0
ready_v1_post=4
pending_v0_post=4
pending_v1_post=0
readiness_counters_unchanged=True
```

## 3) Markdown cardinality evidence (`removed_target=1`, `added_target=1`, `all_removed=1`, `all_added=1`)

Command evidence:

```powershell
$mdDiff = git diff --unified=0 -- project/route-fence.md
"removed_target=$((($mdDiff | Select-String -Pattern '^\-\|\s*run\s*\|\s*profile\s*\|').Matches.Count))"
"added_target=$((($mdDiff | Select-String -Pattern '^\+\|\s*run\s*\|\s*profile\s*\|').Matches.Count))"
"all_removed=$((($mdDiff | Select-String -Pattern '^\-\|').Matches.Count))"
"all_added=$((($mdDiff | Select-String -Pattern '^\+\|').Matches.Count))"
```

Output:

```text
removed_target=1
added_target=1
all_removed=1
all_added=1
```

## 4) JSON changed-key cardinality evidence (`changed_count=1`, key=`run|profile`)

Command evidence:

```powershell
$headRows = (((git show HEAD:project/route-fence.json) -join "`n") | ConvertFrom-Json).rows
$postRows = (Get-Content -Raw project/route-fence.json | ConvertFrom-Json).rows
$headByKey = @{}
foreach($r in $headRows){ $headByKey["$($r.command)|$($r.mode)"] = (ConvertTo-Json $r -Compress) }
$changed = @()
foreach($r in $postRows){
  $k = "$($r.command)|$($r.mode)"
  if($headByKey.ContainsKey($k) -and $headByKey[$k] -ne (ConvertTo-Json $r -Compress)){ $changed += $k }
}
"changed_count=$($changed.Count)"
"changed_key=$($changed -join ',')"
```

Output:

```text
changed_count=1
changed_key=run|profile
```

## 5) JSON add/remove key-set drift evidence

Command evidence:

```powershell
$headKeys = @($headRows | ForEach-Object { "$($_.command)|$($_.mode)" } | Sort-Object -Unique)
$postKeys = @($postRows | ForEach-Object { "$($_.command)|$($_.mode)" } | Sort-Object -Unique)
$headSet = @{}; foreach($k in $headKeys){ $headSet[$k] = $true }
$postSet = @{}; foreach($k in $postKeys){ $postSet[$k] = $true }
$added = @($postKeys | Where-Object { -not $headSet.ContainsKey($_) })
$removed = @($headKeys | Where-Object { -not $postSet.ContainsKey($_) })
"json_added_row_count=$($added.Count)"
"json_removed_row_count=$($removed.Count)"
```

Output:

```text
json_added_row_count=0
json_removed_row_count=0
```

## 6) Target invariants + protected out-of-scope no-change proof (including `WORK_ITEMS.md`)

Target invariant evidence:

```powershell
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*profile\s*\|\s*v0\s*\|\s*Slice-74\s*\|\s*pending\s*\|'
$targetPost = $rowsPost | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'profile' } | Select-Object -First 1
"run_profile_route_is_v0=$($targetPost.route -eq 'v0')"
"run_profile_owner_is_slice74=$($targetPost.owner_slice -eq 'Slice-74')"
"run_profile_parity_is_pending=$($targetPost.parity_status -eq 'pending')"
"json_only_run_profile_changed=$($changed.Count -eq 1 -and $changed[0] -eq 'run|profile')"
```

Output:

```text
project\route-fence.md:16:| run | profile | v0 | Slice-74 | pending |
run_profile_route_is_v0=True
run_profile_owner_is_slice74=True
run_profile_parity_is_pending=True
json_only_run_profile_changed=True
```

Protected out-of-scope no-change evidence:

```powershell
git diff --name-only
$outOfScopeDiff = @(git diff --name-only -- src tests project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml WORK_ITEMS.md)
"out_of_scope_changed_path_count=$($outOfScopeDiff.Count)"
$workItemsDiff = @(git diff --name-only -- WORK_ITEMS.md)
"work_items_changed_path_count=$($workItemsDiff.Count)"
```

Output:

```text
project/route-fence.json
project/route-fence.md
out_of_scope_changed_path_count=0
work_items_changed_path_count=0
```

## 7) Governance checks pass (`--check readiness`, `--check parity`, `--check all`)

Executed commands:

```powershell
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

Concrete output:

```text
[PASS] readiness
Governance checks passed with 0 warning(s).
[PASS] parity
Governance checks passed with 0 warning(s).
[PASS] schema
[PASS] ci-sync
[PASS] loc
[PASS] python-version
[PASS] architecture
[PASS] parity
[PASS] characterization
[PASS] readiness
Governance checks passed with 11 warning(s).
```

## 8) Final implementation verdict

Explicit verdict: **PASS**

Slice 74 implementation requirements were satisfied:
- exactly one owner-only mutation on `run|profile`: `owner_slice WI-00X -> Slice-74`,
- target row invariants preserved: `route=v0`, `parity_status=pending`,
- no non-target row changes,
- readiness counters unchanged,
- no protected out-of-scope file changes (including `WORK_ITEMS.md`),
- governance checks passed (`readiness`, `parity`, `all`).
