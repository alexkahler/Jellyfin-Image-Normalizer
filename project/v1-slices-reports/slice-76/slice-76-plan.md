# Slice 76 Plan v3 (Final)

Date: 2026-03-12  
Branch: `feat/v1-overhaul`  
Planning review status: v3 final.

## 1) Slice ID/title
- Slice 76
- One-objective, single-target workflow-coverage expansion for `run|logo` (no route flip)

## 2) Goal/objective
- Add exactly one workflow-coverage cell entry for `run|logo` in `project/workflow-coverage-index.json`.
- Reuse parity-backed references:
  - `required_parity_ids`: `CLI-ASPECT-001`
  - `required_owner_tests`: `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_warns_for_unrecommended_aspect_ratio`
- Keep evidence mapping compatible with `tests/characterization/baselines/cli_contract_baseline.json#CLI-ASPECT-001`:
  - `evidence_layout.field_container=expected_stats`
  - `evidence_layout.ordering_container=expected_messages`
  - `required_evidence_fields` includes `warnings`
  - `required_ordering_tokens` includes `Unusual logo aspect ratio`
- Require fixed schema-required payload intent for the new `run|logo` cell:
  - `command=run`
  - `mode=logo`
  - `severity.contract=block`
  - `severity.sequence=warn`
  - `future_split_debt.status=closed`
  - `future_split_debt.readiness_blocking=false`
  - `future_split_debt.closure.cell=run|logo`
- Preserve route-fence target-row invariants exactly:
  - `run|logo` remains `v0 | Slice-72 | pending`
- Do not modify route-fence routes/parity/owners.

## 3) In-scope/out-of-scope
### In scope
- Slice 76 artifacts (`plan`, `implementation`, `audit`).
- Single governance mutation: one new workflow cell key `run|logo` in `project/workflow-coverage-index.json`.

### Out of scope
- Any route-fence edits (`project/route-fence.md`, `project/route-fence.json`) including route/owner/parity fields.
- Any runtime or test edits (`src/`, `tests/`).
- Any parity/verification-contract/CI edits:
  - `project/parity-matrix.md`
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
- Any extra workflow-coverage key edits beyond `run|logo`.
- Any pre-audit `WORK_ITEMS.md` mutation.

## 4) Tight role-based writable allowlist
- Planning worker: `project/v1-slices-reports/slice-76/slice-76-plan.md` only.
- Implementation worker:
  - Always allowed: `project/v1-slices-reports/slice-76/slice-76-implementation.md`.
  - Conditionally allowed: `project/workflow-coverage-index.json` for one new cell key `run|logo` only.
- Audit worker: `project/v1-slices-reports/slice-76/slice-76-audit.md` only.
- Orchestration worker (post-audit only): `WORK_ITEMS.md` append-only single-line Slice 76 status update with required next-pointer to Slice 77.

## 5) Measurable acceptance criteria
1. Workflow index diff cardinality is exact:
   - `workflow_added_cell_count=1`
   - `workflow_added_cell_keys=run|logo`
   - `workflow_removed_cell_count=0`
2. New `run|logo` cell contains required anchors exactly:
   - `required_parity_ids` includes `CLI-ASPECT-001`
   - `required_owner_tests` includes `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_warns_for_unrecommended_aspect_ratio`
3. New `run|logo` cell evidence mapping is baseline-compatible with `cli_contract_baseline.json#CLI-ASPECT-001`:
   - `field_container=expected_stats`
   - `ordering_container=expected_messages`
   - `required_evidence_fields` includes `warnings`
   - `required_ordering_tokens` includes `Unusual logo aspect ratio`
4. New `run|logo` cell enforces fixed schema-required payload intent:
   - `command=run`
   - `mode=logo`
   - `severity.contract=block`
   - `severity.sequence=warn`
   - `future_split_debt.status=closed`
   - `future_split_debt.readiness_blocking=false`
   - `future_split_debt.closure.cell=run|logo`
5. Non-target workflow-cell immutability proof is exact (HEAD vs working tree across `cells` minus `run|logo`):
   - `workflow_non_target_changed_cell_count=0`
   - `workflow_non_target_changed_cell_keys=` (empty)
6. Route-fence target row is unchanged in markdown and JSON:
   - `run|logo` remains `v0 | Slice-72 | pending`.
7. Workflow sequence counters advance by exactly `+1/+1` with debt unchanged:
   - pre: `configured=5`, `validated=5`, `open_debts=0`
   - post: `configured=6`, `validated=6`, `open_debts=0`
8. Governance checks pass:
   - `--check characterization`
   - `--check parity`
   - `--check readiness`
   - `--check all`
9. Out-of-scope protected-path diff count is exact (excludes intended mutation target `project/workflow-coverage-index.json` and excludes `WORK_ITEMS.md`, which is guarded separately):
   - `out_of_scope_changed_path_count=0`
10. Pre-audit `WORK_ITEMS.md` guard holds:
   - `pre_audit_work_items_changed_count=0`
11. Slice 76 implementation and audit reports exist with explicit PASS/FAIL semantics.
12. Post-audit `WORK_ITEMS.md` duplicate guard holds:
   - `preexisting_slice76_line_count=0`
13. Post-audit append-only guard holds:
   - `work_items_line_delta=+1`
   - `work_items_added_lines_count=1`
   - `work_items_removed_lines_count=0`
14. Post-audit next-pointer regex guard holds exactly once:
   - `^- Slice 76 -> .*next:\s*Slice 77\b.*$`
   - `slice76_work_items_next_pointer_match_count=1`

## 6) Ordered implementation steps
1. Capture baseline snapshots:
   - route-fence target row state (`run|logo -> v0 | Slice-72 | pending`) from markdown and JSON.
   - characterization counters (`configured`, `validated`, `open_debts`) from `--check characterization`.
2. Snapshot workflow-coverage key set from `HEAD` before mutation.
3. Add exactly one `run|logo` cell in `project/workflow-coverage-index.json` with required parity/test anchors and baseline-compatible evidence fields/tokens.
4. Capture workflow key-set add/remove proofs and confirm cardinality (`added=1`, `removed=0`, added key exactly `run|logo`).
5. Capture non-target workflow-cell immutability proof (`cells` minus `run|logo`) and confirm zero changed non-target keys.
6. Recheck route-fence target row unchanged and verify out-of-scope diff guard (`count=0`).
7. Run governance checks (`characterization`, `parity`, `readiness`, `all`) and record outcomes.
8. Confirm workflow counter movement exactly `5/5 -> 6/6` with open debts `0 -> 0`.
9. Write `slice-76-implementation.md` with explicit evidence, counters, and PASS/FAIL outcome.
10. Audit worker performs independent verification and writes `slice-76-audit.md` with explicit verdict.
11. After explicit audit PASS only, orchestration appends exactly one Slice 76 line to `WORK_ITEMS.md` and proves duplicate/append/regex guards.

## 7) Risks/guardrails + fail-closed triggers
Risks and guardrails:
- Risk: scope creep to multiple workflow keys.  
  Guardrail: key-set diff proof must show exactly one added key (`run|logo`) and zero removed keys.
- Risk: accidental route-fence mutation while editing governance artifacts.  
  Guardrail: explicit no-diff check for `project/route-fence.md` and `project/route-fence.json` plus row-value recheck.
- Risk: weak or incompatible evidence mapping for CLI-ASPECT baseline.  
  Guardrail: enforce baseline-compatible `expected_stats`/`expected_messages` mapping and required `warnings` + `Unusual logo aspect ratio` fields/tokens.
- Risk: premature/malformed orchestration status update.  
  Guardrail: pre-audit `WORK_ITEMS.md` no-change check and post-audit duplicate/append/regex guards.

Fail-closed triggers (any trigger => stop and do not claim completion):
- Workflow key cardinality mismatch (`added != 1`, `removed != 0`, or added key not exactly `run|logo`).
- Anchor mismatch for parity/test references (`CLI-ASPECT-001` or owner test missing/incorrect).
- Evidence-layout/field/token compatibility mismatch for `CLI-ASPECT-001`.
- Fixed schema-required payload intent mismatch for `run|logo` (`command`, `mode`, `severity`, `future_split_debt` required fields/values).
- Non-target workflow-cell drift detected (`workflow_non_target_changed_cell_count != 0`).
- Route-fence target row mismatch (not `run|logo -> v0 | Slice-72 | pending` after mutation).
- Any route-fence file diff detected.
- Workflow sequence counter mismatch (not exactly `configured +1`, `validated +1`, `open_debts unchanged`).
- Any governance check failure (`characterization`, `parity`, `readiness`, or `all`).
- Out-of-scope diff mismatch (`out_of_scope_changed_path_count != 0`).
- Pre-audit `WORK_ITEMS.md` mismatch (`pre_audit_work_items_changed_count != 0`).
- `WORK_ITEMS.md` post-audit guards fail (`preexisting_slice76_line_count != 0`, append counters mismatch, or regex count != 1).
- Missing Slice 76 implementation report or audit report.

## 8) Suggested next slice
- Slice 77: runtime-gate scope decomposition for `run|logo` claim eligibility (add the `CLI-ASPECT-001` owner test into runtime-gate targets) before any readiness-status activation attempt.

## 9) PowerShell verification commands
```powershell
# Baseline route-fence proof (before mutation)
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*logo\s*\|\s*v0\s*\|\s*Slice-72\s*\|\s*pending\s*\|'
$rfPre = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$runLogoPre = $rfPre.rows | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'logo' } | Select-Object -First 1
"run_logo_pre_ok=$($null -ne $runLogoPre -and $runLogoPre.route -eq 'v0' -and $runLogoPre.owner_slice -eq 'Slice-72' -and $runLogoPre.parity_status -eq 'pending')"

# Baseline characterization counters (before mutation)
$charPre = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
$cfgPre = [int](($charPre | Select-String -Pattern 'Workflow sequence cells configured:\s*(\d+)').Matches[0].Groups[1].Value)
$valPre = [int](($charPre | Select-String -Pattern 'Workflow sequence cells validated:\s*(\d+)').Matches[0].Groups[1].Value)
$debtPre = [int](($charPre | Select-String -Pattern 'Workflow sequence open debts:\s*(\d+)').Matches[0].Groups[1].Value)
"workflow_configured_pre=$cfgPre"
"workflow_validated_pre=$valPre"
"workflow_open_debts_pre=$debtPre"

# Workflow index key-set diff cardinality (HEAD vs working tree)
$wcHead = ((git show HEAD:project/workflow-coverage-index.json) -join "`n") | ConvertFrom-Json
$wcPost = Get-Content -Raw project/workflow-coverage-index.json | ConvertFrom-Json
$headKeys = @($wcHead.cells.PSObject.Properties.Name | Sort-Object -Unique)
$postKeys = @($wcPost.cells.PSObject.Properties.Name | Sort-Object -Unique)
$headSet = @{}; foreach ($k in $headKeys) { $headSet[$k] = $true }
$postSet = @{}; foreach ($k in $postKeys) { $postSet[$k] = $true }
$addedKeys = @($postKeys | Where-Object { -not $headSet.ContainsKey($_) })
$removedKeys = @($headKeys | Where-Object { -not $postSet.ContainsKey($_) })
"workflow_added_cell_count=$($addedKeys.Count)"
"workflow_added_cell_keys=$($addedKeys -join ',')"
"workflow_removed_cell_count=$($removedKeys.Count)"
"workflow_removed_cell_keys=$($removedKeys -join ',')"
"workflow_only_run_logo_added=$($addedKeys.Count -eq 1 -and $addedKeys[0] -eq 'run|logo' -and $removedKeys.Count -eq 0)"

# Non-target workflow-cell immutability (HEAD vs working tree across cells minus run|logo)
$nonTargetChangedKeys = @()
$nonTargetKeys = @($headKeys | Where-Object { $_ -ne 'run|logo' })
foreach ($k in $nonTargetKeys) {
  if (-not ($postSet.ContainsKey($k))) { continue }
  $headCellJson = ConvertTo-Json $wcHead.cells.$k -Depth 20 -Compress
  $postCellJson = ConvertTo-Json $wcPost.cells.$k -Depth 20 -Compress
  if ($headCellJson -ne $postCellJson) {
    $nonTargetChangedKeys += $k
  }
}
"workflow_non_target_changed_cell_count=$($nonTargetChangedKeys.Count)"
"workflow_non_target_changed_cell_keys=$($nonTargetChangedKeys -join ',')"

# Target cell anchor + baseline-compatibility proof
$cell = $wcPost.cells.'run|logo'
$cell | ConvertTo-Json -Depth 10
"has_cli_aspect_parity_id=$($cell.required_parity_ids -contains 'CLI-ASPECT-001')"
"has_cli_aspect_owner_test=$($cell.required_owner_tests -contains 'tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_warns_for_unrecommended_aspect_ratio')"
"field_container_expected_stats=$($cell.evidence_layout.field_container -eq 'expected_stats')"
"ordering_container_expected_messages=$($cell.evidence_layout.ordering_container -eq 'expected_messages')"
"required_field_warnings_present=$($cell.required_evidence_fields -contains 'warnings')"
"required_token_present=$($cell.required_ordering_tokens -contains 'Unusual logo aspect ratio')"
"cell_command_is_run=$($cell.command -eq 'run')"
"cell_mode_is_logo=$($cell.mode -eq 'logo')"
"cell_severity_contract_block=$($cell.severity.contract -eq 'block')"
"cell_severity_sequence_warn=$($cell.severity.sequence -eq 'warn')"
"cell_future_split_debt_status_closed=$($cell.future_split_debt.status -eq 'closed')"
"cell_future_split_debt_readiness_blocking_false=$($cell.future_split_debt.readiness_blocking -eq $false)"
"cell_future_split_debt_closure_cell_run_logo=$($cell.future_split_debt.closure.cell -eq 'run|logo')"

# Route-fence target row unchanged (after mutation)
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*logo\s*\|\s*v0\s*\|\s*Slice-72\s*\|\s*pending\s*\|'
$rfPost = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$runLogoPost = $rfPost.rows | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'logo' } | Select-Object -First 1
"run_logo_post_ok=$($null -ne $runLogoPost -and $runLogoPost.route -eq 'v0' -and $runLogoPost.owner_slice -eq 'Slice-72' -and $runLogoPost.parity_status -eq 'pending')"
$routeFenceDiff = @(git diff --name-only -- project/route-fence.md project/route-fence.json)
"route_fence_changed_path_count=$($routeFenceDiff.Count)"

# Out-of-scope protected-path diff guard (excludes intended mutation target `project/workflow-coverage-index.json` and excludes `WORK_ITEMS.md`, which is guarded separately below)
$outOfScopeDiff = @(git diff --name-only -- src tests project/route-fence.md project/route-fence.json project/parity-matrix.md project/verification-contract.yml .github/workflows/ci.yml)
"out_of_scope_changed_path_count=$($outOfScopeDiff.Count)"

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

# Post-mutation counter proof (+1/+1 with open debts unchanged)
$charPost = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
$cfgPost = [int](($charPost | Select-String -Pattern 'Workflow sequence cells configured:\s*(\d+)').Matches[0].Groups[1].Value)
$valPost = [int](($charPost | Select-String -Pattern 'Workflow sequence cells validated:\s*(\d+)').Matches[0].Groups[1].Value)
$debtPost = [int](($charPost | Select-String -Pattern 'Workflow sequence open debts:\s*(\d+)').Matches[0].Groups[1].Value)
"workflow_configured_post=$cfgPost"
"workflow_validated_post=$valPost"
"workflow_open_debts_post=$debtPost"
"workflow_configured_delta=$($cfgPost - $cfgPre)"
"workflow_validated_delta=$($valPost - $valPre)"
"workflow_open_debts_delta=$($debtPost - $debtPre)"

# Pre-audit WORK_ITEMS guard
$preAuditWorkItemsDiff = @(git diff --name-only -- WORK_ITEMS.md)
"pre_audit_work_items_changed_count=$($preAuditWorkItemsDiff.Count)"
Select-String -Path project/v1-slices-reports/slice-76/slice-76-audit.md -Pattern '^Explicit verdict:\s*\*\*PASS\*\*|^Final verdict:\s*\*\*PASS\*\*|^Verdict:\s*PASS'

# WORK_ITEMS append guards (post-audit orchestration step only)
"preexisting_slice76_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 76 -> ').Count)"
$beforeCount = (Get-Content WORK_ITEMS.md).Count
# ...append exactly one Slice 76 line...
$afterCount = (Get-Content WORK_ITEMS.md).Count
"work_items_line_delta=$('{0:+#;-#;0}' -f ($afterCount - $beforeCount))"
$wDiff = git diff --unified=0 -- WORK_ITEMS.md
"work_items_added_lines_count=$((($wDiff | Select-String -Pattern '^\+[^+]').Matches.Count))"
"work_items_removed_lines_count=$((($wDiff | Select-String -Pattern '^\-[^-]').Matches.Count))"
"slice76_work_items_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 76 -> ').Count)"
Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 76 -> .*next:\s*Slice 77\b.*$'
"slice76_work_items_next_pointer_match_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 76 -> .*next:\s*Slice 77\b.*$').Count)"
```

## 10) Evidence/report output paths
- Plan: `project/v1-slices-reports/slice-76/slice-76-plan.md`
- Implementation report: `project/v1-slices-reports/slice-76/slice-76-implementation.md`
- Audit report: `project/v1-slices-reports/slice-76/slice-76-audit.md`
- Governance mutation target: `project/workflow-coverage-index.json`
- Invariant proof targets: `project/route-fence.md`, `project/route-fence.json`
- Post-audit orchestration target: `WORK_ITEMS.md`

## 11) Split-if-too-large rule
Split immediately if any of the following becomes necessary:
- More than one workflow cell addition/removal/rewire.
- Any route-fence route/owner/parity mutation.
- Any runtime/test/parity/verification-contract/CI edit.
- Any objective beyond one-cell workflow-coverage expansion for `run|logo`.

If split is triggered, keep Slice 76 limited to one `run|logo` workflow-cell addition plus slice-report evidence, and defer all additional work to Slice 77.
