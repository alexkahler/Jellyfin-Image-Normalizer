# Slice 77 Plan v3

Date: 2026-03-12  
Branch: `feat/v1-overhaul`  
Planning review status: v3 (final)

## Review checklist compliance
- PASS - scope bounded (in/out): single-objective runtime-gate target addition only.
- PASS - files touched bounded: explicit max implementation mutation set and no-mutation list defined.
- PASS - slice id/title present: Section 1 names Slice 77 and title.
- PASS - objective clear: Section 2 states one target-add objective and preserved invariants.
- PASS - acceptance criteria measurable: Section 5 defines counter- and regex-based checks.
- PASS - implementation steps ordered: Section 6 is sequential and evidence-driven.
- PASS - risk/guardrails + fail-closed present: Section 7 includes both.
- PASS - suggested next slice present: Section 8 defines Slice 78.
- PASS - split-if-too-large rule present: Section 11 defines split triggers.

Final planning verdict: PASS - scoped and approved for implementation worker.

## 1) Slice ID/title
- Slice 77
- Runtime-gate scope decomposition for `run|logo` claim eligibility (no route flip)

## 2) Goal/objective
- Add exactly one runtime-gate target required for `run|logo` owner-test eligibility:
  - `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_warns_for_unrecommended_aspect_ratio`
- Keep runtime-gate budget unchanged at `180` seconds.
- Keep route-fence and parity/readiness surfaces unchanged (no route flips, no owner changes, no parity-status flips).

## 3) In-scope/out-of-scope
### In scope
- Slice 77 artifacts (`plan`, `implementation`, `audit`).
- Runtime-gate target synchronization in exactly these implementation surfaces:
  - `project/verification-contract.yml`
  - `project/scripts/governance_contract.py`
  - `tests/test_governance_checks.py`
- Post-audit orchestrator append-only one-line `WORK_ITEMS.md` update.

### Out of scope
- No mutation to:
  - `project/route-fence.md`
  - `project/route-fence.json`
  - `project/parity-matrix.md`
  - `project/workflow-coverage-index.json`
  - `.github/workflows/ci.yml`
  - `AGENTS.md`
  - `project/v1-plan.md`
  - `tests/characterization/**`
  - `src/**`
- Any runtime-gate budget change from `180`.
- Any pre-audit `WORK_ITEMS.md` edit.

## 4) Tight role-based writable allowlist
- Planning worker: `project/v1-slices-reports/slice-77/slice-77-plan.md` only.
- Implementation worker:
  - Max mutation statement: implementation mutation files are exactly 4 files total:
    - `project/verification-contract.yml`
    - `project/scripts/governance_contract.py`
    - `tests/test_governance_checks.py`
    - `project/v1-slices-reports/slice-77/slice-77-implementation.md`
  - No additional implementation file mutations are allowed.
- Audit worker: `project/v1-slices-reports/slice-77/slice-77-audit.md` only.
- Orchestration worker (post-audit only): append exactly one Slice 77 line to `WORK_ITEMS.md` with next pointer to Slice 78.

## 5) Clear measurable acceptance criteria
1. Runtime-gate target list mutation cardinality is exact:
   - `runtime_gate_added_target_count=1`
   - `runtime_gate_removed_target_count=0`
   - `runtime_gate_added_target_value=tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_warns_for_unrecommended_aspect_ratio`
   - existing pre-slice target order remains unchanged (`runtime_gate_existing_order_preserved=True`).
2. Added target appears consistently across all three touched files:
   - `project/verification-contract.yml`
   - `project/scripts/governance_contract.py`
   - `tests/test_governance_checks.py`
   - and `runtime_gate_lists_consistent_after_change=True`.
3. Runtime-gate budget remains `180` across contract/parser/schema expectations:
   - `characterization_runtime_gate_budget_seconds: 180` in `project/verification-contract.yml`
   - `EXPECTED_RUNTIME_GATE_BUDGET_SECONDS = 180` in `project/scripts/governance_contract.py`
   - runtime-gate budget default remains `180` in `tests/test_governance_checks.py` helper.
4. Route-fence target row `run|logo` is unchanged in markdown and JSON:
   - `run|logo -> v0 | Slice-72 | pending`.
5. Readiness counters remain unchanged pre/post.
6. Governance checks pass:
   - `--check characterization`
   - `--check parity`
   - `--check readiness`
   - `--check all`
7. Runtime-gate counters advance exactly as required:
   - configured `4 -> 5`
   - checked `4 -> 5`
   - passed `4 -> 5`
   - failed remains `0 -> 0`.
8. Out-of-scope changed-path counter is exact:
   - `out_of_scope_changed_path_count=0`.
9. Pre-audit `WORK_ITEMS.md` guard is exact:
   - `pre_audit_work_items_changed_count=0`.
10. Post-audit `WORK_ITEMS.md` append guards pass:
    - `preexisting_slice77_line_count=0`
    - `work_items_line_delta=+1`
    - `work_items_added_lines_count=1`
    - `work_items_removed_lines_count=0`
11. Post-audit next-pointer regex guard passes exactly once:
    - `^- Slice 77 -> .*next:\s*Slice 78\b.*$`
    - `slice77_work_items_next_pointer_match_count=1`.
12. Implementation mutation path count is exact before audit file and `WORK_ITEMS.md` updates:
    - `implementation_mutated_paths_count=4`
    - exact set equals `{project/verification-contract.yml, project/scripts/governance_contract.py, tests/test_governance_checks.py, project/v1-slices-reports/slice-77/slice-77-implementation.md}`.

## 6) Ordered implementation steps
1. Capture pre-mutation runtime-gate counters (`configured/checked/passed/failed`) from `--check characterization`.
2. Capture pre-mutation readiness counters from `--check readiness`.
3. Capture pre-mutation route-fence `run|logo` row proof from markdown and JSON.
4. Snapshot runtime-gate target list from `HEAD` and from working-tree `project/verification-contract.yml`.
5. Add exactly one runtime-gate target in `project/verification-contract.yml`:
   - `tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_warns_for_unrecommended_aspect_ratio`.
6. Mirror the same added target in:
   - `project/scripts/governance_contract.py` (`EXPECTED_RUNTIME_GATE_TARGETS`)
   - `tests/test_governance_checks.py` (`_contract_text` default `runtime_targets`).
7. Confirm cross-file target-list consistency and budget invariants (`180`) across the three touched files.
8. Run governance checks (`characterization`, `parity`, `readiness`, `all`) and record outputs.
9. Confirm post-mutation runtime-gate counter movement (`4/4/4/0 -> 5/5/5/0`) and unchanged readiness counters.
10. Prove route-fence `run|logo` row unchanged and out-of-scope diff count `0`.
11. Write `slice-77-implementation.md` with explicit PASS/FAIL evidence.
12. Audit worker independently verifies all acceptance checks and writes `slice-77-audit.md` with explicit PASS/FAIL verdict.
13. After explicit audit PASS only, orchestration appends exactly one Slice 77 line to `WORK_ITEMS.md` and proves duplicate/append/regex guards.

## 7) Risks/guardrails + fail-closed triggers
Risks and guardrails:
- Risk: list drift beyond one target (removal/reorder/multi-add).  
  Guardrail: enforce add/remove/order cardinality proof with exact target identity.
- Risk: unsynced runtime-gate lists across contract/schema/test defaults.  
  Guardrail: parse and compare all three lists; require exact equality post-change.
- Risk: accidental route-fence/readiness/parity mutation while touching governance files.  
  Guardrail: explicit unchanged-row checks for `run|logo` plus out-of-scope diff counter `0`.
- Risk: premature or malformed `WORK_ITEMS.md` updates.  
  Guardrail: pre-audit no-change proof and post-audit append/regex guards.

Fail-closed triggers (any trigger => stop and do not claim completion):
- `runtime_gate_added_target_count != 1`.
- `runtime_gate_removed_target_count != 0`.
- `runtime_gate_added_target_value` is not exactly the required owner test.
- Existing target order is not preserved.
- Any inconsistency between runtime-gate lists across the three touched files.
- Runtime-gate budget is not `180` in any required expectation surface.
- `run|logo` row is not exactly `v0 | Slice-72 | pending` in either route-fence artifact.
- Readiness counters change pre/post.
- Runtime-gate counters do not move exactly `4/4/4/0 -> 5/5/5/0`.
- Any governance check fails (`characterization`, `parity`, `readiness`, or `all`).
- `out_of_scope_changed_path_count != 0`.
- `pre_audit_work_items_changed_count != 0`.
- Post-audit `WORK_ITEMS.md` guard failures:
  - `preexisting_slice77_line_count != 0`
  - `work_items_line_delta != +1`
  - `work_items_added_lines_count != 1`
  - `work_items_removed_lines_count != 0`
  - `slice77_work_items_next_pointer_match_count != 1`.
- Missing Slice 77 implementation report or audit report.

## 8) Suggested next slice
- Slice 78: readiness-claim activation step for `run|logo` (pending -> ready eligibility claim path) only after Slice 77 audit PASS and with route unchanged (`v0`).

## 9) PowerShell verification commands
```powershell
$target = 'tests/characterization/cli_contract/test_cli_contract_characterization.py::test_cli_warns_for_unrecommended_aspect_ratio'

function Get-ContractRuntimeTargetsFromText([string]$text) {
  $targets = @()
  $inBlock = $false
  foreach ($line in ($text -split "`r?`n")) {
    if ($line -match '^characterization_runtime_gate_targets:\s*$') {
      $inBlock = $true
      continue
    }
    if (-not $inBlock) { continue }
    if ($line -match '^\s*-\s*(.+?)\s*$') {
      $targets += $Matches[1].Trim()
      continue
    }
    if ($line -match '^\S') { break }
  }
  return ,$targets
}

function Get-PythonListLiteralItems([string]$text, [string]$pattern) {
  $match = [regex]::Match($text, $pattern)
  if (-not $match.Success) { return @() }
  $body = $match.Groups[1].Value
  $items = @()
  foreach ($m in [regex]::Matches($body, '["'']([^"''\r\n]+)["'']')) {
    $items += $m.Groups[1].Value
  }
  return ,$items
}

# Baseline runtime-gate + readiness counters (before mutation)
$charPre = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
$rgCfgPre = [int](($charPre | Select-String -Pattern 'Characterization runtime gate targets configured:\s*(\d+)').Matches[0].Groups[1].Value)
$rgChkPre = [int](($charPre | Select-String -Pattern 'Characterization runtime gate targets checked:\s*(\d+)').Matches[0].Groups[1].Value)
$rgPassPre = [int](($charPre | Select-String -Pattern 'Characterization runtime gate targets passed:\s*(\d+)').Matches[0].Groups[1].Value)
$rgFailPre = [int](($charPre | Select-String -Pattern 'Characterization runtime gate targets failed:\s*(\d+)').Matches[0].Groups[1].Value)
"runtime_gate_configured_pre=$rgCfgPre"
"runtime_gate_checked_pre=$rgChkPre"
"runtime_gate_passed_pre=$rgPassPre"
"runtime_gate_failed_pre=$rgFailPre"

$readPre = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
$readClaimsPre = [int](($readPre | Select-String -Pattern 'Route readiness claims:\s*(\d+)').Matches[0].Groups[1].Value)
$readValidatedPre = [int](($readPre | Select-String -Pattern 'Route readiness claims validated:\s*(\d+)').Matches[0].Groups[1].Value)
"readiness_claims_pre=$readClaimsPre"
"readiness_validated_pre=$readValidatedPre"

# Route-fence invariant baseline (before mutation)
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*logo\s*\|\s*v0\s*\|\s*Slice-72\s*\|\s*pending\s*\|'
$rfPre = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$runLogoPre = $rfPre.rows | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'logo' } | Select-Object -First 1
"run_logo_pre_ok=$($null -ne $runLogoPre -and $runLogoPre.route -eq 'v0' -and $runLogoPre.owner_slice -eq 'Slice-72' -and $runLogoPre.parity_status -eq 'pending')"

# Runtime-gate list mutation cardinality (HEAD vs working tree contract)
$contractHeadText = ((git show HEAD:project/verification-contract.yml) -join "`n")
$contractPostText = Get-Content -Raw project/verification-contract.yml
$targetsPre = Get-ContractRuntimeTargetsFromText $contractHeadText
$targetsPost = Get-ContractRuntimeTargetsFromText $contractPostText
$targetSetPre = @{}; foreach ($t in $targetsPre) { $targetSetPre[$t] = $true }
$targetSetPost = @{}; foreach ($t in $targetsPost) { $targetSetPost[$t] = $true }
$addedTargets = @($targetsPost | Where-Object { -not $targetSetPre.ContainsKey($_) })
$removedTargets = @($targetsPre | Where-Object { -not $targetSetPost.ContainsKey($_) })
$existingOrderPreserved = $true
if ($targetsPre.Count -gt $targetsPost.Count) {
  $existingOrderPreserved = $false
} else {
  for ($i = 0; $i -lt $targetsPre.Count; $i++) {
    if ($targetsPre[$i] -ne $targetsPost[$i]) { $existingOrderPreserved = $false; break }
  }
}
"runtime_gate_added_target_count=$($addedTargets.Count)"
"runtime_gate_removed_target_count=$($removedTargets.Count)"
"runtime_gate_added_target_value=$($addedTargets -join ',')"
"runtime_gate_existing_order_preserved=$existingOrderPreserved"

# Cross-file target-list consistency check (three touched files)
$gcText = Get-Content -Raw project/scripts/governance_contract.py
$testsText = Get-Content -Raw tests/test_governance_checks.py
$gcTargets = Get-PythonListLiteralItems $gcText '(?s)EXPECTED_RUNTIME_GATE_TARGETS\s*=\s*\[(.*?)\]'
$testsTargets = Get-PythonListLiteralItems $testsText '(?s)runtime_targets\s*=\s*runtime_gate_targets\s*or\s*\[(.*?)\]'
$contractSig = ($targetsPost -join '||')
$gcSig = ($gcTargets -join '||')
$testsSig = ($testsTargets -join '||')
"target_present_contract=$($targetsPost -contains $target)"
"target_present_governance_contract=$($gcTargets -contains $target)"
"target_present_tests_helper=$($testsTargets -contains $target)"
"runtime_gate_lists_consistent_after_change=$($contractSig -eq $gcSig -and $contractSig -eq $testsSig)"

# Budget invariants (must remain 180 everywhere)
"contract_budget_180=$([regex]::IsMatch($contractPostText, '(?m)^characterization_runtime_gate_budget_seconds:\s*180\s*$'))"
"governance_contract_budget_180=$([regex]::IsMatch($gcText, '(?m)^EXPECTED_RUNTIME_GATE_BUDGET_SECONDS = 180\s*$'))"
"tests_helper_budget_180=$([regex]::IsMatch($testsText, 'runtime_gate_budget_seconds:\s*int\s*=\s*180'))"

# Governance checks
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

# Post-mutation runtime-gate + readiness deltas (after mutation)
$charPost = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
$rgCfgPost = [int](($charPost | Select-String -Pattern 'Characterization runtime gate targets configured:\s*(\d+)').Matches[0].Groups[1].Value)
$rgChkPost = [int](($charPost | Select-String -Pattern 'Characterization runtime gate targets checked:\s*(\d+)').Matches[0].Groups[1].Value)
$rgPassPost = [int](($charPost | Select-String -Pattern 'Characterization runtime gate targets passed:\s*(\d+)').Matches[0].Groups[1].Value)
$rgFailPost = [int](($charPost | Select-String -Pattern 'Characterization runtime gate targets failed:\s*(\d+)').Matches[0].Groups[1].Value)
"runtime_gate_configured_post=$rgCfgPost"
"runtime_gate_checked_post=$rgChkPost"
"runtime_gate_passed_post=$rgPassPost"
"runtime_gate_failed_post=$rgFailPost"
"runtime_gate_configured_delta=$($rgCfgPost - $rgCfgPre)"
"runtime_gate_checked_delta=$($rgChkPost - $rgChkPre)"
"runtime_gate_passed_delta=$($rgPassPost - $rgPassPre)"
"runtime_gate_failed_delta=$($rgFailPost - $rgFailPre)"

$readPost = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check readiness
$readClaimsPost = [int](($readPost | Select-String -Pattern 'Route readiness claims:\s*(\d+)').Matches[0].Groups[1].Value)
$readValidatedPost = [int](($readPost | Select-String -Pattern 'Route readiness claims validated:\s*(\d+)').Matches[0].Groups[1].Value)
"readiness_claims_post=$readClaimsPost"
"readiness_validated_post=$readValidatedPost"
"readiness_claims_delta=$($readClaimsPost - $readClaimsPre)"
"readiness_validated_delta=$($readValidatedPost - $readValidatedPre)"

# Route-fence invariant recheck (after mutation)
Select-String -Path project/route-fence.md -Pattern '^\|\s*run\s*\|\s*logo\s*\|\s*v0\s*\|\s*Slice-72\s*\|\s*pending\s*\|'
$rfPost = Get-Content -Raw project/route-fence.json | ConvertFrom-Json
$runLogoPost = $rfPost.rows | Where-Object { $_.command -eq 'run' -and $_.mode -eq 'logo' } | Select-Object -First 1
"run_logo_post_ok=$($null -ne $runLogoPost -and $runLogoPost.route -eq 'v0' -and $runLogoPost.owner_slice -eq 'Slice-72' -and $runLogoPost.parity_status -eq 'pending')"

# Out-of-scope diff guard (pre/post audit)
$allowed = @(
  'project/verification-contract.yml',
  'project/scripts/governance_contract.py',
  'tests/test_governance_checks.py',
  'project/v1-slices-reports/slice-77/slice-77-plan.md',
  'project/v1-slices-reports/slice-77/slice-77-implementation.md',
  'project/v1-slices-reports/slice-77/slice-77-audit.md',
  'WORK_ITEMS.md'
)
$changed = @(git diff --name-only)
$outOfScope = @($changed | Where-Object { $_ -notin $allowed })
"out_of_scope_changed_path_count=$($outOfScope.Count)"

# Pre-audit WORK_ITEMS guard
$preAuditWorkItemsDiff = @(git diff --name-only -- WORK_ITEMS.md)
"pre_audit_work_items_changed_count=$($preAuditWorkItemsDiff.Count)"
Select-String -Path project/v1-slices-reports/slice-77/slice-77-audit.md -Pattern '^Explicit verdict:\s*\*\*PASS\*\*|^Final verdict:\s*\*\*PASS\*\*|^Verdict:\s*PASS'

# WORK_ITEMS append guards (post-audit orchestration only)
"preexisting_slice77_line_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 77 -> ').Count)"
$beforeCount = (Get-Content WORK_ITEMS.md).Count
# ...append exactly one Slice 77 line...
$afterCount = (Get-Content WORK_ITEMS.md).Count
"work_items_line_delta=$('{0:+#;-#;0}' -f ($afterCount - $beforeCount))"
$wDiff = git diff --unified=0 -- WORK_ITEMS.md
"work_items_added_lines_count=$((($wDiff | Select-String -Pattern '^\+[^+]').Matches.Count))"
"work_items_removed_lines_count=$((($wDiff | Select-String -Pattern '^\-[^-]').Matches.Count))"
Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 77 -> .*next:\s*Slice 78\b.*$'
"slice77_work_items_next_pointer_match_count=$((Select-String -Path WORK_ITEMS.md -Pattern '^- Slice 77 -> .*next:\s*Slice 78\b.*$').Count)"
```

## 10) Evidence/report output paths
- Plan: `project/v1-slices-reports/slice-77/slice-77-plan.md`
- Implementation report: `project/v1-slices-reports/slice-77/slice-77-implementation.md`
- Audit report: `project/v1-slices-reports/slice-77/slice-77-audit.md`
- Implementation mutation surfaces:
  - `project/verification-contract.yml`
  - `project/scripts/governance_contract.py`
  - `tests/test_governance_checks.py`
- Invariant proof surfaces:
  - `project/route-fence.md`
  - `project/route-fence.json`
- Post-audit orchestration target: `WORK_ITEMS.md`

## 11) Split-if-too-large rule
Split immediately if any of the following becomes necessary:
- More than one runtime-gate target addition/removal/reorder.
- Any route-fence row change, owner change, route flip, or parity-status flip.
- Any workflow/parity/readiness topology mutation.
- Any runtime code or characterization-suite behavior edits.
- Any runtime-gate budget change from `180`.

If split is triggered, keep Slice 77 limited to one objective: add only the `test_cli_warns_for_unrecommended_aspect_ratio` runtime-gate target with three-file synchronization and required slice-report evidence; defer all additional work to Slice 78.

