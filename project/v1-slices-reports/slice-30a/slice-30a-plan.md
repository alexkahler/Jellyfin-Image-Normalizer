# Slice-30a Plan (v3)

## Slice Id and Title
- Slice id: `Slice-30a`
- Slice title: `Runtime evasion remediation tranche 3a (cli.py first, decomposed)`

## Baseline and Context Lock
- Branch baseline: `v1/thm-a-governance-contract-posture-recovery`.
- Baseline `HEAD`: `7e35f1e`.
- Slice-30 is blocked/nonclosable and remains historical evidence only.
- Starting worktree is intentionally unclean due historical evidence under `project/v1-slices-reports/slice-30/`; preserve it exactly as-is and do not delete, rewrite, or commit it in this slice.
- Precondition: the only allowed pre-existing unclean path is `project/v1-slices-reports/slice-30/`; if any other pre-existing dirt is present, stop immediately and document it before proceeding.
- Timing rule for pre-existing dirt check: run this check at start-of-slice baseline capture before creating/modifying Slice-30a artifacts, or compare against a recorded pre-slice snapshot captured at that time.
- Theme A and `A-08` remain open after this slice.

## Objective
- Remove anti-evasion suppression from `src/jfin/cli.py`.
- Achieve honest, formatter-compatible `<=300` LOC for `src/jfin/cli.py`.
- Preserve behavior and signatures for CLI entry flow.
- Avoid substantive `src/jfin/cli_runtime.py` changes; defer runtime tranche work to Slice-30b.
- Scope guard: no `src/jfin/cli_runtime.py` edits except trivial import/compile compatibility; if more is required, hard-stop and split to Slice-30b.

## In Scope / Out of Scope
- In scope:
  - Behavior-preserving structural remediation in `src/jfin/cli.py` only.
  - Anti-evasion suppression removal for `cli.py` only.
  - Honest LOC reduction in `cli.py` via formatter-compatible refactor.
- Out of scope:
  - Substantive `src/jfin/cli_runtime.py` code changes.
  - Any pipeline tranche work (`pipeline.py`, `pipeline_backdrops.py`).
  - Route-fence/governance redesign or closure claims.
  - Any attempt to close Theme A or `A-08`.
  - Editing historical Slice-30 evidence content.

## Pre-Slice Baseline Capture (cli.py Anti-Evasion State)
- Capture and record the baseline before any runtime edit:
  - `src/jfin/cli.py` currently contains `# fmt: off` (anti-evasion marker).
  - Baseline offender set must include:
    - `src/jfin/cli.py`
    - `src/jfin/cli_runtime.py`
    - `src/jfin/pipeline.py`
    - `src/jfin/pipeline_backdrops.py`
- Baseline capture is mandatory evidence for this plan and is a precondition for implementation.

## Strategy (Honest Structural LOC Reduction)
1. Remove `# fmt: off`/`# fmt: on` from `src/jfin/cli.py`.
2. Apply formatter-compatible structural consolidation inside `cli.py` only:
   - Extract repeated CLI argument-token validation loop logic into one private helper.
   - Keep existing public function names/signatures and exit semantics unchanged (`parse_args`, `main`, `validate_*` entry points).
   - Consolidate repetitive warning/allow-list declarations where behavior is identical.
3. Keep `cli.py` readable and honest under formatter; no suppression or packing tricks.

## Disallowed Tactics
- `# fmt: off` / `# fmt: on` suppression.
- Multi-statement semicolon packing.
- Dense inline control-flow suite packing.

## Acceptance Criteria
- `src/jfin/cli.py` has no formatter suppression markers.
- `src/jfin/cli.py` is honest formatted LOC `<=300`.
- CLI behavior/signatures remain unchanged.
- `src/jfin/cli_runtime.py` has no substantive changes in this slice.
- Post-success anti-evasion offender set is exactly:
  - `src/jfin/cli_runtime.py`
  - `src/jfin/pipeline.py`
  - `src/jfin/pipeline_backdrops.py`
- Exact remaining-offender assertion must also confirm these files are not flagged:
  - `src/jfin/cli.py`
  - `src/jfin/client.py`
  - `src/jfin/client_http.py`
- No unexpected anti-evasion offender expansion.
- Theme A and `A-08` remain open.

## Deliverables
- `project/v1-slices-reports/slice-30a/slice-30a-plan.md`
- `project/v1-slices-reports/slice-30a/slice-30a-implementation.md`
- `project/v1-slices-reports/slice-30a/slice-30a-audit.md`

## Verification Ownership
- Workers may run provisional checks during implementation.
- The main orchestration agent must run authoritative verification gates before audit and before commit.

## Exact Verification Commands
```powershell
$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = 'src'

$expectedBaselineOffenders = @(
  'src/jfin/cli.py',
  'src/jfin/cli_runtime.py',
  'src/jfin/pipeline.py',
  'src/jfin/pipeline_backdrops.py'
)

$expectedRemaining = @(
  'src/jfin/cli_runtime.py',
  'src/jfin/pipeline.py',
  'src/jfin/pipeline_backdrops.py'
)

$expectedCleared = @('src/jfin/cli.py')
$expectedNotFlagged = @(
  'src/jfin/cli.py',
  'src/jfin/client.py',
  'src/jfin/client_http.py'
)
$allowedRuntimeTouches = @('src/jfin/cli.py')
$preSliceSnapshotPath = 'project/v1-slices-reports/slice-30a/pre-slice-status.txt'

function Get-AntiEvasionOffenders {
  param([string]$Text)
  [regex]::Matches($Text, 'src/jfin/[A-Za-z0-9_]+\.py(?=\s+\[anti_evasion\.)') |
    ForEach-Object { $_.Value } |
    Sort-Object -Unique
}

function Assert-OffenderSetExact {
  param(
    [string]$CheckName,
    [int]$ExitCode,
    [string]$OutputText,
    [string[]]$Expected
  )

  if ($ExitCode -eq 0) {
    throw "Expected $CheckName to remain non-zero while anti-evasion offenders still exist."
  }

  $offenders = Get-AntiEvasionOffenders -Text $OutputText
  "[$CheckName] offenders: $($offenders -join ', ')"

  $diff = Compare-Object -ReferenceObject ($Expected | Sort-Object -Unique) -DifferenceObject $offenders
  if ($diff) {
    $diff | Format-Table -AutoSize
    throw "$CheckName offender set mismatch."
  }
}

# 0) Baseline lock
$branch = git rev-parse --abbrev-ref HEAD
$head = git rev-parse --short=7 HEAD
if ($branch -ne 'v1/thm-a-governance-contract-posture-recovery') {
  throw "Unexpected branch baseline: $branch"
}
if ($head -ne '7e35f1e') {
  throw "Unexpected baseline HEAD: $head"
}
git status --short
git status --short -- project/v1-slices-reports/slice-30
# Run at slice start before modifying Slice-30a files. If resuming later,
# validate against the recorded pre-slice snapshot.
if (Test-Path $preSliceSnapshotPath) {
  $preExisting = Get-Content $preSliceSnapshotPath
} else {
  $preExisting = git status --porcelain
  $preExisting | Set-Content $preSliceSnapshotPath
}
$invalidPreExisting = $preExisting |
  Where-Object { $_ -and $_ -notmatch 'project/v1-slices-reports/slice-30/' }
if ($invalidPreExisting) {
  $invalidPreExisting
  throw 'Precondition failed: pre-existing dirt exists outside project/v1-slices-reports/slice-30/. Stop and document.'
}

# 1) Pre-slice baseline capture for cli.py anti-evasion state
$fmtBefore = rg -n "#\s*fmt:\s*(off|on)" src/jfin/cli.py
if ($LASTEXITCODE -ne 0) {
  throw "Baseline missing expected cli.py suppression marker."
}
$fmtBefore
"cli.py pre-change LOC=$((Get-Content src/jfin/cli.py).Length)"

$baselineLocOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc 2>&1
$baselineLocExit = $LASTEXITCODE
$baselineLocText = $baselineLocOutput | Out-String
$baselineLocText
Assert-OffenderSetExact -CheckName 'baseline --check loc' -ExitCode $baselineLocExit -OutputText $baselineLocText -Expected $expectedBaselineOffenders

# 2) Post-change cli.py anti-evasion + honest LOC checks
$fmtAfter = rg -n "#\s*fmt:\s*(off|on)" src/jfin/cli.py
if ($LASTEXITCODE -eq 0) {
  $fmtAfter
  throw 'Formatter suppression remains in src/jfin/cli.py.'
}

$cliLoc = (Get-Content src/jfin/cli.py).Length
"cli.py LOC=$cliLoc"
if ($cliLoc -gt 300) {
  throw 'src/jfin/cli.py exceeds 300 LOC.'
}

.\.venv\Scripts\python.exe -m ruff check src/jfin/cli.py --select E701,E702,E703
.\.venv\Scripts\python.exe -m ruff format --check src/jfin/cli.py

# 3) Targeted CLI regression checks
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q `
  tests/characterization/cli_contract/test_cli_contract_characterization.py `
  tests/test_jfin.py `
  tests/test_config.py

# 4) Governance offender assertions
$locOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc 2>&1
$locExit = $LASTEXITCODE
$locText = $locOutput | Out-String
$locText
Assert-OffenderSetExact -CheckName '--check loc' -ExitCode $locExit -OutputText $locText -Expected $expectedRemaining

$allOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all 2>&1
$allExit = $LASTEXITCODE
$allText = $allOutput | Out-String
$allText
Assert-OffenderSetExact -CheckName '--check all' -ExitCode $allExit -OutputText $allText -Expected $expectedRemaining

$allOffenders = Get-AntiEvasionOffenders -Text $allText
$stillFlaggedCleared = $expectedCleared | Where-Object { $_ -in $allOffenders }
if ($stillFlaggedCleared.Count -gt 0) {
  throw "Cleared target still flagged: $($stillFlaggedCleared -join ', ')"
}
$stillFlaggedNotAllowed = $expectedNotFlagged | Where-Object { $_ -in $allOffenders }
if ($stillFlaggedNotAllowed.Count -gt 0) {
  throw "Expected non-flagged file still present in offender set: $($stillFlaggedNotAllowed -join ', ')"
}

# 5) AGENTS.md required repository verification command set
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit

# 6) Scope control evidence
git diff --numstat -- src
$srcTouched = git diff --name-only -- src
$unexpected = $srcTouched | Where-Object { $_ -notin $allowedRuntimeTouches }
if ($unexpected) {
  throw "Out-of-scope src touches: $($unexpected -join ', ')"
}
if ($srcTouched -contains 'src/jfin/cli_runtime.py') {
  throw 'cli_runtime.py edits beyond trivial import/compile compatibility are out of scope for Slice-30a; hard-stop and split to Slice-30b.'
}

# 7) Preserve blocked Slice-30 historical evidence
git status --short -- project/v1-slices-reports/slice-30
```

## Rollback Plan
- If post-change verification fails before commit: restore `src/jfin/cli.py` to baseline and rerun baseline capture commands.
- If the slice commit exists: `git revert <slice-30a-commit-sha>`, then rerun:
  - targeted CLI tests,
  - `project/scripts/verify_governance.py --check loc`,
  - `project/scripts/verify_governance.py --check all`.
- Never delete or rewrite `project/v1-slices-reports/slice-30/` during rollback.

## Stop / Split Rules
- Stop immediately if honest formatter-compatible `cli.py <=300` cannot be achieved without behavior/signature risk.
- Stop immediately if remediation requires any `src/jfin/cli_runtime.py` edits beyond trivial import/compile compatibility.
- Stop immediately if anti-evasion offender set after verification is not exactly the expected post-success set.
- Stop immediately on any unexpected `src/` file touch outside `src/jfin/cli.py`.
- If any stop condition triggers, mark Slice-30a blocked and split forward instead of widening scope.

## Failure Path (Blocked Slice-30a)
- If Slice-30a cannot satisfy acceptance criteria, fail closed and make no closable-slice claim.
- Record blocked-state artifacts in `project/v1-slices-reports/slice-30a/`:
  - `slice-30a-plan.md` (blocked update)
  - `slice-30a-implementation.md` (blocked evidence and rollback state)
  - `slice-30a-audit.md` (independent blocked verdict)
- Preserve historical Slice-30 evidence and Theme A / `A-08` open status.

## Explicit Next Slice Statement
- `Slice-30b Runtime evasion remediation tranche 3b (cli_runtime.py)`
- Why: after successful Slice-30a, `cli_runtime.py` remains an expected anti-evasion offender and needs its own isolated, behavior-preserving remediation tranche to satisfy LOC/anti-evasion contract without scope mixing.
