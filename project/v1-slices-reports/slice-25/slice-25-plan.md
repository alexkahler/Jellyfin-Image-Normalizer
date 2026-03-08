# Slice 25 Plan (V3 FINAL)

## Slice Id and Title
- Slice id: `A-08R1`
- Slice title: `slice-25: a-08 quality blocker remediation`

## Objective
Clear the Slice 24 required-job blocker by removing the known `quality` failure cause (`ruff format --check .`) with a remediation-only, behavior-preserving change set.

## In-Scope / Out-of-Scope
- In scope: formatter-driven remediation for files currently failing `ruff format --check .`.
- In scope: Slice 25 artifacts (`slice-25-plan.md`, `slice-25-audit.md`).
- Out of scope: Slice 24 evidence updates during implementation (handled only in post-closure handoff).
- Out of scope: unrelated refactors, route-fence/parity changes, architecture redesign, opportunistic cleanup.
- Out of scope: semantic/runtime behavior changes unless strictly unavoidable (if unavoidable, mark blocked and stop).

## Target Files
- `project/v1-slices-reports/slice-25/slice-25-plan.md`
- `project/v1-slices-reports/slice-25/slice-25-audit.md`
- `src/jfin/backup.py`
- `src/jfin/backup_restore.py`
- `src/jfin/cli.py`
- `src/jfin/cli_runtime.py`
- `src/jfin/client.py`
- `src/jfin/client_http.py`
- `src/jfin/config.py`
- `src/jfin/config_core.py`
- `src/jfin/pipeline.py`
- `src/jfin/pipeline_backdrops.py`
- `src/jfin/pipeline_image_normalization.py`
- `src/jfin/pipeline_image_payload.py`
- `src/jfin/pipeline_orchestration.py`
- `src/jfin/pipeline_profiles.py`
- `tests/test_characterization_checks_safety.py`

## Acceptance Criteria
- Passes local `.\.venv\Scripts\python.exe -m ruff format --check .` and removes known Slice 24 quality blocker cause.
- Remediation remains narrowly scoped to formatter compliance.
- No intended runtime semantic behavior change.
- `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all` is run and outcome recorded.
- Verification evidence is captured, including `git diff --numstat -- src`.
- Slice 25 audit states whether branch is ready to rerun A-08 same-SHA CI proof.
- Slice 24 remains the blocked evidence record until post-remediation same-SHA proof is completed.

## Exact Verification Commands
```powershell
# Baseline blocker check
.\.venv\Scripts\python.exe -m ruff format --check .

# Apply formatter remediation (targeted failing set)
.\.venv\Scripts\python.exe -m ruff format `
  src\jfin\backup.py `
  src\jfin\backup_restore.py `
  src\jfin\cli.py `
  src\jfin\cli_runtime.py `
  src\jfin\client.py `
  src\jfin\client_http.py `
  src\jfin\config.py `
  src\jfin\config_core.py `
  src\jfin\pipeline.py `
  src\jfin\pipeline_backdrops.py `
  src\jfin\pipeline_image_normalization.py `
  src\jfin\pipeline_image_payload.py `
  src\jfin\pipeline_orchestration.py `
  src\jfin\pipeline_profiles.py `
  tests\test_characterization_checks_safety.py

# AGENTS.md contract commands (PowerShell forms)
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit

# Governance gate
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all

# Scope sanity
git diff --numstat -- src
```

## Rollback Step
Revert the remediation commit if rollback is required: `git revert <slice-25-remediation-commit>`.

## Behavior-Preservation Statement
This slice is remediation-only for formatter compliance and is intended to preserve runtime behavior.

## Implementation Steps
1. Confirm blocker with `ruff format --check .`.
2. Run targeted formatter remediation on failing files only.
3. Re-run formatter check; if still failing, stop-and-fix within remediation scope.
4. Run AGENTS verification command set and governance `--check all`.
5. If remediation requires semantic changes beyond formatting, mark Slice 25 blocked in `slice-25-audit.md` and stop.
6. If any AGENTS verification gate fails, record blocked state in `slice-25-audit.md` and do not claim closure.
7. Capture scope evidence (`git diff --numstat -- src`).
8. Produce `slice-25-audit.md` with pass/fail and closure recommendation.
9. If clean, commit and push Slice 25 remediation commit.

## Risks / Guardrails
- Risk: formatter churn may trigger other gates.
- Guardrail: keep changes minimal and confined to formatter-affected files.
- Risk: remediation appears to require semantic edits beyond formatting.
- Guardrail: stop-and-fix rule; if semantic edits are required, mark blocked and stop.
- Risk: false closure claim for A-08.
- Guardrail: do not close A-08 from Slice 25; closure only via same-SHA CI evidence rerun on new HEAD.

## Expected Commit Title
`slice-25: a-08 quality blocker remediation`

## Post-closure Handoff to Slice 24/A-08
1. Capture new HEAD SHA (`git rev-parse HEAD`).
2. Run `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`.
3. Query same-SHA CI evidence for `.github/workflows/ci.yml` (`CI`) and required jobs.
4. Update `project/v1-slices-reports/slice-24/a08-ci-evidence.json`.
5. Update `project/v1-slices-reports/slice-24/slice-24-audit.md`.
6. Update `WORK_ITEMS.md`.
