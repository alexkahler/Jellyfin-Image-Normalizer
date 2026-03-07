---
name: cli-and-config-contract
description: Primary skill for changing a user-facing CLI or configuration contract: flags/options, subcommands, config keys/schema, defaults, validation, precedence, help text, config generation, and migration behavior. Use this first when a request changes how users invoke the program or configure it, including argparse/click/typer interfaces and TOML/YAML/JSON/env-backed settings. Companion skill: use docs-self-healing-update-loop after the contract change when README, docs, examples, templates, or agent guidance must be synchronized. Don't use for purely internal refactors that do not affect user-visible behavior.
metadata:
  version: "2.1.0"
  updated: "2026-03-07"
  owners: 
    - "@codex"
    - "@alexkahler"
  notes: Repo-agnostic. Assumes the repo has AGENTS.md with verification gates and CI. If your repo does not have (a) a public CLI entrypoint, (b) documented config format, or (c) a config example/template, you must add those artifacts (or adjust this skill) before it can be applied as-written.
compatibility: Primary language: Python. Works with argparse/click/typer and common config formats (TOML/YAML/JSON/env). If using TOML, prefer Python 3.11+ (tomllib) or a TOML library; adapt validation tooling as needed.
---

# CLI and Config Contract

This is the **primary skill** for user-facing interface contract changes. If a request changes how a user runs the program, supplies options, provides configuration, relies on defaults, or encounters validation/error behavior, start here.

A CLI + config surface is a **public interface**. Treat changes like API changes: make behavior explicit, keep backward compatibility when feasible, and ship tests + docs with every externally observable change.

## Scope and intent

This skill owns:
- Flags/options, subcommands, help text, exit codes, and user-facing error behavior
- Config keys/schema, defaults, validation, deprecations, and compatibility shims
- Precedence/merge behavior across CLI, config files, environment variables, and defaults
- "Generate config" / "print config" / "validate config" features
- Config migrations and contract-level behavior changes

Use this skill as the **first-choice entry point** when the change affects the external invocation/configuration contract.

Companion relationship:
- If the contract change also requires README/docs/example/template/agent-guidance updates, use `docs-self-healing-update-loop` as a **companion after or alongside this skill**.
- Documentation synchronization does **not** replace contract ownership; this skill remains primary for deciding and implementing the behavior change.

Non-goals:
- Pure refactors with zero user-visible effect (use normal dev process instead)
- Large multi-module redesigns before the interface change is well-scoped (use your repo's planning skill / plan-first process)
- Generic docs cleanup that does not follow from a contract change (prefer the docs skill directly)

## Routing boundaries

Choose this skill over nearby skills when:
- The main question is **what users can pass, configure, or expect**
- The change touches flags, options, keys, defaults, precedence, validation, help output, or config compatibility
- The request includes words like: "flag", "option", "subcommand", "config", "settings", "default", "env var", "precedence", "schema", "YAML", "JSON", "TOML", "rename config key", "deprecate option"

Prefer a different primary skill when:
- The task is a purely internal Python refactor with no contract change → use the refactor/Python quality skill
- The task is mainly about planning a risky multi-step change before implementation starts → use the planning skill first
- The task is mainly about validating/proving an already-implemented change → use the verification skill
- The task is only about syncing docs after behavior is already settled → use the docs skill as primary

## Inputs and preconditions

Before editing code, identify and write down:
- **Public entrypoints**:
  - CLI executable/module (e.g., `python -m pkg`, `pkg` console script, `cli.py`)
  - Config file(s) used/accepted (names, locations, discovery rules)
- **Current behavior baseline**:
  - Default values
  - Precedence order (e.g., CLI > env > config > defaults)
  - Validation rules and error behavior (messages + exit codes)
- **Where docs live**:
  - README usage examples
  - `docs/` pages
  - example config/template file(s) (if any)

If you cannot point to a documented baseline, add minimal documentation first (even a short "Current behavior" section).

## Tools and permissions

- Use unit tests as the source of truth for behavior.
- Follow the repo's verification gates in **AGENTS.md** (do not invent new gate commands).
- Avoid broad rewrites: keep diffs scoped to the contract change.
- Treat contract changes as externally visible even when the code diff is small.

## Contract invariants (do not violate silently)

1) **Precedence must be explicit and stable**
- Document and test the precedence order.
- If you change precedence, treat it as a breaking/behavior change and add migration notes.

2) **Errors must be actionable**
- Invalid inputs/config must produce:
  - clear error message (what + how to fix)
  - stable non-zero exit code
- Do not turn formerly-valid inputs into hard failures without a deprecation/migration path (unless explicitly requested).

3) **Defaults are part of the public surface**
- Changing defaults is a behavioral change; tests and docs must reflect it.

4) **Single-source-of-truth for parsing/validation**
- Avoid duplicating validation rules across CLI parsing and config loading.
- Prefer one canonical validation layer used by both CLI-only and config-driven paths.

## Workflow

### 1) Classify the change (choose the smallest safe path)
- **Additive**: new flag/config key that doesn't change existing behavior → usually safe.
- **Behavioral**: changes defaults, precedence, or meaning of an existing flag/key → requires strong tests + docs updates.
- **Breaking**: removes/renames flags/keys or changes accepted values → requires a deprecation/migration plan (or explicit approval).

### 2) Confirm primary ownership
Before making changes, confirm that the request is primarily about the external contract:
- If users will notice a different command, option, config shape, default, precedence rule, validation outcome, or migration path, this skill is the owner.
- If docs/examples must also change, note that `docs-self-healing-update-loop` is a companion task, not the decision-maker for contract semantics.

### 3) Update the contract surface (code)
Make the smallest change that achieves the goal:
- CLI:
  - add/adjust flag/subcommand definitions
  - update help text and examples (help output is user-facing)
  - ensure parsing rules remain deterministic (avoid ambiguous combinations)
- Config:
  - update schema definition and validation
  - maintain stable key naming and structure unless migrating
  - keep config loading + CLI parsing aligned (same defaults, same validation)

**If/then decision rules**
- If you **rename/remove** a flag or key:
  - keep a compatibility alias when feasible (old name still works)
  - emit a deprecation warning (not a hard error) for at least one release cycle (or as your repo policy dictates)
  - document the replacement and timeline
- If you **change meaning** of a flag/key:
  - prefer introducing a new flag/key and deprecating the old behavior
  - only "flip semantics" directly when explicitly requested and versioned as breaking

### 4) Add/extend tests (contract tests first)
Minimum required tests for any contract change:

**CLI parsing tests**
- Happy path: parses and maps to the intended internal representation
- Invalid values: produces clear error + non-zero exit code
- Interaction/exclusivity: incompatible options fail clearly (or resolve deterministically)
- Precedence test(s): confirm CLI overrides config/env as documented

**Config tests**
- Schema validation: missing/unknown/invalid keys behave as intended
- Defaults: loaded config + missing keys yield correct defaults
- Merge behavior: multiple config sources merge deterministically (if supported)

**Migration tests** (if applicable)
- Old config/flags still work (or produce the expected deprecation warning)
- New config/flags behave correctly
- Round-trip test for config generation (if you have "generate-config"):
  - generated config validates
  - generated config is consistent with current defaults

Testing guidance:
- Prefer parametrized "decision tables" for flags/keys/value combos.
- Use `tmp_path` for temporary config files.
- Keep tests focused on observable behavior: output, exit codes, and parsed/validated results.

### 5) Update docs and examples (keep them runnable)
Update all user-facing references that mention the changed surface:
- README "Usage" section and copy/paste examples
- `docs/` pages (advanced usage, config reference)
- Example config/template file(s)
- Shell completions (if your repo generates them) and `--help` snapshots (if tracked)

Rules:
- Examples must match reality (commands and flags must actually work).
- If behavior changes, include a short "Migration / Breaking changes" note with before/after snippets.
- If the documentation impact is broad, load `docs-self-healing-update-loop` as a companion and synchronize every externally visible reference.

### 6) Run verification
Use `references/shared-verification-and-proof-template.md` for the common verification flow:
- run the smallest relevant checks first,
- use `AGENTS.md` as the canonical source for repo gates,
- apply stop-and-fix,
- and record a short verification note.

For this skill, the targeted checks should focus on CLI/config behavior first.

## Verification checklist (must complete before declaring done)
- [ ] Tests cover new/changed flag and/or config behavior (including precedence)
- [ ] Invalid inputs produce clear errors (message + exit code)
- [ ] Docs/examples updated and consistent with the implementation
- [ ] If breaking/behavioral: migration/deprecation path is documented and tested
- [ ] Repo verification gates (AGENTS.md) pass
- [ ] Contract ownership remained clear: external behavior decisions were made here, with docs sync handled as a companion if needed

## Completion criteria (stop condition)
You are done when:
- The updated contract is enforced by tests,
- Documentation and examples match the new behavior,
- And CI/verification gates pass without special casing.

## Troubleshooting

**Symptom:** "Docs say X but CLI does Y"
- Likely cause: examples weren't updated or defaults changed silently.
- Fix: add a test that asserts the documented example behavior; update docs and/or code to match.

**Symptom:** "Old config file no longer works"
- Likely cause: key rename/removal without a compatibility shim.
- Fix: add migration/alias handling and tests; add a deprecation warning and a migration note.

**Symptom:** "Ambiguous option combinations produce weird behavior"
- Likely cause: missing mutual exclusion or precedence rule.
- Fix: enforce exclusivity or deterministic precedence; add interaction tests.

**Symptom:** "Generated config differs from actual defaults"
- Likely cause: defaults defined in multiple places.
- Fix: centralize defaults and ensure generator reads from the same source; add a round-trip test.

**Symptom:** "A docs-oriented skill started to drive interface semantics"
- Likely cause: ownership confusion between contract and documentation updates.
- Fix: return contract decisions to this skill, then use the docs skill only to propagate the already-decided external behavior.

## Examples

### SHOULD trigger this skill
- "Add a new `--output-format` flag and document it."
- "Change the default compression level in the CLI and config."
- "Rename config key `foo_bar` to `foo-bar` but keep backward compatibility."
- "Update precedence so env vars override config file values."
- "Deprecate `--legacy-mode` and replace it with a config setting."

### SHOULD NOT trigger this skill
- "Refactor internal helper functions used by the CLI without changing behavior."
- "Rename a private variable inside config loading code."
- "Improve logging messages that are not part of user-facing errors/help."
- "Sync README examples after the interface behavior has already been finalized." 

## References and resources (optional, repo-dependent)
If present, update the relevant artifacts:
- README usage sections (CLI examples)
- docs/ (config reference, advanced usage)
- examples/ or assets/ config templates (e.g., `config.example.*`)
- Any "generate-config / validate-config" documentation
- AGENTS.md verification gates (do not duplicate the commands here)
- references/shared-verification-and-proof-template.md — use for the common verification flow and final proof note

Companion usage:
- `docs-self-healing-update-loop` — use when externally visible contract changes require synchronized updates across docs, examples, templates, release notes, or agent-facing guidance.

## Changelog
- 2026-03-07 / 2.1.0: Added explicit primary-skill positioning for user-facing CLI/config contract changes; clarified routing boundaries; marked docs-self-healing-update-loop as a companion rather than a co-owner.
- 2026-03-04 / 2.0.0: Generalized to be repo-agnostic; added explicit contract invariants, branching rules, verification-first workflow, and trigger examples.