# AGENTS.md - JFIN Agent Operating Contract

This file is the canonical in-repo operating contract for coding agents working in JFIN.
Keep it concise, command-accurate, and synchronized with enforced governance artifacts.

## Scope and Precedence

- This root `AGENTS.md` applies to the entire repository.
- If a subtree contains its own `AGENTS.md`, the nearest file applies for that subtree and can add stricter rules.
- Some tools load instruction files from root to leaf and effectively prioritize closer instructions.
- Some tools stop loading instruction content after size limits; keep this root file small and move specialization to scoped overrides or skills.

## Skill selection and routing

This repository uses a skill library for task-scoped procedures.

Rules:
- Keep repo-wide invariant rules in this AGENTS.md.
- Use skills for task-specific workflows and deeper procedures.
- When multiple skills appear relevant, consult `references/skill-catalog-routing.md` and follow its:
  - primary skill rules,
  - companion skill rules,
  - near-miss exclusions,
  - handoff / escalation rules.
- Prefer the most phase-specific and domain-specific skill over a broader default.
- Do not duplicate full skill procedures into AGENTS.md; use this file for policy and repo conventions only.

Minimum routing order:
1. Check whether the task is primarily planning, implementation-shaping, verification, contract change, refactor, or docs synchronization.
2. Select the primary skill accordingly.
3. Load companion skills only when the routing document says they compose.
4. If the task changes phase, hand off to the next appropriate skill rather than forcing one skill to cover the whole lifecycle.

## Skill catalog maintenance

When changing the skill library:
- Update `references/skill-catalog-routing.md` if a skill’s scope, primary role, companion role, near-miss boundary, or handoff behavior changes.
- Update affected skill `description` fields when routing distinctions change.
- Add or update near-miss examples in the relevant `SKILL.md`.
- If repo structure or commands referenced by a skill change, update AGENTS.md and the skill in the same change.

## Single Source of Truth and Enforcement Truth

- Repository policy: `AGENTS.md` is the canonical committed instruction contract for repo-wide agent operation.
- Keep repo-wide invariants, canonical command sets, and enforcement-linked expectations in `AGENTS.md`.
- Shared references may exist for reusable routing or verification mechanics, but they must not redefine or contradict repo policy in `AGENTS.md`.
- Skills should reference shared routing/verification documents instead of duplicating repo-wide commands or invariants.
- If a future tool requires a specific instruction filename, it must be a thin pointer/shim to `AGENTS.md`.
- Personal/global local overrides are allowed for individual workflows but are non-contractual and must never be relied on for CI or shared team behavior.
- CI enforcement truth is defined by:
  - `project/verification-contract.yml`
  - `.github/workflows/ci.yml`
- `AGENTS.md` must mirror these enforcement artifacts and must not invent contradictory command sets.
## Environment Assumptions

- Python baseline: `3.13`.
- Run commands from repository root.
- Module invocation in this repo context requires `PYTHONPATH=src`.
- Use the project virtual environment interpreter, not a global interpreter:
  - PowerShell/Windows: `.\.venv\Scripts\python.exe`
  - POSIX shells: `./.venv/bin/python`

## Verification Commands (Contract)

Run the verification contract command set via the `.venv` interpreter:

```bash
PYTHONPATH=src ./.venv/bin/python -m pytest
./.venv/bin/python -m ruff check .
./.venv/bin/python -m ruff format --check .
./.venv/bin/python -m mypy src
./.venv/bin/python -m bandit -r src
./.venv/bin/python -m pip_audit
```

PowerShell equivalent:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit
```

## Verification policy

- `AGENTS.md` is the canonical source for repo-wide verification gates and governance checks.
- Shared verification mechanics used by skills should live in `references/shared-verification-and-proof-template.md`.
- Skills should reference that shared file for common verification flow, while keeping skill-specific assertions, stop conditions, and completion criteria local.
- Do not duplicate the full repo gate command set into skills unless a strong local reason requires it.

## Governance Verification Commands

Use governance entrypoint checks when touching governance artifacts or characterization contracts:

```bash
./.venv/bin/python project/scripts/verify_governance.py --check parity
./.venv/bin/python project/scripts/verify_governance.py --check characterization
./.venv/bin/python project/scripts/verify_governance.py --check all
```

PowerShell equivalent:

```powershell
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization
.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all
```

## Same-SHA CI Closure Discipline

For future route-work closure/progression claims, closure records must handle same-SHA CI evidence explicitly.

Required closure-evidence fields:
- local SHA
- workflow identity
- CI run id/url when same-SHA evidence exists
- per-required-job status summary for required CI jobs from `project/verification-contract.yml` (currently `test`, `security`, `quality`, `governance`)

If same-SHA CI evidence cannot be obtained:
- explicitly state inability to obtain CI evidence and why
- include a residual-risk note
- do not silently imply same-SHA evidence was validated

## LOC and Complexity Guardrails

Contract values (from `project/verification-contract.yml`):

- `src_max_lines: 300` with `src_mode: block`
- `tests_max_lines: 300` with `tests_mode: warn`
- anti-evasion policy is contract-bound:
  - `# fmt: off` / `# fmt: on` cannot be used to claim LOC compliance.
  - Multi-statement semicolon packing cannot be used to claim LOC compliance.
  - Dense inline control-flow suite packing cannot be used to claim LOC compliance.
  - Fail closed: if honest LOC cannot be established, mark the file/slice blocked.

Required behavior:

- Do not introduce or expand `src/` files past 300 LOC; split or extract instead.
- Treat test files above 300 LOC as a warning condition that requires explicit review and splitting consideration.
- LOC policy rationale: maintainability limits are valid only with honest, formatter-compatible structure; suppression/packing that hides readable line growth is noncompliant.
- Keep changes scoped to one objective; avoid broad, unrelated cleanup.

## Safety Invariants (Non-Negotiable)

- `dry_run` must prevent all write-equivalent API actions on write paths (POST/DELETE behavior).
- Dry-run gating must be preserved in both:
  - orchestration/application flow, and
  - API gateway/adapter layer.
- Backdrop delete/re-upload paths are safety-critical and must remain non-destructive under dry-run.
- Preserve API-first behavior: do not add direct Jellyfin media filesystem operations as primary workflow.
- Backups/restores are convenience snapshots only, not full disaster recovery.
- Backup/restore caveat is mandatory: if Jellyfin UUIDs change after rebuild/re-import, restore mapping can fail.

## Security and Secrets Rules

- Never commit API keys, tokens, credentials, or secret material.
- Never log, print, or echo sensitive values.
- Use redaction/safe logging patterns when adding diagnostics.

## Governance Artifact Rules (Do/Don't)

Do:

- Keep parity/route-fence/contract artifacts schema-accurate and validator-compatible.
- If touching `project/parity-matrix.md` or `project/route-fence.md`, run:
  - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check parity`
- If touching `tests/characterization/` tests or baselines, run:
  - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check characterization`
- Before completion, run:
  - `.\.venv\Scripts\python.exe project/scripts/verify_governance.py --check all`

Don't:

- Do not casually reformat or restructure governance artifacts.
- Do not silently change observed behavior during refactors.
- If behavior looks suspicious, capture/label characterization and parity status explicitly rather than "fixing" behavior implicitly.

## Repo Navigation (Minimal)

- CLI implementation entrypoint: `src/jfin/cli.py`
- Common run pattern in repo context:
  - POSIX: `PYTHONPATH=src ./.venv/bin/python -m jfin ...`
  - PowerShell: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m jfin ...`
- Runtime code: `src/jfin/`
- Governance artifacts and validators: `project/`
- Characterization contracts and baselines: `tests/characterization/`
- Detailed architecture and behavior notes: `docs/TECHNICAL_NOTES.md`

## Nested Override Policy

- No nested `AGENTS.md` files are created in this pass.
- Candidate override zones for future specialization:
  - `project/`
  - `tests/characterization/`
  - `src/jfin/`
- Add scoped overrides only when specialization pressure is clear, such as:
  - format/schema-sensitive artifacts enforced by validators,
  - safety-critical write paths,
  - large characterization harness/baseline areas needing tighter local constraints.

## Definition of Done

A change is done only when all items below are true:

- Scope is limited to one objective.
- Required verification commands are run and pass in the intended Python 3.13 environment.
- Applicable governance checks are run for touched artifacts.
- Safety invariants remain intact and are explicitly preserved.
- Docs/contracts are updated when behavior, commands, layout, or governance expectations change.

## When to Update This File

Update `AGENTS.md` in the same PR when any of the following change:

- Verification commands, Python baseline, or LOC policy.
- CI job expectations in `.github/workflows/ci.yml`.
- Safety invariants (`dry_run` gating, write-path protections, backup/restore semantics).
- Governance workflow commands or artifact locations.
- Instruction layering policy or override strategy.

## References

Local repository sources:

- `project/verification-contract.yml`
- `.github/workflows/ci.yml`
- `docs/TECHNICAL_NOTES.md`
- `README.md`
- `references/skill-catalog-routing.md`
- `references/shared-verification-and-proof-template.md`

External AGENTS guidance and examples:

- https://agents.md/
- https://developers.openai.com/codex/guides/agents-md/
- https://docs.gitlab.com/user/duo_agent_platform/customize/agents_md/
- https://docs.qodo.ai/qodo-documentation/qodo-gen/agent/agents.md-support
- https://raw.githubusercontent.com/openai/openai-agents-python/main/AGENTS.md
- https://github.com/getsentry/sentry/blob/master/AGENTS.md
- https://raw.githubusercontent.com/google/adk-python/main/AGENTS.md
- https://raw.githubusercontent.com/fgmacedo/python-statemachine/develop/AGENTS.md
- https://github.com/strands-agents/sdk-python/blob/main/AGENTS.md
