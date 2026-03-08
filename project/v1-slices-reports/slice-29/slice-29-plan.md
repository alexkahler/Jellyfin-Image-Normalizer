# Slice 29 Plan (v3 FINAL)

## Slice Id and Title
- Slice id: `Slice-29`
- Slice title: `Runtime evasion remediation tranche 2 (client pair)`

## Objective
- Remove anti-evasion suppression reliance from the client pair while preserving behavior.
- Bring honest LOC to `<=300` for both `src/jfin/client.py` and `src/jfin/client_http.py` without suppression or packing tactics.
- Complete only this tranche scope.
- Keep `A-08` open; no closure claim in Slice 29.

## In Scope
- Behavior-preserving structural remediation only in:
- `src/jfin/client.py`
- `src/jfin/client_http.py`
- Removal of `# fmt: off` / `# fmt: on` in both target files.
- Small helper extraction/reordering between these two files only, if needed to satisfy honest LOC and readability.

## Out of Scope
- Any behavioral change to Jellyfin API semantics (auth headers, retry/backoff behavior, timeouts, TLS verify, dry-run/write-gate behavior, fail-fast behavior).
- Any edit outside `src/jfin/client.py` and `src/jfin/client_http.py`.
- Governance artifact edits (`project/*`, parity/route-fence artifacts, characterization baselines).
- Work on CLI or pipeline anti-evasion files.
- Closing `A-08`.

## Target Files
- `src/jfin/client.py`
- `src/jfin/client_http.py`

## Public Interfaces Affected
- Interface change policy: no public interface changes are allowed in this slice.
- `client.py`: `JellyfinClient` dataclass fields and methods must remain behaviorally equivalent, including `test_connection`, `list_users`, `list_media_folders`, `query_items`, `get_item`, `get_item_image`, `get_item_image_head`, `get_user_image`, `set_item_image_bytes`, `set_item_image`, `set_user_image_bytes`, `delete_image`, `set_user_profile_image`.
- `client_http.py`: `get_response`, `head_response`, `get_json_payload`, `test_connection`, `post_image`, `delete_image` must remain behaviorally equivalent.

## Acceptance Criteria
- `# fmt: off` / `# fmt: on` are removed from both target files.
- No anti-evasion tactics are introduced in target files.
- No formatter suppression.
- No multi-statement semicolon packing.
- No dense inline control-flow packing.
- Honest LOC is `<=300` for each target file.
- Targeted client/discovery/safety-contract tests pass.
- If targeted client/safety tests reveal behavior drift in retries/timeouts/dry-run gating, Slice 29 is blocked and must not be force-closed.
- `verify_governance --check loc` and `--check all` are expected to remain non-zero globally until later slices.
- Slice-29-specific remaining anti-evasion runtime offenders must be exactly:
- `src/jfin/cli.py`
- `src/jfin/cli_runtime.py`
- `src/jfin/pipeline.py`
- `src/jfin/pipeline_backdrops.py`
- Slice-29-specific cleared files must not appear in anti-evasion findings:
- `src/jfin/client.py`
- `src/jfin/client_http.py`
- If offender-set assertions fail (missing expected remaining offenders, unexpected expansion, or target pair still flagged), Slice 29 is blocked and must not be closed until discrepancy is explained and fixed.
- `A-08` is explicitly still open at slice close.

## Exact Verification Commands
```powershell
$env:PYTHONPATH='src'

$expectedRemainingOffenders = @(
  "src/jfin/cli.py",
  "src/jfin/cli_runtime.py",
  "src/jfin/pipeline.py",
  "src/jfin/pipeline_backdrops.py"
)
$expectedClearedPair = @(
  "src/jfin/client.py",
  "src/jfin/client_http.py"
)

function Get-AntiEvasionOffenders {
  param([string]$Text)
  [regex]::Matches($Text, "src/jfin/[A-Za-z0-9_]+\.py(?=\s+\[anti_evasion\.)") |
    ForEach-Object { $_.Value } |
    Sort-Object -Unique
}

function Assert-OffenderSet {
  param(
    [string]$CheckName,
    [string]$OutputText,
    [int]$ExitCode
  )

  if ($ExitCode -eq 0) {
    throw "Expected $CheckName to remain non-zero globally until later slices."
  }

  $offenders = Get-AntiEvasionOffenders -Text $OutputText

  $missingExpected = $expectedRemainingOffenders | Where-Object { $_ -notin $offenders }
  if ($missingExpected.Count -gt 0) {
    throw "Unexpected offender drop for $CheckName: missing expected remaining offenders: $($missingExpected -join ', ')"
  }

  $unexpectedExpansion = $offenders | Where-Object { $_ -notin $expectedRemainingOffenders }
  if ($unexpectedExpansion.Count -gt 0) {
    throw "Unexpected offender expansion for $CheckName: $($unexpectedExpansion -join ', ')"
  }

  $stillFlaggedTargetPair = $expectedClearedPair | Where-Object { $_ -in $offenders }
  if ($stillFlaggedTargetPair.Count -gt 0) {
    throw "Target client pair still flagged in $CheckName: $($stillFlaggedTargetPair -join ', ')"
  }
}

# Targeted tests for client pair behavior and safety contracts
.\.venv\Scripts\python.exe -m pytest -q tests/test_client.py tests/test_discovery.py tests/characterization/safety_contract/test_safety_contract_api.py
if ($LASTEXITCODE -ne 0) {
  throw "Targeted client/safety tests failed; possible behavior drift in retries/timeouts/dry-run gating. Slice is blocked."
}

# Target-file anti-evasion checks
rg -n "#\s*fmt:\s*(off|on)" src/jfin/client.py src/jfin/client_http.py
if ($LASTEXITCODE -eq 0) { throw "Formatter suppression remains in target client pair." }

.\.venv\Scripts\python.exe -m ruff check src/jfin/client.py src/jfin/client_http.py --select E701,E702,E703

# Honest LOC checks for target files
$clientLoc = (Get-Content src/jfin/client.py).Length
$clientHttpLoc = (Get-Content src/jfin/client_http.py).Length
"client.py LOC=$clientLoc"
"client_http.py LOC=$clientHttpLoc"
if ($clientLoc -gt 300 -or $clientHttpLoc -gt 300) { throw "Target client pair exceeds 300 LOC." }

# Governance fail-closed checks with machine assertions on offender set
$locOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc 2>&1
$locExit = $LASTEXITCODE
$locText = $locOutput | Out-String
$locText
Assert-OffenderSet -CheckName "--check loc" -OutputText $locText -ExitCode $locExit

$allOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all 2>&1
$allExit = $LASTEXITCODE
$allText = $allOutput | Out-String
$allText
Assert-OffenderSet -CheckName "--check all" -OutputText $allText -ExitCode $allExit

# Repository contract command set from AGENTS.md
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit

# Scope evidence
$srcDiff = git diff --name-only -- src
$srcDiff
$unexpectedSrcTouch = $srcDiff | Where-Object { $_ -notin @("src/jfin/client.py", "src/jfin/client_http.py") }
if ($unexpectedSrcTouch) { throw "Out-of-scope src edits detected: $($unexpectedSrcTouch -join ', ')" }

# Slice evidence
git diff --numstat -- src/jfin/client.py src/jfin/client_http.py
```

## Behavior-Preservation Statement
- Slice 29 is behavior-preserving only.
- No intended changes to observable Jellyfin client contract behavior.
- Dry-run/write-gate safety invariants in client write/delete paths must remain equivalent.

## Implementation Steps
1. Capture pre-change baselines for both target files (LOC, suppression markers, current anti-evasion findings).
2. Remove formatter suppression markers from both files.
3. Apply minimal formatter-compatible restructuring to restore readability without semantic changes.
4. If needed for LOC, move cohesive helper logic only between `client.py` and `client_http.py`.
5. Re-run targeted client/discovery/safety tests after each micro-change.
6. Run anti-evasion checks and confirm client-pair clearance from `--check loc` and `--check all` outputs.
7. Enforce machine assertions that remaining offenders are exactly CLI pair + pipeline pair (no drop/expansion for this slice objective).
8. Run the AGENTS contract command set and capture evidence.
9. Record that `A-08` remains open and is not closed by Slice 29.

## Risks / Guardrails
- Risk: behavior drift in retry/backoff/error handling or dry-run write gating.
- Guardrail: keep signatures/semantics stable and run targeted safety-contract tests throughout.
- Risk: LOC remains above threshold after suppression removal.
- Guardrail: perform only cohesive helper redistribution inside the client pair; no evasion tactics.
- Risk: scope creep into non-client modules or governance artifacts.
- Guardrail: hard-stop on edits outside the two target files.
- Risk: offender-set assertions indicate unexpected drop/expansion or client pair still flagged.
- Guardrail: mark Slice 29 blocked and do not close until the discrepancy is explained and fixed.

## Rollback
- `git revert <slice-29-commit-sha>`
- Re-run targeted client/safety tests plus governance `--check loc` and `--check all` to confirm restoration.

## Expected Commit Title
- `Slice-29 Runtime evasion remediation tranche 2 (client pair)`

## Explicit Split Rule
- If completion requires editing any file outside `src/jfin/client.py` and `src/jfin/client_http.py`, stop and split immediately.
- If either target file cannot be kept at honest `<=300` LOC without behavior risk, stop and split by cohesive helper boundary inside the client pair rather than using any anti-evasion tactic.

## Blocked State (Recorded 2026-03-08)
- Slice 29 implementation was attempted but could not be closed safely within the bounded client-pair scope.
- Multiple bounded remediation attempts produced non-closable intermediate states and did not reach honest `<=300` LOC for both files simultaneously without unacceptable risk of behavior drift.
- Final working tree was restored to pre-slice runtime baseline for this pair (`HEAD` at Slice 28 closure) to avoid partial unsafe changes.
- Per split rule, Slice 29 is **blocked** and should be decomposed before further implementation.

