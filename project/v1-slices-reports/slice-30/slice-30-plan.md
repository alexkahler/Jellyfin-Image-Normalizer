# Slice 30 Plan (Slice-29a)

## Slice Id and Title
- Slice id: `Slice-29a`
- Slice title: `Runtime evasion remediation tranche 2a (client_http first, decomposed)`

## Objective
- Remove anti-evasion formatter suppression from `src/jfin/client_http.py`.
- Keep `src/jfin/client_http.py` at honest LOC `<=300` under enforced anti-evasion rules.
- Preserve runtime behavior and safety invariants.
- Keep `A-08` open (no closure claim in this slice).

## In Scope / Out of Scope
- In scope:
  - Behavior-preserving structural/formatter-compatible remediation in `src/jfin/client_http.py`.
  - Removal of `# fmt: off` / `# fmt: on` from `src/jfin/client_http.py`.
  - Minimal tightly-coupled helper movement between `client_http.py` and `client.py` only if unavoidable to keep honest LOC and readability.
- Out of scope:
  - Any CLI/pipeline/config remediation.
  - Any route-fence flips or governance artifact redesign.
  - Any Jellyfin API behavior changes (auth, retries, timeouts, TLS, dry-run/write-gate semantics).
  - Closing `A-08` / GG-008.
  - Starting Slice 29b or Slice 30+ work in this slice.

## Target Files
- `src/jfin/client_http.py`
- Optional only-if-unavoidable tightly-coupled adjustment: `src/jfin/client.py`
- Slice artifacts:
  - `project/v1-slices-reports/slice-30/slice-30-plan.md`
  - `project/v1-slices-reports/slice-30/slice-30-implementation.md`
  - `project/v1-slices-reports/slice-30/slice-30-audit.md`

## Public Interfaces Affected
- No public interface changes are allowed.
- Preserve behavior/signatures for `client_http.py` functions:
  - `_http_error`
  - `_request_with_retry`
  - `get_response`
  - `head_response`
  - `get_json_payload`
  - `test_connection`
  - `post_image`
  - `delete_image`
- Preserve `JellyfinClient` call contracts that delegate into `client_http`.

## Acceptance Criteria
- `src/jfin/client_http.py` contains no `# fmt: off` or `# fmt: on` markers.
- `src/jfin/client_http.py` uses no anti-evasion tactics:
  - no formatter suppression
  - no semicolon multi-statement packing
  - no dense inline control-flow suite packing
- Honest LOC for `src/jfin/client_http.py` is `<=300`.
- Targeted client/discovery/safety-contract tests pass.
- `verify_governance --check loc` and `--check all` still fail globally (expected until later slices) but must no longer flag `src/jfin/client_http.py`.
- Offender-set assertion after Slice-29a must be exactly:
  - `src/jfin/cli.py`
  - `src/jfin/cli_runtime.py`
  - `src/jfin/client.py`
  - `src/jfin/pipeline.py`
  - `src/jfin/pipeline_backdrops.py`
- `A-08` remains open and unchanged in status.

## Exact Verification Commands (PowerShell)
```powershell
$env:PYTHONPATH='src'

# 1) Targeted anti-evasion marker checks for client pair
rg -n "#\s*fmt:\s*(off|on)" src/jfin/client_http.py src/jfin/client.py
# Expected after Slice-29a: only src/jfin/client.py may match.

# 2) Honest LOC check for Slice-29a target
$clientHttpLoc = (Get-Content src/jfin/client_http.py).Length
"client_http.py LOC=$clientHttpLoc"
if ($clientHttpLoc -gt 300) { throw "client_http.py exceeds honest LOC limit (300)." }

# 3) Anti-evasion syntax checks (no packed inline suites/statements)
.\.venv\Scripts\python.exe -m ruff check src/jfin/client_http.py src/jfin/client.py --select E701,E702,E703
if ($LASTEXITCODE -ne 0) { throw "E701/E702/E703 check failed for client pair." }

# 4) Targeted behavior/safety tests
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_client.py tests/test_discovery.py tests/characterization/safety_contract/test_safety_contract_api.py
if ($LASTEXITCODE -ne 0) { throw "Targeted client/discovery/safety tests failed." }

# 5) Governance checks + offender-set assertions
$expectedOffenders29a = @(
  "src/jfin/cli.py",
  "src/jfin/cli_runtime.py",
  "src/jfin/client.py",
  "src/jfin/pipeline.py",
  "src/jfin/pipeline_backdrops.py"
)
$mustBeCleared29a = @("src/jfin/client_http.py")

function Get-AntiEvasionOffenders {
  param([string]$Text)
  [regex]::Matches($Text, "src/jfin/[A-Za-z0-9_]+\.py(?=\s+\[anti_evasion\.)") |
    ForEach-Object { $_.Value } |
    Sort-Object -Unique
}

function Assert-Offenders29a {
  param(
    [string]$CheckName,
    [int]$ExitCode,
    [string]$OutputText
  )

  if ($ExitCode -eq 0) {
    throw "$CheckName unexpectedly passed globally; later offender slices are expected open."
  }

  $offenders = Get-AntiEvasionOffenders -Text $OutputText
  $missing = $expectedOffenders29a | Where-Object { $_ -notin $offenders }
  if ($missing.Count -gt 0) {
    throw "$CheckName missing expected remaining offenders: $($missing -join ', ')"
  }

  $unexpected = $offenders | Where-Object { $_ -notin $expectedOffenders29a }
  if ($unexpected.Count -gt 0) {
    throw "$CheckName has unexpected offender expansion: $($unexpected -join ', ')"
  }

  $stillFlagged = $mustBeCleared29a | Where-Object { $_ -in $offenders }
  if ($stillFlagged.Count -gt 0) {
    throw "$CheckName still flags Slice-29a cleared target(s): $($stillFlagged -join ', ')"
  }
}

$locOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc 2>&1
$locExit = $LASTEXITCODE
$locText = $locOutput | Out-String
$locText
Assert-Offenders29a -CheckName "--check loc" -ExitCode $locExit -OutputText $locText

$allOutput = & .\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all 2>&1
$allExit = $LASTEXITCODE
$allText = $allOutput | Out-String
$allText
Assert-Offenders29a -CheckName "--check all" -ExitCode $allExit -OutputText $allText

# 6) Repo verification contract (AGENTS.md)
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit

# 7) Scope proof
git diff --numstat -- src
```

## Behavior-Preservation Statement
- This slice is behavior-preserving only.
- No intended change to Jellyfin request semantics, retry/backoff policy, timeout handling, TLS behavior, or dry-run/write-gate behavior.
- Safety-critical write/delete dry-run protections remain unchanged.

## Implementation Steps
1. Capture pre-change baseline (`fmt` markers, LOC, offender set, targeted test pass).
2. Remove `# fmt: off` / `# fmt: on` from `src/jfin/client_http.py`.
3. Apply minimal formatter-compatible restructuring in `client_http.py` only.
4. If honest LOC or readability cannot be preserved safely, perform only minimal tightly-coupled helper movement with `client.py`; otherwise keep `client.py` unchanged.
5. Re-run targeted tests and anti-evasion checks after each micro-change.
6. Run governance `--check loc` and `--check all` with offender-set assertions.
7. Run AGENTS verification contract commands.
8. Record implementation evidence and preserve blocked Slice 29 artifacts unchanged.

## Risks / Guardrails
- Risk: accidental behavior drift in retry or write/delete pathways.
  - Guardrail: no semantic edits; run targeted client/discovery/safety tests.
- Risk: scope creep into Slice-29b (`client.py`) or later tranches.
  - Guardrail: hard-stop on non-unavoidable `client.py` edits; no other runtime file edits.
- Risk: anti-evasion checks still flag `client_http.py`.
  - Guardrail: fail closed; do not close the slice unless offender-set assertions pass.
- Risk: LOC growth above 300 after honest formatting.
  - Guardrail: prefer small extraction; if not safe within scope, block and split.

## Rollback Step
- `git revert <slice-29a-commit-sha>`
- Re-run targeted client/safety tests and governance `--check loc`/`--check all` to confirm restoration.

## Expected Commit Title
- `Slice-29a Runtime evasion remediation tranche 2a (client_http first, decomposed)`

## Split Rule
- If work requires substantive behavioral edits, or touches runtime files outside `src/jfin/client_http.py` (except unavoidable minimal tight-coupling with `client.py`), stop and split.
- If `client_http.py` cannot be cleared from anti-evasion findings while preserving behavior and honest LOC, mark Slice-29a blocked and do not proceed to Slice-29b.

## Plan Review Notes (assumptions/ambiguities)
- Assumption: current anti-evasion findings for `client_http.py` are due to formatter suppression markers, not hidden semicolon/inline control-flow violations.
- Assumption: `client.py` may remain an expected offender until Slice-29b and should not be remediated here beyond unavoidable coupling.
- Ambiguity handled fail-closed: if governance output format changes and regex offender extraction fails, manual offender validation is required before closure.
- Sequence constraint retained: no Slice 30+ work is permitted until both decomposition slices (29a, 29b) are closed and independently audited compliant.
