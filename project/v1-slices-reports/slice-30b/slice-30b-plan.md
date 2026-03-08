# Slice-30b Plan (v3)

## Slice Id and Title
- Slice id: `Slice-30b`
- Slice title: `Runtime evasion remediation tranche 3b (cli_runtime.py)`

## Baseline and Context Lock
- Branch baseline: `v1/thm-a-governance-contract-posture-recovery`.
- Baseline `HEAD`: `500a3cd`.
- Pre-slice cleanliness evidence must come from an orchestrator-captured snapshot at slice start, before implementation edits.
- Slice-start snapshot file: `project/v1-slices-reports/slice-30b/pre-slice-status.txt`.
- If slice-start status is clean, persist sentinel `<clean>` in the snapshot file.
- Slice-30 historical artifacts are committed history and must not be reinterpreted or edited.
- Slice-30a is already closed in commit `ec9edba`; `src/jfin/cli.py` is considered cleared for this tranche.
- Theme A and `A-08` remain open before and after this slice.

## Objective
- Remove anti-evasion formatter suppression from `src/jfin/cli_runtime.py`.
- Keep `src/jfin/cli_runtime.py` honest, formatter-compatible, and `<=300` LOC.
- Preserve CLI/config/runtime behavior and function signatures.
- Keep scope to one objective; do not widen to pipeline remediation.

## In Scope / Out of Scope
In scope:
- `src/jfin/cli_runtime.py` behavior-preserving anti-evasion remediation.
- Minimal adjacent helper module extraction only if required to keep honest formatter-compatible LOC `<=300`.
- Slice-30b reporting artifacts.

Out of scope:
- Pipeline remediation (`src/jfin/pipeline.py`, `src/jfin/pipeline_backdrops.py`).
- Route-fence redesign, Theme A/A-08 closure, and same-SHA CI proof.
- Any substantive `src/jfin/cli.py` edits (except trivial import compatibility if strictly required).

## Pre-Slice Baseline Capture (Mandatory)
Capture and record baseline evidence for `src/jfin/cli_runtime.py` before implementation edits:
- Create `project/v1-slices-reports/slice-30b/pre-slice-status.txt` from `git status --porcelain` at slice start.
- If `git status --porcelain` returns no lines, write sentinel `<clean>` to the snapshot file.
- Suppression state (`# fmt: off` / `# fmt: on`) in `cli_runtime.py`.
- Honest LOC count for `cli_runtime.py`.
- Governance anti-evasion offender set from `verify_governance --check loc`.
- Baseline offender set assertion for Slice-30b start must be exactly `src/jfin/cli_runtime.py`, `src/jfin/pipeline.py`, and `src/jfin/pipeline_backdrops.py`.

## Refactor Strategy (Behavior-Preserving, Formatter-Compatible <=300)
1. Remove formatter suppression markers from `src/jfin/cli_runtime.py`.
2. Run formatter/lint checks and LOC check immediately after suppression removal.
3. If LOC remains `<=300`, stop with suppression-only remediation and no further decomposition.
4. If LOC exceeds `300`, perform minimal behavior-preserving extraction into one adjacent private helper module focused on cohesive runtime orchestration blocks (no contract/signature changes).
5. Keep public runtime entry points and call signatures unchanged (`parse_args`, `run_main`, and referenced CLI integration behavior).
6. Preserve dry-run and write-path safety invariants; no semantic changes to execution routing.

## Disallowed Anti-Evasion Tactics
- `# fmt: off` / `# fmt: on` suppression.
- Multi-statement semicolon packing.
- Dense inline control-flow suite packing.

## Scope Control and Stop/Split Rules
- Hard stop if remediation requires widening into pipeline files.
- Hard stop if behavior/signature changes are required to reach LOC target.
- Hard stop if `src/jfin/cli.py` needs more than trivial import compatibility.
- Hard stop if offender set after verification is not exactly the expected remaining pair.
- If stopped, mark Slice-30b blocked, preserve evidence, and split forward instead of broadening scope.

## Acceptance Criteria
- `src/jfin/cli_runtime.py` has no formatter suppression markers.
- `src/jfin/cli_runtime.py` is honest formatted LOC `<=300`.
- Runtime/CLI behavior and signatures are preserved.
- Post-success anti-evasion offender set is exact pair only: `src/jfin/pipeline.py` and `src/jfin/pipeline_backdrops.py`.
- Explicit non-flagged assertions after success: `src/jfin/cli_runtime.py`, `src/jfin/cli.py`, `src/jfin/client.py`, and `src/jfin/client_http.py`.
- No unexpected `src/` scope expansion.
- Theme A and `A-08` remain open.

## Deliverables
- `project/v1-slices-reports/slice-30b/slice-30b-plan.md`
- `project/v1-slices-reports/slice-30b/slice-30b-implementation.md`
- `project/v1-slices-reports/slice-30b/slice-30b-audit.md`

## Verification Ownership
- Workers may run provisional checks during implementation.
- The main orchestration agent must run authoritative verification before audit and before commit.

## Exact Verification Commands
```powershell
$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = 'src'

$expectedBaselineOffenders = @(
  'src/jfin/cli_runtime.py',
  'src/jfin/pipeline.py',
  'src/jfin/pipeline_backdrops.py'
)

$expectedRemaining = @(
  'src/jfin/pipeline.py',
  'src/jfin/pipeline_backdrops.py'
)

$expectedNotFlaggedAfterSuccess = @(
  'src/jfin/cli_runtime.py',
  'src/jfin/cli.py',
  'src/jfin/client.py',
  'src/jfin/client_http.py'
)

$preSliceSnapshotPath = 'project/v1-slices-reports/slice-30b/pre-slice-status.txt'
$sliceArtifactPrefix = 'project/v1-slices-reports/slice-30b/'
$implementationReportPath = 'project/v1-slices-reports/slice-30b/slice-30b-implementation.md'
$allowedPrimaryTouch = 'src/jfin/cli_runtime.py'
$cleanSentinel = '<clean>'

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

# 0) Slice-start snapshot capture (orchestrator; run once before implementation edits)
$startStatus = git status --porcelain
if ($startStatus) {
  $startStatus | Set-Content -Encoding utf8 $preSliceSnapshotPath
} else {
  $cleanSentinel | Set-Content -Encoding utf8 $preSliceSnapshotPath
}

# 1) Baseline lock and pre-slice cleanliness validation
$branch = git rev-parse --abbrev-ref HEAD
$head = git rev-parse --short=7 HEAD
if ($branch -ne 'v1/thm-a-governance-contract-posture-recovery') {
  throw "Unexpected branch baseline: $branch"
}
if ($head -ne '500a3cd') {
  throw "Unexpected baseline HEAD: $head"
}

if (-not (Test-Path $preSliceSnapshotPath)) {
  throw "Missing pre-slice snapshot: $preSliceSnapshotPath"
}
$preSliceSnapshot = Get-Content $preSliceSnapshotPath | Where-Object { $_ -and $_ -ne $cleanSentinel }
$currentStatus = git status --porcelain

$unexpectedStatus = $currentStatus | Where-Object {
  $_ -and ($_ -notin $preSliceSnapshot) -and ($_ -notmatch [regex]::Escape($sliceArtifactPrefix))
}
if ($unexpectedStatus) {
  $unexpectedStatus
  throw 'Unexpected worktree dirt outside pre-slice snapshot and allowed Slice-30b artifact paths.'
}

git status --short
git diff --name-only -- src

# 2) Pre-slice baseline capture for cli_runtime.py suppression/LOC/offenders
$fmtBefore = rg -n "#\s*fmt:\s*(off|on)" src/jfin/cli_runtime.py
if ($LASTEXITCODE -ne 0) {
  throw 'Baseline missing expected cli_runtime.py suppression marker.'
}
$fmtBefore

$runtimeLocBefore = (Get-Content src/jfin/cli_runtime.py).Length
"cli_runtime.py pre-change LOC=$runtimeLocBefore"

$baselineLocOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc 2>&1
$baselineLocExit = $LASTEXITCODE
$baselineLocText = $baselineLocOutput | Out-String
$baselineLocText
Assert-OffenderSetExact -CheckName 'baseline --check loc' -ExitCode $baselineLocExit -OutputText $baselineLocText -Expected $expectedBaselineOffenders

# 3) Post-change anti-evasion and honest LOC checks
$fmtAfter = rg -n "#\s*fmt:\s*(off|on)" src/jfin/cli_runtime.py
if ($LASTEXITCODE -eq 0) {
  $fmtAfter
  throw 'Formatter suppression remains in src/jfin/cli_runtime.py.'
}

$runtimeLocAfter = (Get-Content src/jfin/cli_runtime.py).Length
"cli_runtime.py LOC=$runtimeLocAfter"
if ($runtimeLocAfter -gt 300) {
  throw 'src/jfin/cli_runtime.py exceeds 300 LOC.'
}

.\.venv\Scripts\python.exe -m ruff check src/jfin/cli_runtime.py --select E701,E702,E703

# Required command in this slice checklist
.\.venv\Scripts\python.exe -m ruff format --check .

# 4) Targeted CLI/runtime regression checks
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q `
  tests/characterization/cli_contract/test_cli_contract_characterization.py `
  tests/test_jfin.py `
  tests/test_config.py `
  tests/test_route_fence_runtime.py `
  tests/test_characterization_runtime_gate.py

# 5) Governance offender assertions
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
$unexpectedOffenders = $allOffenders | Where-Object { $_ -notin $expectedRemaining }
if ($unexpectedOffenders) {
  throw "Post-success offender set must be exact pair only. Unexpected offenders: $($unexpectedOffenders -join ', ')"
}
$stillFlagged = $expectedNotFlaggedAfterSuccess | Where-Object { $_ -in $allOffenders }
if ($stillFlagged.Count -gt 0) {
  throw "Expected non-flagged file still present in offender set: $($stillFlagged -join ', ')"
}

# 6) Scope-control evidence
git diff --name-only -- src
git diff --numstat -- src
$srcTouched = git diff --name-only -- src
$unexpected = @()
$helperTouch = @()

foreach ($path in $srcTouched) {
  if ($path -eq $allowedPrimaryTouch) {
    continue
  }
  if ($path -match '^src/jfin/cli_runtime_[A-Za-z0-9_]+\.py$') {
    $helperTouch += $path
    continue
  }
  $unexpected += $path
}

if ($unexpected) {
  throw "Out-of-scope src touches: $($unexpected -join ', ')"
}
if ($helperTouch.Count -gt 1) {
  throw "At most one adjacent helper module is allowed. Found: $($helperTouch -join ', ')"
}
if ($helperTouch.Count -eq 1) {
  if (-not (Test-Path $implementationReportPath)) {
    throw "Helper extraction touched ($($helperTouch[0])) but implementation report is missing: $implementationReportPath"
  }
  $implementationText = Get-Content -Raw $implementationReportPath
  if ($implementationText -notmatch [regex]::Escape($helperTouch[0])) {
    throw "Helper extraction path must be explicitly documented in implementation report: $($helperTouch[0])"
  }
}

# 7) AGENTS.md full gate set
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit

# 8) Final cleanliness/status snapshot
git status --short
```

## Failure Path (If Slice-30b Cannot Close Safely)
- Fail closed; do not claim Slice-30b closure.
- Revert uncommitted source edits and retain evidence artifacts.
- Publish blocked-state details in `project/v1-slices-reports/slice-30b/slice-30b-implementation.md` and `project/v1-slices-reports/slice-30b/slice-30b-audit.md`.
- Record exact blocker cause (behavior risk, LOC breach, or scope breach) and required follow-on split.

## Explicit Open-State Statement
- `A-08` remains open after Slice-30b.
- Theme A remains open after Slice-30b.

## Explicit Next-Slice Output After 30b
- Next slice output: `Slice-30c Pipeline evasion remediation tranche 3c (pipeline.py first)`.
- Rationale: after successful Slice-30b, only the pipeline pair remains in the anti-evasion offender set, so remediation should stay one-objective and start with `pipeline.py`.
- Expected blockers entering the next slice: `src/jfin/pipeline.py` (anti-evasion suppression and honest LOC risk) and `src/jfin/pipeline_backdrops.py` (anti-evasion suppression remains until its own tranche).
- Theme-level status remains unchanged: `A-08` open, Theme A open.

