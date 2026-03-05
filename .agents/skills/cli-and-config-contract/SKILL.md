---
name: cli-and-config-contract
description: Safely evolve a Python CLI and TOML configuration schema without breaking users. Use when adding/changing flags, defaults, validation rules, config generation, or config migration behavior. Includes a step-by-step workflow for: precedence rules, exclusivity constraints, deprecation strategy, documentation sync, and contract/characterization tests.  Don't use for runtime/image-processing behavior changes unless they are strictly driven by CLI/config interface changes.
metadata:
  version: "2.0.0"
  updated: "2026-03-04"
  owners: "@codex @alexkahler"
  notes: Assumes Python 3.11+ so TOML can be parsed via stdlib tomllib; if supporting older Python, you'll need tomli (and should document/pin it). If the repo uses baseline/characterization contracts for CLI/config (recommended), update those artifacts as part of this workflow.
---

# CLI and Config Contract

## Scope and intent

This skill is a runbook for changing a CLI + TOML config **public interface** safely:
- Add/change CLI flags or subcommands
- Change defaults, constraints, or validation rules
- Modify precedence (CLI vs config vs environment variables)
- Modify config template generation (`--generate-config` / init commands)
- Introduce config migration or schema versioning
- Tighten/relax exclusivity rules (e.g., restore vs run flags)

**Non-goals**
- Refactoring internals that does not affect parsing/validation/precedence or user-visible docs
- Changing operational semantics unrelated to CLI/config surface (do those separately, with their own contract tests)

---

## Inputs and preconditions

Before editing code, confirm:

- Where parsing lives (e.g., `src/**/cli.py`, `src/**/config.py`)
- Where user docs live (README, docs pages, `config.example.toml`)
- Whether the repo has:
  - Contract/characterization tests + baseline artifacts for CLI/config
  - Governance/verification gates in `AGENTS.md` and CI
- Whether config parsing is TOML-only and what the supported Python baseline is

---

## Contract principles (what must remain true)

### 1) One source of truth for "effective configuration"
At runtime, the program should be able to explain:
- Which value is effective
- Where it came from (default vs config vs CLI vs env)
- Why a conflicting value was ignored or rejected

### 2) Explicit precedence order (must be documented)
Pick one and keep it stable unless intentionally changed:
- CLI overrides config
- Config overrides defaults
- Environment variables (if used) have a defined position in precedence

### 3) Validation must be deterministic and user-facing
- Invalid inputs must fail with a clear message and a non-zero exit status
- Mutually exclusive combinations must be rejected early
- "No-op" options (options that do nothing in the chosen mode) must either:
  - warn clearly, or
  - be rejected (choose one policy and enforce it consistently)

### 4) Backward compatibility is a deliberate choice
For any interface change, choose one:
- **Compatible**: accept old + new forms; warn on old; document migration
- **Breaking**: reject old forms; add a prominent release note and upgrade guide

---

## Workflow

### Step 0 — Classify the change
Write a one-paragraph change classification (in the PR description or issue):
- **Surface**: new flag, renamed flag, changed default, new config key, removed key, new constraint, etc.
- **Risk**: low/medium/high (high = could stop runs or change outputs broadly)
- **Compatibility plan**: compatible vs breaking

**If breaking:** add an explicit "upgrade notes" section in docs and ensure tests assert the new failure mode.

---

### Step 1 — Define the contract update (before coding)
Make the change explicit as a set of contract statements:

- New/changed CLI syntax (including help text intent)
- New/changed config keys and their types
- Precedence rule (who wins)
- Exclusivity rules (what cannot be combined)
- Default changes (old → new)
- Deprecation behavior (warning text + timeline, if applicable)

**Output of this step:** a short checklist you can translate directly into tests.

---

### Step 2 — Update parsing and data model
Implement changes in a way that keeps parsing separate from execution:

- Parse CLI → typed args structure
- Load config TOML → typed config structure
- Merge → "effective config" with provenance tracking where possible

**If introducing new config keys:**
- Validate type and allowed values
- Decide how unknown keys are handled:
  - error (strict), or
  - warning (permissive)
Pick one consistent policy.

**If introducing new CLI flags:**
- Make names stable and consistent (kebab-case for long options)
- Avoid ambiguous boolean flags; prefer explicit enums where it helps clarity

---

### Step 3 — Enforce exclusivity and "mode correctness"
Add hard checks for incompatible combinations.

Common patterns:
- "Operational flags" must be rejected with "config init / generate config" commands
- Restore operations must reject run-only flags
- Single-target operations may require an explicit mode/image-type selector

**If a flag is mode-specific:**
- Decide policy for "flag provided but mode not selected":
  - warn (and ignore), or
  - error
Document the policy and test it.

---

### Step 4 — Deprecation strategy (when renaming/removing)
If you are changing a CLI/config name:

1) Keep the old name working (if compatible), but emit a warning:
   - Warning must say: what to use instead
2) Add a doc note + examples using the new name
3) Add tests asserting:
   - old name still works (until removal)
   - warning is emitted
   - new name works
4) Decide removal timing and record it in changelog/release notes

**If breaking now:** ensure error text includes the replacement and migration hint.

---

### Step 5 — Update docs and templates (no drift allowed)
Update all user-facing references in the same change:

- README usage examples
- `config.example.toml` (or equivalent template)
- Advanced usage docs / feature tour pages
- Any "generated config" output (if the tool emits comments or defaults)

**Rule:** If the tool can generate a config, that output is a contract surface too.

---

### Step 6 — Update contract tests / characterization baselines
Add or update tests to pin the behavior.

Minimum test set for any CLI/config change:
- **Happy path parsing**: new syntax works
- **Validation**: invalid values fail with clear messages
- **Exclusivity**: incompatible combinations are rejected
- **Precedence**: CLI overrides config (or whatever your rule is)
- **No-op policy**: warn or error is asserted
- **Template generation**: `--generate-config` output includes new key/default (when relevant)

If your repo uses baseline/characterization artifacts:
- Update the baseline JSON (or snapshot) to include the new behavior ID/entry
- Ensure governance/linkage checks still pass

---

### Step 7 — Verification gates (run before declaring done)
Run the repo's verification commands (from `AGENTS.md` / CI contract).
At minimum (typical Python repos):
- Unit tests
- Lint/format checks
- Type checks (if enforced)
- Governance/contract checks (if present)

---

## Verification checklist (Definition of Done)

- [ ] CLI help + examples reflect the new interface
- [ ] Config template/example reflects the new schema
- [ ] Exclusivity rules are enforced with clear errors
- [ ] Precedence is tested (effective config is correct)
- [ ] Deprecations (if any) warn with a migration hint
- [ ] Contract/characterization baselines (if present) updated
- [ ] All verification gates pass

---

## Troubleshooting

### Symptom: "Flag does nothing" confusion
**Likely cause:** mode-specific option supplied without selecting that mode  
**Fix:** enforce policy (warn+ignore or error), document it, add tests.

### Symptom: "Generated config doesn't include the new key"
**Likely cause:** template generator is not sourced from the same schema as runtime defaults  
**Fix:** generate template from the same default config model; add a template regression test.

### Symptom: "Users can't tell which value won"
**Likely cause:** merge logic lacks provenance or logging  
**Fix:** add an "effective config summary" log block (or debug output) and test for key lines.

### Symptom: "Mutually exclusive flags still parse"
**Likely cause:** exclusivity enforced in execution, not in parse/validate stage  
**Fix:** move the check into validation; ensure error occurs before any side effects.

---

## Examples

### SHOULD trigger this skill
- "Add a new `--foo` flag and update the config to support it."
- "Rename a config key and keep backward compatibility with a warning."
- "Make `--restore` reject operational flags and document the behavior."
- "Change the default size/quality and ensure docs + tests match."

### SHOULD NOT trigger this skill (near misses)
- "Refactor the image pipeline for performance without changing CLI/config."
- "Update Docker instructions without changing flags or config schema."
- "Fix a bug in JPEG encoding output (unless a CLI/config option controls it)."

---

## References and related resources (repo-local)
- `config.example.toml` — example schema and defaults (must stay in sync)
- `docs/advanced-usage.md` — advanced patterns and mode-specific options
- `docs/TECHNICAL_NOTES.md` — reference for current CLI/config behavior and flow
- Contract tests/baselines — if present under `tests/**/cli_*` and `tests/**/config_*`

## Changelog
- 2026-03-04 (v2.0.0): Rewritten as a contract-first runbook with explicit
  precedence/exclusivity/deprecation workflows, verification checklist, troubleshooting,
  and trigger/near-miss examples. Agnostic to internal implementation variants.