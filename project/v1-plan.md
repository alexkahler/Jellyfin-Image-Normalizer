# JFIN v1 Track 1 Migration Blueprint

Plan version: v1.0-track1
Frozen on: March 3, 2026
Change policy: any scope/contract change requires explicit addendum

## Summary

1. This is a full, execution-ready **Track 1** plan for v0→v1.
2. Default architecture target remains **Option C (Workflow Cells)**.
3. **Public behavior is preserved by default**; interface/platform redesign is deferred to Track 2.
4. Planning mode only: this document is a blueprint; implementation happens slice-by-slice with verification and rollback.
5. Baseline health snapshot captured in v1: `174 passed in 6.99s` (`PYTHONPATH=src python -m pytest -q`). *(Historical baseline; not a guarantee of current runtime as changes land.)*

---

## 1) Scope Split

### Track 1 (in scope now)

* Decomposition and maintainability refactor
* Boundary enforcement (OOP/SOLID locality, clear responsibilities)
* Global-state removal and replacement with explicit context
* Workflow-cell extraction
* Centralization of core invariants
* Safety parity and behavior parity (characterization + goldens + parity matrix)

### Track 2 (deferred; out of scope for Track 1)

* CLI subcommands redesign (flat flags → subcommands)
* Config schema redesign (schema-first structured sections, new precedence tracking beyond compatibility)
* Exit-code taxonomy redesign (beyond Track-1-compatible semantics)
* Python baseline bump beyond current compatibility window

---

## 2) Compact Repo Map (Current Baseline)

### Entry Points and Runtime Flow

1. Entrypoint: `python -m jfin` → `src/jfin/__main__.py` → `src/jfin/cli.py`.
2. CLI flow (current): parse flags, load+merge config, validate, preflight Jellyfin, dispatch restore/single/library/profile workflows, map to exit semantics.
3. Processing flow (current): discovery → per-item normalization → optional backup → upload/delete → stats/logging.

### IO boundaries today

* Network: `src/jfin/client.py`
* Filesystem backup/restore/staging: `src/jfin/backup.py`
* Imaging transforms: `src/jfin/imaging.py`
* Global runtime state/logging: `src/jfin/state.py`, `src/jfin/logging_utils.py`

### Top 10 Largest Python Files (Current)

| File                     |  LOC | Responsibility                                                              |
| ------------------------ | ---: | --------------------------------------------------------------------------- |
| `tests/test_pipeline.py` | 1153 | Workflow behavior spec for normalization/backdrop/single-item/profile paths |
| `src/jfin/pipeline.py`   |  950 | Core orchestration for discovery, normalize, backdrop transaction-like flow |
| `src/jfin/cli.py`        |  682 | CLI contract, validation, config wiring, control-flow branching             |
| `src/jfin/client.py`     |  652 | Jellyfin HTTP API wrapper, retries, write gates, upload/delete              |
| `tests/test_backup.py`   |  621 | Restore/backup behavioral matrix, filename/index semantics                  |
| `src/jfin/config.py`     |  560 | TOML loading, schema-ish validation, CLI override merge, client factory     |
| `src/jfin/backup.py`     |  464 | Backup layout, restore walk/grouping/index logic, staging cleanup           |
| `src/jfin/imaging.py`    |  361 | Scale planning, padding/crop policies, encoding                             |
| `tests/test_config.py`   |  330 | Config parse/validate/override contract tests                               |
| `tests/test_imaging.py`  |  295 | Scale/crop/encoding unit behavior tests                                     |

### Coupling hotspots

1. `state.py` is the central coupling seam (fan-in ~8 modules).
2. `cli.py` has high fan-out (mixing parsing, policy, dispatch).
3. `pipeline.py` has high fan-out and mixes decisions with IO/logging/stats.
4. `config.py` imports client factory directly (blurs config vs infrastructure).
5. `constants.py` broadly shared (mixes schema defaults + operational constants).

### Side-effect hotspots

1. `client.py`: direct `requests.*`, retry sleeps, POST/DELETE behavior.
2. `pipeline.py`: server deletes/uploads plus local staging writes.
3. `backup.py`: recursive filesystem traversal and restore side effects.
4. `cli.py`, `config.py`, `discovery.py`: multiple `SystemExit/sys.exit` calls from non-entry layers (current baseline problem).
5. `logging_utils.py`: mutates global logger/state.

---

## 3) Architecture Options (Historical, for context)

> **Option C remains selected.** Options A/B are preserved here for completeness as they were part of Version 1 planning outputs.

### Option A: Domain-Oriented (Hexagonal)

* Boundaries: `domain` (entities/policies/ports), `app` (use-cases), `adapters` (HTTP/Pillow/FS), `bootstrap` (composition root), `cli` (transport only).
* Public APIs:

  1. `RunUseCase.execute(RunRequest) -> RunResult`
  2. `RestoreUseCase.execute(RestoreRequest) -> RestoreResult`
  3. `JellyfinGatewayPort`, `ImageEnginePort`, `BackupStorePort`, `ConfigProviderPort`
* Pros: strongest isolation, easiest long-term extension.
* Cons: highest churn/migration cost.

### Option B: Technical-Layer Oriented

* Boundaries: `cli`, `config`, `network`, `imaging`, `backup`, `workflow`.
* Public APIs:

  1. `workflow.process_run(context, request)`
  2. `workflow.process_restore(context, request)`
  3. `network.client`, `imaging.engine`, `backup.store`
* Pros: fastest refactor from current.
* Cons: risks business rules remaining spread.

### Option C: Workflow Cells (Selected Default)

* The selected target for Track 1 because it matches real seams (`command + mode`) and minimizes cross-module edits when extending.

---

## 4) CLI Compatibility Contract (Track 1)

1. Track 1 keeps the **current CLI flag surface**.
2. CLI parser remains as a **compatibility layer**.
3. Parsed args are mapped to **typed use-case requests**.
4. **No parser/UX redesign** in Track 1.
5. Only CLI layer may call `sys.exit`.

---

## 5) Architecture Blueprint and Boundaries (Track 1)

1. `bootstrap/container.py`: dependency wiring only.

2. `bootstrap/main.py`: command → **concrete use-case** resolution only.

3. CLI calls resolved use-case directly; **no generic `bootstrap.run(...)` orchestration hub**.

4. `app/use_cases/`: command orchestration:

* `run`, `restore`, `test_connection`, `config_init`, `config_validate`

5. `app/mode_processors/`: mode processors behind a common interface:

* `logo`, `thumb`, `backdrop`, `profile`

6. `app/services/`: explicit shared zone for cross-cell logic (examples preserved from v3):

* `discovery_service.py`
* `normalization_service.py`
* `backdrop_transaction_service.py`
* `staging_service.py`
* `result_aggregation_service.py`

7. `domain/`: pure rules and types only (no IO imports).
8. `adapters/`: Jellyfin HTTP, Pillow imaging, filesystem backup/staging, config providers, event sinks.

---

## 6) App Services Boundary Rule (Hard)

1. `app/services` may import `domain/*` and port interfaces.
2. `app/services` may **not** import concrete adapters.
3. `app/services` may **not** parse CLI args or config files directly.
4. `app/services` must remain transport-agnostic.

---

## 7) Workflow Cell Contract (Hard)

1. Each cell has one use-case entry file.
2. Main flow comprehension target is **≤3 files**.
3. **Escape hatch:** shared interfaces/types/policies are allowed as explicit extras beyond the 3 main-flow files.
4. Cross-cell imports are forbidden **except** shared contracts/services.
5. Any cell file **>200 LOC** triggers split review.

---

## 8) Error Flow Contract (Hard)

1. Only CLI calls `sys.exit`.
2. Non-entry layers raise typed exceptions only.
3. Exception set:

* `ValidationError`
* `ConnectivityError`
* `PolicyViolationError`
* `RestoreSafetyError`
* `ProcessingError`
* `FatalError`

4. Classification rules (from v3/v4):

* `PolicyViolationError`: skip/warning by default unless explicitly configured as hard-fail.
* `ValidationError`: operator-visible failure.
* `ConnectivityError`: fatal preflight failure.
* `ProcessingError`: item-level failure; continue unless fail-fast policy applies.
* `FatalError`: immediate abort.

5. Retryability rules:

* Retryable: transient connectivity/transport failures.
* Non-retryable: validation/policy/restore-safety violations.

6. Track 1 keeps existing exit semantics; only internal error flow changes.

---

## 9) Core Invariants Contract (Hard)

1. Centralize in `domain/model/`:

* `Mode`
* `ImageType`
* mode↔image-type mapping
* backup naming/index rules
* profile-vs-item image path semantics

2. No duplicated mapping constants across CLI/use-cases/adapters/services.
3. Dry-run write safety is dual-enforced:

* app policy gate
* Jellyfin adapter gate

---

## 10) Imaging Boundary Contract (Hard)

1. Domain owns scale/policy decisions.
2. App owns normalization orchestration.
3. Pillow-specific transforms/encoding live only in imaging adapter.
4. Domain must not import Pillow/requests/filesystem modules.

---

## 11) Observability and State Contract

1. Replace module-global mutable runtime state with explicit `RunContext`.
2. Keep user-visible run summary outputs behavior-compatible.
3. Add characterization tests for run summary/log shape with normalized run_id/time.

---

## 12) Structure Validation Checklist (Gate)

1. Fail if any `src/` file exceeds **300 LOC**.
2. Fail if non-CLI modules use `sys.exit` or `SystemExit`.
3. Fail if domain imports adapters/framework/IO.
4. Fail if invariant mappings are duplicated outside `domain/model`.
5. Fail if dry-run dual write-gate tests fail.
6. Fail if backdrop transaction/recovery parity tests fail.

---

## 13) Migration Pattern (Strangler Routing, Hard)

1. Use strangler routing explicitly.
2. CLI can route per command/mode to:

* legacy v0 path
* new v1 use-case path

3. Remove shims only after parity matrix is green for that route.

### Strangler Route Fence Table (Required)

| command | mode | route(v0\|v1) | owner slice | parity status |
| --- | --- | --- | --- | --- |
| run | logo | v0 | WI-00X | pending |
| run | thumb | v0 | WI-00X | pending |
| run | backdrop | v0 | WI-00X | pending |
| run | profile | v0 | WI-00X | pending |
| restore | logo\|thumb\|backdrop\|profile | v0 | WI-00X | pending |
| test_connection | n/a | v0 | WI-00X | pending |
| config_init | n/a | v0 | WI-00X | pending |
| config_validate | n/a | v0 | WI-00X | pending |

Route flips from `v0` to `v1` only when that row's parity tests are green.

---

## 14) Parity Source-of-Truth Rule (Hard)

1. If docs/tests/runtime disagree, **characterization-observed behavior wins** for Track 1.
2. Such rows are marked `suspicious` in parity matrix.
3. `suspicious` behavior is still preserved unless explicitly approved as a break.

---

## 15) Migration Map Outline (Track 1)

Preserved and updated to reflect Track 1 constraints:

1. `cli.py` → `cli/` + compatibility parser shim (preserve flag surface).
2. `pipeline.py` → `app/use_cases/` + `app/mode_processors/` + `app/services/`.
3. `client.py` → `adapters/jellyfin/` (HTTP transport + gateway).
4. `config.py` → `adapters/config/` + app config resolution (compatibility preserved).
5. `imaging.py` → domain scale policies + `adapters/imaging/pillow_engine.py`.
6. `backup.py` → `adapters/backup/` + restore use-case logic.
7. `discovery.py` → `app/services/discovery_*` + gateway queries (preserve filter/pagination via characterization).
8. `state.py` + `logging_utils.py` → `app/context.py` + observability sinks (no module globals).
9. `constants.py` → consolidated ownership via `domain/model` and/or focused constant modules, with single authoritative mapping ownership.

---

## 16) Behavior Preservation Plan

### Characterization suites

* `tests/characterization/cli_contract/`
* `tests/characterization/config_contract/`
* `tests/characterization/workflows/`
* `tests/characterization/restore_contract/`
* `tests/characterization/observability/`

### Imaging golden suite

* Deterministic harness
* Fixed corpus
* Deterministic encoder settings and metadata normalization
* Strict assertions on dimensions/mode/format
* Tolerant pixel diff where lossy codecs apply

*(v1 also mentioned a possible layout: `tests/golden/imaging/cases/`, `tests/golden/imaging/expected/`, `tests/golden/test_imaging_golden.py` — preserved as an optional structure.)*

### Parity matrix artifact

* `project/parity-matrix.md` with:

  * behavior id
  * status: `preserved/changed/removed/suspicious`
  * owning tests
  * notes
  * migration note link (where applicable)

### Parity row schema (required)

Each parity row must include:

* `behavior_id`
* `baseline_source`
* `current_result`
* `status`
* `owner_test`
* `approval_ref` (required when status is changed/removed or otherwise intentionally different)

### Non-determinism stabilization

* Fixed clock/run IDs in tests
* Patched sleep/retries (`time.sleep`)
* Deterministic ordering for discovery/item lists (stable sort where needed)
* Normalized metadata for codec comparisons

### Stable observability outputs to snapshot

* Final summary counters
* Presence/absence of warning/error classes
* Failure list shape/content (normalized IDs/timestamps)
* Deterministic ordering rules

### Gate intended breaks

* Track 1: breaks are not expected; if one is necessary, it must be explicitly approved and recorded (parity row + migration note + test updates).

---

## 17) Verification and Slice Policy (Strict)

1. One objective per slice.
2. ≤150 net `src/` LOC unless justified.
3. Independent verification must finish in <10 minutes.
4. If verification exceeds 10 minutes, split the slice first.
5. Every slice includes explicit rollback.
6. Full-suite runs are gate checks, not default per-slice checks.
7. No “while I'm here” edits.

### Iterative planning rule for subsequent slices (preserved from v1)

1. After each slice, update coupling snapshot and parity matrix deltas.
2. Pick the next slice that removes one hotspot edge (e.g., `cli -> pipeline`, `pipeline -> state`) with minimal blast radius.
3. If any slice changes observable behavior unexpectedly, stop and add characterization coverage before proceeding.

---

## 18) Initial Slice Set (First 5)

1. Governance scaffolding (`WORK_ITEMS.md`, `/plans` templates, PR template).
2. Parity matrix skeleton + behavior IDs.
3. CLI/config characterization harness.
4. Imaging golden harness.
5. Architecture guard tests (import boundaries + no non-entry exits).
6. Dry-run/write-gate + restore-safety contracts

Each slice must define:

* objective
* verification commands (<10 minutes)
* rollback steps

---

## 19) Governance and Anti-Drift

1. CI defines and runs the verification contract (inside workflow or a repo contract file). 
   - Verification contract is defined in CI workflow file(s) and/or project/verification-contract.yml.
2. If the verification contract changes (CI workflow and/or a repo verification contract file), CI must be updated in the same PR.
3. CI enforces:
   - execution of verification commands
   - file-size guard (>300 LOC in `src/`)
   - required test jobs on pull requests
4. AGENTS.md is a local operational guide and does not participate in CI drift validation.
5. Python version consistency checks across docs/CI/metadata (preserved from v1/v2).
6. `src/` file-size guard fails on >300 LOC.
7. New test file >300 LOC triggers split review (non-blocking).

### WORK_ITEMS.md + /plans templates (preserved)

Create `WORK_ITEMS.md` with only:

* `WI-001` Governance + anti-drift checks
* `WI-002` Parity matrix + behavior inventory
* `WI-003` Imaging characterization + goldens
* `WI-004` CLI/config characterization
* `WI-005` Dry-run/write-gate + restore-safety contracts

Create `/plans/WI_TEMPLATE.md` fields:

1. Objective
2. In-scope / Out-of-scope
3. Public interfaces affected
4. Acceptance criteria
5. Verification commands (<10 min)
6. Rollback step
7. Behavior-preservation statement

### PR template requirements (preserved)

* objective/scope (single objective)
* behavior-preservation statement (Preserved vs Intended Break)
* parity IDs touched
* verification outputs (exact commands + results)
* rollback note
* docs/contract update checklist (AGENTS/README/CI/template parity)

---

## 20) Public API / Interface / Type Additions (Track 1)

1. `UseCase.execute(request) -> result`.
2. `ModeProcessor.process(asset, context) -> ProcessOutcome`.
3. Ports/interfaces:

* `JellyfinGatewayPort`
* `ImageEnginePort`
* `BackupStorePort`
* `ConfigProviderPort`
* `EventSinkPort`
* `ClockPort`

4. Typed exception model from section 8.
5. Central domain model types for mode/image invariants.

> v3/v4 explicitly prohibit a generic orchestration hub; use `bootstrap/container.py` + `bootstrap/main.py` + direct use-case calls instead.

---

## 21) Test and Acceptance Scenarios (Track 1)

1. Dry-run blocks POST/DELETE in both app layer and adapter layer.
2. Backdrop transaction parity: stage/normalize/delete/upload/finalize plus failure retention.
3. Restore parity: filename/index semantics, profile/item path handling, refusal behavior.
4. Config/CLI parity under current Track-1 public surface.
5. Observability parity for run summaries and counters.
6. Imaging parity via characterization + golden checks.
7. Route fence test: command/mode dispatch must follow declared `route(v0|v1)` in the route-fence table.
8. CI contract test: if verification workflow or verification contract file changes, CI must be updated in the same PR.
9. Parity schema test: parity rows fail validation when required fields are missing.

---

## 22) Acceptance Criteria (Track 1 Done)

1. No `src/` file >300 LOC.
2. No overlapping responsibilities across CLI/app/domain/adapters (single ownership boundaries).
3. No global mutable runtime state in execution path.
4. Dry-run dual gate proven by tests.
5. Backdrop/restore/imaging behavior parity is green and test-backed.
6. Parity matrix complete with `preserved/changed/removed/suspicious`.
7. Track 1 CLI/config public behavior remains compatibility-equivalent.
8. Slice-level verification discipline is enforced in PRs and CI.

---

## 23) LOC Policy Clarification

1. Above >300 LOC blocker applies to `src/` in Track 1.
2. Existing oversized test files are allowed temporarily.
3. Any **new** test file >300 LOC triggers non-blocking split review.

---

## 24) Risk Register (Top 5) and Mitigations (Preserved from v1)

1. Hidden behavior regressions in `pipeline.py` monolith

   * Mitigation: characterization-first before extraction.
2. Dry-run safety leak during adapter migration

   * Mitigation: dual gate tests at use-case + gateway layers.
3. Backdrop ordering/recovery regressions

   * Mitigation: transaction-state tests + deterministic index assertions.
4. Config precedence drift during config refactor

   * Mitigation: source-tracked effective config tests and characterization.
5. Overgrowth from rewrite scaffolding

   * Mitigation: per-slice LOC budget + boundary guard checks + no-monolith contracts.

---

## 25) Rollback Strategy (Preserved and aligned with strangler routing)

1. Keep compatibility fence so routing can fall back to v0 path during migration.
2. Revert slice-by-slice (no multi-objective commits).
3. Block release cleanup until parity matrix and full gates are green.
4. If write-path regression is detected, disable write-enabled mode and retain backups/staging for recovery analysis.

---

## 26) Assumptions and Defaults

1. Option C remains default.
2. Track 1 is behavior-preserving by default.
3. Python baseline change is deferred to Track 2.
4. Interface-breaking CLI/config changes are deferred to Track 2.
5. Unrelated worktree deletions in `project/v1-checklist.md` and `project/v1-project-plan.md` are treated as out-of-scope.

## 27) Addendum
Slice 6 (WI-005) is adopted from WORK_ITEMS as a Track 1 prerequisite before strangler route flips.