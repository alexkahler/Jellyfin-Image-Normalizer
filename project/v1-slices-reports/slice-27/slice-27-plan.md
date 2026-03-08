# Slice 27 Plan (v3 FINAL)

## Slice Id and Title
- Slice id: `Slice-27`
- Slice title: `Anti-evasion enforcement parity in governance checks`

## Objective
- Wire anti-evasion codification into the governance parser/schema/check path so `verify_governance --check loc` and `verify_governance --check all` fail closed when LOC compliance depends on forbidden suppression/evasion tactics.

## Status Alignment (Required Context)
- This slice executes the explicit next step selected by Slice 26 artifacts (`slice-26-plan.md`, `slice-26-implementation.md`, `slice-26-audit.md`).
- This slice does **not** close Theme A by itself.
- **A-08 remains open** (Slice 24 remains blocked due to same-SHA CI `quality` failure on 2026-03-08, and Theme A remains open until both GG-001 and GG-008 are closed).

## Authoritative Inputs Used
- `project/v1-slices-reports/audits/track-1-theme-a-iteration-roadmap.md`
- `project/v1-plan.md`
- `AGENTS.md`
- `project/verification-contract.yml`
- `WORK_ITEMS.md`
- Slice 24 artifacts:
  - `project/v1-slices-reports/slice-24/slice-24-plan.md`
  - `project/v1-slices-reports/slice-24/slice-24-audit.md`
  - `project/v1-slices-reports/slice-24/a08-ci-evidence.json`
- Slice 26 artifacts:
  - `project/v1-slices-reports/slice-26/slice-26-plan.md`
  - `project/v1-slices-reports/slice-26/slice-26-implementation.md`
  - `project/v1-slices-reports/slice-26/slice-26-audit.md`

## In-Scope / Out-of-Scope
- In scope:
  - Enforce anti-evasion LOC keys already codified in `project/verification-contract.yml` by extending parser and schema validation.
  - Enforce anti-evasion checks in governance LOC evaluation path with fail-closed behavior.
  - Add/update governance tests proving parser/schema/check behavior and expected fail-closed outcomes.
  - Contract/doc parity updates only if implementation reveals mismatch with current key names or required values.
- Out of scope:
  - Any `src/jfin/` runtime refactor or LOC remediation work (belongs to Slice 28+ runtime remediation tranches).
  - Route-fence changes, architecture redesign, CLI/config public-surface redesign.
  - Reattempting A-08 same-SHA CI closure.

## Target Files
- Primary implementation:
  - `project/scripts/governance_contract.py`
  - `project/scripts/governance_checks.py`
- Governance tests:
  - `tests/test_governance_checks.py` (required primary test surface for this slice)
  - `tests/test_governance_runtime_gate.py` (optional only if touched code overlaps runtime-gate shared helpers or check-selection wiring; otherwise skip to keep scope tight)
  - Optional new governance test module only if needed to keep existing files maintainable.
- Conditional parity updates only if required:
  - `project/verification-contract.yml` (only if key naming/schema correction is unavoidable)
  - `AGENTS.md` (only if contract wording/key semantics change)

## Public Interfaces Affected
- Governance CLI behavior only:
  - `project/scripts/verify_governance.py --check loc`
  - `project/scripts/verify_governance.py --check all`
- Expected interface effect:
  - These checks should return non-zero when anti-evasion violations make LOC compliance invalid or unverifiable.
- No product runtime interface changes under `src/`.

## Acceptance Criteria
- Parser/schema parity:
  - `parse_verification_contract` requires and parses anti-evasion keys under `loc_policy`.
  - `check_contract_schema` validates anti-evasion keys against canonical expected values and fails on drift.
- LOC check parity:
  - `check_loc_policy` enforces anti-evasion rules (fmt suppression, semicolon packing, dense inline control-flow packing) according to contract values.
  - Fail-closed behavior is explicit: inability to establish honest LOC (or policy-supported analysis) is a blocking error.
- Runtime posture proof:
  - On the current repository state (with retained `# fmt: off` in `src/`), `--check loc` and `--check all` are expected to fail for anti-evasion reasons after parity wiring is complete.
  - This expected fail-closed result is pass evidence for the Slice 27 objective (enforcement parity), not a slice failure.
- Test proof:
  - Governance tests (primarily `tests/test_governance_checks.py`) cover parser required-key enforcement, schema value enforcement, and fail-closed LOC behavior.
- Scope discipline:
  - No `src/` runtime code edits.
  - Single objective maintained (enforcement parity only).
- Explicit carry-forward:
  - Plan and implementation artifacts keep **A-08 open** and avoid closure claims.

## Closure Decision
- Slice 27 closes when all are true:
  - enforcement parity is wired in governance parser/schema/check path;
  - expected fail-closed evidence is present (`--check loc` and `--check all` return non-zero for anti-evasion reasons);
  - governance tests pass;
  - `git diff --numstat -- src` is empty (no runtime edits).
- Slice 27 is blocked when either is true:
  - governance failures are unrelated to the anti-evasion enforcement objective;
  - scope expands beyond governance parser/schema/check/tests.

## Exact Verification Commands
```powershell
# 1) Targeted governance unit tests for this slice
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_governance_checks.py

# 1b) Optional only when runtime-gate shared helper/wiring surface is touched
# $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_governance_runtime_gate.py

# 2) Required anti-evasion static signal command from Slice 27 spec
.\.venv\Scripts\python.exe -m ruff check src tests .github --select E701,E702,E703

# 3) Loc-only governance gate is expected to fail closed while retained anti-evasion violations remain
# Expected non-zero here is PASS evidence for Slice 27 objective completion.
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc
if ($LASTEXITCODE -eq 0) { throw "Expected --check loc to fail closed under retained anti-evasion violations." }

# 4) Aggregate governance gate is also expected to fail closed for the same reason
# Expected non-zero here is PASS evidence for Slice 27 objective completion.
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
if ($LASTEXITCODE -eq 0) { throw "Expected --check all to fail closed under retained anti-evasion violations." }

# 5) Runtime-surface evidence gate: output must be empty; non-empty output blocks Slice 27 closure
$srcDiff = git diff --numstat -- src
$srcDiff
if ($srcDiff) { throw "Expected empty 'git diff --numstat -- src' output for Slice 27 closure." }

# 6) Repo contract command set (run as standard gate; failures outside anti-evasion objective are blockers)
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit
```

## Rollback Step
- Revert the Slice 27 commit if enforcement parity causes unexpected governance regressions:
  - `git revert <slice-27-commit-sha>`
- Re-run:
  - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check loc`
  - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`
  - targeted governance tests listed above.

## Behavior-Preservation Statement
- Slice 27 is governance-enforcement work only.
- No intended runtime behavior changes under `src/`.
- Runtime safety invariants (`dry_run` dual-gate and backdrop/restore protections) remain untouched.

## Implementation Steps
1. Extend `LocPolicy` parsing in `project/scripts/governance_contract.py` to require anti-evasion keys already present in `project/verification-contract.yml`.
2. Extend `check_contract_schema` to validate anti-evasion keys and fail on value drift.
3. Implement anti-evasion detection/evaluation in `project/scripts/governance_checks.py` LOC path:
   - detect formatter suppression markers;
   - detect multi-statement semicolon packing beyond policy threshold;
   - detect dense inline control-flow suites beyond policy threshold;
   - enforce fail-closed when honest LOC cannot be asserted.
4. Ensure violation messages identify file path + violation category so failures are actionable.
5. Add/update governance unit tests for parser/schema/check behavior and fail-closed outcomes.
6. Run exact verification commands and capture expected `--check loc` / `--check all` failure posture.
7. Update contract/doc parity artifacts only if required by key semantics (otherwise no doc/contract edits in this slice).

## Risks / Guardrails
- Risk: false positives in anti-evasion detection.
  - Guardrail: encode deterministic thresholds from contract keys and test explicit positive/negative cases.
- Risk: accidental scope creep into runtime remediation.
  - Guardrail: no `src/jfin/` edits in this slice; runtime suppression removal deferred.
- Risk: parser/schema drift if anti-evasion keys are parsed but not schema-validated (or vice versa).
  - Guardrail: enforce both parse-time required keys and schema-time canonical values.
- Risk: failing to preserve one-objective slice discipline.
  - Guardrail: defer all remediation/content reformat work to Slice 28+.

## Expected Commit Title
- `Slice-27 Anti-evasion enforcement parity in governance checks`

## Explicit Split Rule (If Scope Sprawls)
- If implementation requires touching anything outside governance parser/schema/check/tests (for example any `src/jfin/*.py` remediation, route-fence artifacts, or broad docs rewrites), stop and split immediately:
  - `Slice-27a`: governance parser/schema/check enforcement parity only.
  - `Slice-27b`: residual governance-test/doc parity follow-up only.
- Do **not** absorb runtime LOC-remediation work (Slice 28+) into Slice 27.

## Assumptions / Gaps
- Assumption: anti-evasion keys in `project/verification-contract.yml` are canonical and should be enforced as-is unless implementation reveals a hard schema mismatch.
- Gap to confirm during implementation: exact dense-control-flow detection heuristic that is strict enough for fail-closed policy while keeping low false-positive risk.
