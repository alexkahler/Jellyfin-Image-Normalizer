# Slice 72 Plan v3 (Final) - One-Row Ownership/Readiness-Prep Follow-On for `run|logo` (No Route Flip)

Date: 2026-03-11  
Branch: `feat/v1-overhaul`  
Planning review status: v3 final.

## 1) Slice ID/title
- Slice 72
- One-row ownership/readiness-prep follow-on for `run|logo` (no route flip)

## 2) Goal/objective
- Complete one bounded objective: ownership/readiness-prep follow-on for route-fence row `run|logo`.
- Prefer ownership-only mutation aligned to this objective:
  - `owner_slice: WI-00X -> Slice-72`
- Preserve non-target fields:
  - `route` stays `v0`
  - `parity_status` stays `pending`

## 3) In-scope/out-of-scope
### In scope
- Slice 72 artifacts (`plan`, `implementation`, `audit`).
- Single target-row ownership mutation for `run|logo` in both route-fence artifacts.
- Evidence capture proving no route flip and no out-of-scope mutation.

### Out of scope
- Any route flip (including `run|logo`).
- Any runtime/test source edits (`src/`, `tests/`).
- Any parity/workflow/verification-contract/CI mutation:
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
- Any non-target route-fence row mutation.

## 4) Tight role-based writable allowlist
- Planning worker: `project/v1-slices-reports/slice-72/slice-72-plan.md` only.
- Implementation worker:
  - Always allowed: `project/v1-slices-reports/slice-72/slice-72-implementation.md`.
  - Conditionally allowed: `project/route-fence.md`, `project/route-fence.json` for one-row `run|logo` owner update only (`WI-00X -> Slice-72`).
- Audit worker: `project/v1-slices-reports/slice-72/slice-72-audit.md` only.
- Orchestration-only post-audit path: `WORK_ITEMS.md` status/next-pointer update (no historical rewrites).

## 5) Measurable acceptance criteria
1. Pre-mutation baseline is proven in both route-fence artifacts as:
   - `run|logo -> route=v0, owner_slice=WI-00X, parity_status=pending`.
2. Pre-mutation readiness claim counters are captured from route-fence JSON snapshot:
   - `ready_v0`, `ready_v1`, `pending_v0`, `pending_v1`.
3. Exactly one target-row owner update is applied in both route-fence artifacts:
   - `run|logo owner_slice: WI-00X -> Slice-72`.
4. Markdown route-fence diff cardinality is exact:
   - exactly one removed target row (`run|logo` old row),
   - exactly one added target row (`run|logo` updated row).
5. JSON route-fence mutation cardinality is exact:
   - exactly one changed row object,
   - changed key is only `run|logo`.
6. `run|logo` non-target fields are unchanged in both artifacts:
   - `route=v0`, `parity_status=pending`.
7. Readiness claim counters remain unchanged versus pre-mutation snapshot.
8. No other route-fence rows change.
9. No out-of-scope file mutations occur (`src/`, `tests/`, parity/workflow/verification-contract/CI files).
10. Governance checks pass for touched governance artifacts:
   - `--check readiness`
   - `--check parity`
   - `--check all`
11. Slice 72 implementation and audit reports exist with explicit PASS/FAIL verdict semantics.
12. Post-audit orchestration pre-append duplicate guard is satisfied:
   - `preexisting_slice72_line_count=0`.
13. If `WORK_ITEMS.md` is updated post-audit, append-only single-line behavior is proven:
   - `slice72_work_items_line_count=1`
   - `work_items_line_delta=+1`
   - `work_items_added_lines_count=1`
   - `work_items_removed_lines_count=0`

## 6) Ordered implementation steps
1. Capture baseline row evidence for `run|logo` from markdown and JSON route-fence artifacts.
2. Capture pre-mutation readiness counter snapshot (`ready_v0`, `ready_v1`, `pending_v0`, `pending_v1`) from route-fence JSON.
3. Confirm clean scope guardrails and protected-file no-change baseline.
4. Apply one-row ownership-only update for `run|logo` in `project/route-fence.md` and `project/route-fence.json`.
5. Capture one-row mutation cardinality proofs:
   - markdown diff: one removed + one added `run|logo` row,
   - JSON comparison: one changed row object (`run|logo`) only.
6. Verify readiness counters are unchanged from pre-mutation snapshot.
7. Run governance checks (`readiness`, `parity`, `all`) and record outputs.
8. Write `slice-72-implementation.md` with evidence and outcome.
9. Audit worker performs independent verification and writes `slice-72-audit.md` with explicit verdict.

## 7) Risks/guardrails + fail-closed triggers
Risks and guardrails:
- Risk: unintended route progression while touching route-fence rows.  
  Guardrail: enforce owner-only mutation proof and explicit `route=v0` invariant.
- Risk: accidental spread into additional pending rows.  
  Guardrail: single-target-row diff checks for `run|logo` only.
- Risk: governance drift via unrelated artifact edits.  
  Guardrail: strict writable allowlist + protected-file diff proof.

Fail-closed triggers (any trigger => stop and do not claim completion):
- Baseline mismatch for `run|logo` precondition (`v0 | WI-00X | pending`).
- Markdown mutation cardinality mismatch (not exactly one removed + one added `run|logo` row).
- JSON mutation cardinality mismatch (changed row count != 1 or changed key != `run|logo`).
- Any route change on `run|logo` or parity-status drift.
- Readiness counter drift after mutation (`ready_v0`, `ready_v1`, `pending_v0`, `pending_v1` not unchanged).
- Any non-target route-fence row mutation.
- Any edit to out-of-scope files (`src/`, `tests/`, parity/workflow/verification-contract/CI).
- Any `WORK_ITEMS.md` edit before explicit Slice 72 audit PASS.
- `WORK_ITEMS.md` pre-append duplicate guard fails (`preexisting_slice72_line_count != 0`).
- `WORK_ITEMS.md` post-append proof fails (`slice72_work_items_line_count != 1`, `work_items_line_delta != +1`, `work_items_added_lines_count != 1`, or `work_items_removed_lines_count != 0`).
- Governance check failure (`readiness`, `parity`, or `all`).
- Missing Slice 72 implementation or audit artifact.

## 8) Suggested next slice
- Slice 73: repeat the same ownership/readiness-prep pattern for the smallest remaining pending placeholder-owner row (`run|thumb`), still no route flip.

## 9) Verification commands (PowerShell)
```powershell
# Baseline snapshot (run before mutation in same PowerShell session)
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*logo\s*\|\s*v0\s*\|\s*WI-00X\s*\|\s*pending\s*\|'
$rfPre = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$rowsPre = $rfPre.rows
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

# Scope + protected-file diff proof
git diff --name-only
git diff -- project/route-fence.md project/route-fence.json project/parity-matrix.md project/workflow-coverage-index.json project/verification-contract.yml .github/workflows/ci.yml src tests WORK_ITEMS.md

# One-row mutation cardinality proof (run after mutation)
$mdDiff = git diff --unified=0 -- project/route-fence.md
"md_removed_run_logo_count=$((($mdDiff | Select-String -Pattern '^\-\|\s*run\s*\|\s*logo\s*\|').Matches.Count))"
"md_added_run_logo_count=$((($mdDiff | Select-String -Pattern '^\+\|\s*run\s*\|\s*logo\s*\|').Matches.Count))"

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
"json_only_run_logo_changed=$($changedKeys.Count -eq 1 -and $changedKeys[0] -eq 'run|logo')"

# Post-change row + readiness invariants
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*logo\s*\|\s*v0\s*\|\s*Slice-72\s*\|\s*pending\s*\|'
$rowsPost | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'logo' } |
  Select-Object command, mode, route, owner_slice, parity_status
"ready_v0_post=$(@($rowsPost | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v0' }).Count)"
"ready_v1_post=$(@($rowsPost | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v1' }).Count)"
"pending_v0_post=$(@($rowsPost | Where-Object { $_.parity_status -eq 'pending' -and $_.route -eq 'v0' }).Count)"
"pending_v1_post=$(@($rowsPost | Where-Object { $_.parity_status -eq 'pending' -and $_.route -eq 'v1' }).Count)"
"readiness_counters_unchanged=$($readyV0Pre -eq @($rowsPost | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v0' }).Count -and $readyV1Pre -eq @($rowsPost | Where-Object { $_.parity_status -eq 'ready' -and $_.route -eq 'v1' }).Count -and $pendingV0Pre -eq @($rowsPost | Where-Object { $_.parity_status -eq 'pending' -and $_.route -eq 'v0' }).Count -and $pendingV1Pre -eq @($rowsPost | Where-Object { $_.parity_status -eq 'pending' -and $_.route -eq 'v1' }).Count)"

# Governance checks for touched governance artifacts
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

# Guard: WORK_ITEMS must remain untouched before audit PASS
git diff --name-only -- WORK_ITEMS.md

# Audit PASS gate proof
Select-String -Path project/v1-slices-reports/slice-72/slice-72-audit.md -Pattern '^Explicit verdict:\s*\*\*PASS\*\*|^Final verdict:\s*\*\*PASS\*\*'

# WORK_ITEMS append guards (post-audit orchestration step)
"preexisting_slice72_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 72 -> ').Count)"
$beforeCount = (Get-Content WORK_ITEMS.md).Count
# ...append exactly one Slice 72 line...
$afterCount = (Get-Content WORK_ITEMS.md).Count
"work_items_line_delta=$('{0:+#;-#;0}' -f ($afterCount - $beforeCount))"
$wDiff = git diff --unified=0 -- WORK_ITEMS.md
"work_items_added_lines_count=$((($wDiff | Select-String -Pattern '^\+[^+]').Matches.Count))"
"work_items_removed_lines_count=$((($wDiff | Select-String -Pattern '^\-[^-]').Matches.Count))"
"slice72_work_items_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 72 -> ').Count)"
```

## 10) Evidence/report output paths
- Plan: `project/v1-slices-reports/slice-72/slice-72-plan.md`
- Implementation report: `project/v1-slices-reports/slice-72/slice-72-implementation.md`
- Audit report: `project/v1-slices-reports/slice-72/slice-72-audit.md`
- Target governance evidence artifacts: `project/route-fence.md`, `project/route-fence.json`

## 11) Split-if-too-large rule
Split immediately if any of the following is required:
- More than one row mutation.
- Any route flip or parity-state change.
- Any runtime/test edits.
- Any parity/workflow/verification-contract/CI mutation.

If split is triggered, keep Slice 72 limited to `run|logo` ownership/readiness-prep evidence and defer additional work to the next numbered slice.
