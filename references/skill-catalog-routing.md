# Skill Catalog Routing Artifact

## Purpose

This artifact defines how to choose the right skill first, when to load a companion skill, which nearby skill is a near-miss that should not lead, and when to hand off as the task changes phase.

This is catalog-level routing guidance, not a triggerable skill. It exists because the main weakness in the current library is selection ambiguity between adjacent skills, not missing runbooks.

---

## Core routing rules

### 1) Choose the phase-specific skill first

Pick the skill that matches the task's current phase:

* Before coding starts -> `plan-first-scope-and-risks`
* While implementing, when the change is sprawling -> `loc-and-complexity-discipline`
* During or after validation/proof -> `verification-gates-and-diff-discipline`
* After implementation, when independent compliance reporting is needed -> `audit-governance-and-slice-compliance`

This phase split is the primary routing rule for planning / implementation / verification / audit.

### 2) Choose the narrower domain skill over the broader one

If a specialized skill clearly matches, it should lead over a broad baseline skill.

Examples:

* Python structural refactor -> `safe-refactor-python-modules` leads over `python-quality-bar`
* Python bug diagnosis and corrective fix -> `python-bug-triage-and-regression-fix` leads over `python-quality-bar`
* Jellyfin endpoint and schema contract selection -> `jellyfin-openapi-reference` leads over `jellyfin-api-client-safety`
* Jellyfin client request-semantics safety work -> `jellyfin-api-client-safety` leads over `jellyfin-openapi-reference`
* Imaging characterization and golden preservation work -> `pytest-characterization-tests-for-imaging` leads over generic Python overlays
* CLI/config contract change -> `cli-and-config-contract` leads over `docs-self-healing-update-loop`
* General Python work without a narrower match -> `python-quality-bar` can lead

### 3) Use broad skills as overlays, not replacements

Some skills are best treated as a default overlay or companion, not the first-choice owner.

* `python-quality-bar` is the default Python quality overlay
* `docs-self-healing-update-loop` is usually a companion for synchronization after externally visible changes
* `verification-gates-and-diff-discipline` may accompany other work, but it becomes primary only when the main task is proving, validating, and reporting verification
* `audit-governance-and-slice-compliance` is an independent audit/reporting owner, not an implementation owner

### 4) Escalate when the task changes phase

A task may legitimately move across skills over time.

Typical progression:

* plan -> implement -> verify
* bug triage/fix -> verification report
* OpenAPI contract mapping -> client safety implementation -> verification
* imaging characterization lock -> implementation/refactor -> verification
* implementation complete -> governance audit
* contract change -> docs sync

This is not overlap failure. It is intended phase handoff.

---

## Primary routing matrix

| Skill | Primary use | Choose first when | Typical companion(s) | Near-miss that should not lead | Handoff / escalation |
| --- | --- | --- | --- | --- | --- |
| `plan-first-scope-and-risks` | Pre-coding planning | The request is non-trivial and needs scoping, blast-radius analysis, staged milestones, rollback, or a read-only exploration phase before edits | `cli-and-config-contract`, `safe-refactor-python-modules`, `verification-gates-and-diff-discipline` later | `loc-and-complexity-discipline`, `verification-gates-and-diff-discipline` | Hand off to the implementation skill once scope, risks, and milestones are defined |
| `loc-and-complexity-discipline` | Implementation-time complexity control | The change is already in progress and starts to sprawl in LOC, file size, branching, helper layers, or scaffolding | `python-quality-bar`, `verification-gates-and-diff-discipline` | `plan-first-scope-and-risks`, `verification-gates-and-diff-discipline` | Hand off to verification once the implementation is scoped back down and ready to prove |
| `verification-gates-and-diff-discipline` | Verification and proof | Code has changed and the main question is what to run, in what order, and how to prove the change is safe | Any implementation skill; sometimes `docs-self-healing-update-loop` if public-surface changes must be confirmed/documented | `plan-first-scope-and-risks`, `loc-and-complexity-discipline` | Escalate back only if failures reveal missing planning, oversized scope, or mixed objectives |
| `audit-governance-and-slice-compliance` | Independent governance and slice-plan audit | Work claims slice completion or checkpoint readiness and needs an evidence-based Track 1 audit report | `verification-gates-and-diff-discipline` for command evidence; `plan-first-scope-and-risks` for remediation planning after findings | `verification-gates-and-diff-discipline` when the task is only in-flight verification | Hand off findings to the matching implementation/contract skill for fixes; rerun audit after remediation |
| `python-quality-bar` | Default Python quality overlay | The task is a normal Python code change and no narrower Python skill dominates | `loc-and-complexity-discipline`, `verification-gates-and-diff-discipline`; companion to `safe-refactor-python-modules`, `python-bug-triage-and-regression-fix`, and `jellyfin-api-client-safety` | `safe-refactor-python-modules`, `python-bug-triage-and-regression-fix`, `pytest-characterization-tests-for-imaging`, `jellyfin-api-client-safety` when the task is specialized | Stay as overlay; hand off primary ownership if work becomes a specialized domain workflow |
| `python-bug-triage-and-regression-fix` | Defect diagnosis and corrective Python fix | A Python bug/regression, crash, exception, or wrong output must be reproduced, root-caused, fixed with minimal scope, and protected with a regression test | `python-quality-bar`, then `verification-gates-and-diff-discipline`; add `docs-self-healing-update-loop` only when externally visible behavior changes | `python-quality-bar` for defect-first work; `verification-gates-and-diff-discipline` before diagnosis/fix work is done | Hand off to verification after reproducer passes and regression test is in place |
| `safe-refactor-python-modules` | Behavior-preserving Python refactor | The task is splitting, extracting, moving, or reorganizing Python code without changing observable behavior | `python-quality-bar`, `verification-gates-and-diff-discipline` | `python-quality-bar` as primary for this case | Hand off to non-refactor implementation if behavior must change; hand off to verification when slices are complete |
| `pytest-characterization-tests-for-imaging` | Imaging characterization and golden preservation | You are changing `src/jfin/imaging.py` or adjacent rendering/resize behavior and need `IMG-*` baseline/golden coverage before refactor or risky behavior changes | `safe-refactor-python-modules`, `python-bug-triage-and-regression-fix`, `verification-gates-and-diff-discipline` | `python-quality-bar` when imaging contract-locking is the main objective | Hand off to refactor/fix implementation after contracts are locked; hand off to audit when compliance reporting is required |
| `jellyfin-openapi-reference` | Jellyfin API contract source of truth | You need correct endpoint/method/params/request/response/auth shape from local Jellyfin OpenAPI JSON | `jellyfin-api-client-safety` when HTTP semantics are changing, `verification-gates-and-diff-discipline` | `jellyfin-api-client-safety` when task is retry/timeout/TLS/auth/dry-run/write-gate behavior | Hand off to implementation/client-safety work once operation contract is established |
| `jellyfin-api-client-safety` | Jellyfin HTTP client safety semantics | You are changing auth headers, retries/backoff, timeouts, TLS verification, redirects, or dry-run/write gates in client request handling | `jellyfin-openapi-reference` for endpoint contract clarification, `python-quality-bar`, `verification-gates-and-diff-discipline` | `jellyfin-openapi-reference` when task is endpoint selection or request/response schema mapping | Hand off to verification for proof; hand off to docs sync if externally visible safety behavior changes |
| `cli-and-config-contract` | User-facing CLI/config contract ownership | The task changes flags/options, subcommands, config keys/schema, defaults, precedence, validation, help text, or migration behavior | `docs-self-healing-update-loop`, `verification-gates-and-diff-discipline`, sometimes `plan-first-scope-and-risks` | `docs-self-healing-update-loop` | Hand off to docs sync after contract decisions are implemented; hand off to verification for proof |
| `docs-self-healing-update-loop` | Post-change synchronization | Externally visible behavior is already decided or already changed and docs/examples/templates/agent guidance must be brought back in sync | Usually `cli-and-config-contract`, but also any implementation/refactor/verification skill | `cli-and-config-contract` when deciding behavior | Hand off back to primary contract/domain skill if underlying behavior is still undecided |

---

## Companion logic

### Default companion patterns

**Jellyfin endpoint contract mapping**

* Primary: `jellyfin-openapi-reference`
* Companion: `jellyfin-api-client-safety` only if request semantics or client safety behavior are changing
* Finish with: `verification-gates-and-diff-discipline`
  Rationale: OpenAPI skill owns endpoint contract correctness; client-safety skill owns HTTP transport semantics and write safety boundaries.

**Jellyfin client safety hardening**

* Primary: `jellyfin-api-client-safety`
* Companion: `jellyfin-openapi-reference` if endpoint contract details are ambiguous
* Companion: `python-quality-bar`
* Finish with: `verification-gates-and-diff-discipline`
* Add docs sync only if behavior changed externally: `docs-self-healing-update-loop`
  Rationale: client-safety skill owns retries/timeouts/auth/TLS/dry-run gating; OpenAPI remains the API contract companion.

**Imaging behavior-preservation before risky change**

* Primary: `pytest-characterization-tests-for-imaging`
* Then: `safe-refactor-python-modules` or `python-bug-triage-and-regression-fix` depending on whether behavior should be preserved or corrected
* Finish with: `verification-gates-and-diff-discipline`
  Rationale: imaging characterization establishes stable baseline/golden contracts before implementation work.

**Post-implementation governance checkpoint**

* Primary: `audit-governance-and-slice-compliance`
* Companion: `verification-gates-and-diff-discipline` for reproducible command evidence
* Then: hand findings to matching implementation skills for remediation
* Finish by rerunning: `audit-governance-and-slice-compliance`
  Rationale: audit skill is independent read/verify/report; remediation belongs to domain skills.

**Python bug diagnosis and corrective fix**

* Primary: `python-bug-triage-and-regression-fix`
* Companion: `python-quality-bar`
* Finish with: `verification-gates-and-diff-discipline`
* Add docs sync only if behavior changed externally: `docs-self-healing-update-loop`
  Rationale: bug-triage skill owns diagnosis plus minimal corrective fix plus regression lock.

**Python structural refactor**

* Primary: `safe-refactor-python-modules`
* Companion: `python-quality-bar`
* Finish with: `verification-gates-and-diff-discipline`
  Rationale: refactor skill owns behavior-preserving structure, quality-bar stays overlay.

**General Python implementation**

* Primary: `python-quality-bar`
* Companion: `loc-and-complexity-discipline` only if diff starts to sprawl
* Finish with: `verification-gates-and-diff-discipline`
  Rationale: quality-bar is baseline for normal Python work.

**CLI/config change**

* Primary: `cli-and-config-contract`
* Companion: `docs-self-healing-update-loop`
* Finish with: `verification-gates-and-diff-discipline`
* Add upfront planning: `plan-first-scope-and-risks` if the contract change is risky, multi-file, or migration-heavy
  Rationale: contract skill owns semantics; docs skill propagates; verification proves.

---

## Near-miss exclusions

These are the highest-value "do not lead with this" rules.

### `audit-governance-and-slice-compliance`

Do not lead with this while actively implementing a slice or making code changes. It should run after implementation work (or as a mid-flight checkpoint) and produce findings, not fixes.

### `jellyfin-openapi-reference`

Do not lead with this for Jellyfin UI/how-to, plugin setup, or non-API troubleshooting. Do not lead with this when the main task is client retries/timeouts/TLS/auth/dry-run/write-gate behavior.

### `jellyfin-api-client-safety`

Do not lead with this for endpoint discovery or request/response schema selection; use `jellyfin-openapi-reference` first for API contract truth. Do not lead for non-client application logic.

### `pytest-characterization-tests-for-imaging`

Do not lead with this for CLI/config characterization, API safety contracts, or pipeline/restore behavior. Use it only for imaging behavior preservation contracts.

### `verification-gates-and-diff-discipline`

Do not lead with this when the real problem is pre-coding planning, implementation sprawl, or unresolved root-cause diagnosis.

### `python-quality-bar`

Do not lead with this when the task is clearly a structural refactor, bug-triage workflow, imaging characterization run, or Jellyfin client safety semantics change.

### `docs-self-healing-update-loop`

Do not lead with this when contract or behavior is still undecided.

---

## Escalation handoff rules

### Handoff: planning -> implementation

When `plan-first-scope-and-risks` has produced a clear scope, milestones, verification gates, and rollback strategy, hand off to the narrowest implementation skill:

* Python bug diagnosis and corrective fix -> `python-bug-triage-and-regression-fix`
* Python refactor -> `safe-refactor-python-modules`
* Imaging contract lock -> `pytest-characterization-tests-for-imaging`
* Jellyfin API contract mapping -> `jellyfin-openapi-reference`
* Jellyfin client request-safety semantics -> `jellyfin-api-client-safety`
* CLI/config behavior change -> `cli-and-config-contract`
* General Python edit -> `python-quality-bar`
* Change sprawl during coding -> `loc-and-complexity-discipline`

### Handoff: OpenAPI contract mapping -> client safety

When `jellyfin-openapi-reference` has established endpoint contract details and the remaining risk is HTTP semantics (retry/timeout/TLS/auth/write-gate), hand off to `jellyfin-api-client-safety`.

### Handoff: imaging characterization -> implementation

When `pytest-characterization-tests-for-imaging` has locked relevant `IMG-*` baseline/golden behavior, hand off to:

* `safe-refactor-python-modules` for behavior-preserving structural work
* `python-bug-triage-and-regression-fix` for behavior-corrective defect work

### Handoff: implementation -> verification

When code changes are ready to validate, hand off to `verification-gates-and-diff-discipline`.

### Handoff: implementation -> docs sync

When externally visible behavior is finalized and only propagation remains, hand off to `docs-self-healing-update-loop`.

### Handoff: implementation -> governance audit

When a slice/branch claims completion and needs independent compliance evidence, hand off to `audit-governance-and-slice-compliance`.

### Handoff: audit findings -> remediation loop

If audit reports blockers or major gaps, hand off to `plan-first-scope-and-risks` for remediation sequencing, then to the matching implementation skill. Rerun audit after fixes.

---

## Fast chooser

Use this as the short routing index:

* "We have not coded yet; map risks and safe stages." -> `plan-first-scope-and-risks`
* "This change keeps growing; keep it small and local." -> `loc-and-complexity-discipline`
* "Code changed; tell me exactly how to verify it." -> `verification-gates-and-diff-discipline`
* "Audit this slice/PR for governance and slice-plan compliance." -> `audit-governance-and-slice-compliance`
* "Which Jellyfin endpoint/params/schema/auth shape is correct?" -> `jellyfin-openapi-reference`
* "Change Jellyfin client retries/timeouts/TLS/auth/dry-run write gates safely." -> `jellyfin-api-client-safety`
* "We are touching imaging behavior and need characterization/golden safety tests first." -> `pytest-characterization-tests-for-imaging`
* "This is a normal Python change." -> `python-quality-bar`
* "A Python bug/regression needs reproduce -> root-cause -> minimal fix -> regression test." -> `python-bug-triage-and-regression-fix`
* "This is a Python refactor without behavior change." -> `safe-refactor-python-modules`
* "This changes flags/config/defaults/validation/precedence." -> `cli-and-config-contract`
* "Behavior is already decided; sync docs/examples/guidance." -> `docs-self-healing-update-loop`

---

## Catalog governance note

This artifact should be maintained whenever:

* a skill changes role or scope,
* a new skill is added,
* a primary/companion relationship changes,
* repeated routing collisions are observed in practice.

That follows the report's recommendation to improve the catalog as a system, not just individual files.
