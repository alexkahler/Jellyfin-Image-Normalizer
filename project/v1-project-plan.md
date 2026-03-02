# JFIN v1.0 Big-Bang Overhaul & Implementation Blueprint (Merged)

## 1. High-Level Summary

1. Execute a **big-bang rewrite** on a dedicated `v1` branch (no incremental compatibility phase).
2. Replace the current function-heavy architecture with a **hexagonal OOP design**:

   * explicit domain models, ports, and adapters
   * strict composition root and no global mutable runtime state
3. Introduce and enforce key safety invariants and policies:

   * `WritePolicy` (all writes gated)
   * `RestoreSafetyPolicy`
   * `BackdropReplacementTransaction` for backdrop flows
4. Keep behavior **Docker-ready without introducing Docker artifacts**, via a strict filesystem/runtime contract and env-overridable config.
5. Ship as a **breaking `v1.0.0`**: new subcommand-based CLI, normalized config schema, strongly-typed domain objects, and stable exit-code contract.
6. Replace the entire test suite with architecture-aligned **unit, contract, workflow, CLI, and golden tests**, plus behavior parity checks.
7. Gate deletion of legacy modules behind:

   * a **behavior parity matrix**
   * migration docs
   * and all **acceptance gates** being green.
8. Maintainability:

   * pyproject-first tooling
   * strict “no file > 500 LOC” rule as a release blocker
   * advisory size/complexity guidelines for files/classes/functions.

---

## 2. Public API / Interface Changes

### 2.1 CLI Surface (Breaking)

1. CLI changes to **subcommands** (no more flat action flags):

   * `jfin run`
   * `jfin restore`
   * `jfin test-connection`
   * `jfin config init`
   * `jfin config validate`

2. Keep `python -m jfin` as a **thin entrypoint** that delegates to the bootstrap/composition root.

3. Replace ambiguous flag combinations with **command-specific options** and strict parser validation / exclusivity rules.

### 2.2 Stable Exit Code Contract

Stable exit codes are:

1. `0` – success
2. `1` – validation/config error
3. `2` – connectivity/auth error
4. `3` – partial failures (command completed but at least one target ended in terminal processing error)
5. `4` – fatal unhandled error (takes precedence over other exit types)
6. `5` – restore refused by safety policy

### 2.3 Config Schema & Precedence

1. Move to **schema-first TOML** with clear sections:

   * `[server]`
   * `[runtime]`
   * `[discovery]`
   * `[logging]`
   * `[modes.logo]`, `[modes.thumb]`, `[modes.backdrop]`, `[modes.profile]`

2. Environment override contract for Docker readiness, e.g.:

   * `JFIN_SERVER_URL`
   * `JFIN_API_KEY`
   * plus other server/runtime overrides.

3. Config precedence is **fixed and enforced**:

   * CLI flags > environment variables > TOML.

4. `jfin config validate` must:

   * perform **schema and semantic checks**
   * **print the resolved effective configuration** including the **source per key**
   * redact sensitive fields where appropriate.

### 2.4 Python Runtime Baseline

* Python support is **`3.13+` only** in docs, packaging metadata, and CI (earlier `3.10` mentions from earlier drafts are superseded).

---

## 3. Target Architecture & Module Layout

### 3.1 Top-Level Package Layout

Create the following packages under `src/jfin/`:

1. `src/jfin/__main__.py`

   * Thin entrypoint that calls the bootstrap runner.

2. `src/jfin/bootstrap/`

   * Single **composition root**, dependency wiring only, no business logic.
   * Main entrypoint: `bootstrap/runner.py`.

3. `src/jfin/cli/`

   * `app.py`, `parser.py`
   * `commands/`

     * `base.py`
     * `run.py`
     * `restore.py`
     * `test_connection.py`
     * `config_init.py`
     * `config_validate.py`
   * Responsibilities:

     * parse subcommands and options
     * construct request DTOs
     * call bootstrap with the appropriate use-case
     * map results/errors to **exit codes**

4. `src/jfin/app/`

   * `context.py` (holds `RunContext`)
   * `dto.py` (CLI/app DTOs)
   * `use_cases/`

     * `run_batch.py`
     * `run_single_item.py`
     * `run_single_profile.py`
     * `restore_all.py`
     * `restore_single.py`
     * `test_connection.py`
     * plus consolidated `run`, `restore`, `test_connection`, `config_init`, `config_validate` use-case classes matching the CLI contract
   * `services/`

     * orchestration helpers such as:

       * normalization coordinator
       * backup/upload coordinator
       * discovery processor
       * result aggregator
       * transaction recovery handling

5. `src/jfin/domain/`

   * `enums.py`
   * `entities.py`
   * `value_objects.py`
   * `policies/`

     * `scale_policy.py`
     * `backup_policy.py`
     * `safety_policy.py`
     * domain policy implementations:

       * `WritePolicy`
       * `RestoreSafetyPolicy`
       * `RateLimitPolicy`
   * `services/`

     * `image_normalizer.py`
     * `backdrop_workflow.py` (will be aligned with `BackdropReplacementTransaction`)
   * `ports.py`

     * port interfaces, including:

       * `JellyfinGatewayPort`
       * `ImageEnginePort`
       * `BackupStorePort`
       * `ConfigProviderPort`
       * `EventSinkPort`
       * `ClockPort`

6. `src/jfin/adapters/`

   * `jellyfin/`

     * `http_transport.py`
     * `jellyfin_gateway.py` (enforces write gate at adapter layer)
   * `imaging/`

     * `pillow_image_engine.py`
   * `backup/`

     * `filesystem_backup_store.py` (including manifest writing)
   * `config/`

     * `toml_loader.py`
     * `env_overrides.py`
     * `schema.py`
   * `logging/`

     * `logger_factory.py`
   * Additional event sink adapters:

     * `LoggingEventSink`
     * `MetricsEventSink`
     * optional `JsonlEventSink`

7. `src/jfin/observability/`

   * `metrics.py`
   * `events.py`
   * typed events and metrics accumulator, no module globals.

8. `src/jfin/shared/`

   * `errors.py` (error taxonomy)
   * `types.py` (typing utilities)

### 3.2 Legacy Modules to Move (After Parity Gate)

After the parity matrix and migration docs are complete and all gates are green, move the below files to `v0` folder:

1. `src/jfin/cli.py`
2. `src/jfin/pipeline.py`
3. `src/jfin/client.py`
4. `src/jfin/config.py`
5. `src/jfin/state.py`
6. `src/jfin/imaging.py`
7. `src/jfin/backup.py`
8. `src/jfin/discovery.py`
9. `src/jfin/logging_utils.py`
10. Any remaining monolithic legacy modules not aligned with the new structure.

---

## 4. Responsibility Boundaries & OOP/SOLID Model

### 4.1 Architectural Boundaries

1. `domain` **owns business rules only**; no imports from HTTP, filesystem, CLI, or framework modules.
2. `app/use_cases` orchestrate workflows, depending only on **domain ports/interfaces**.
3. `app/services` contain reusable orchestration logic (normalization, backup/upload, discovery, result aggregation).
4. `adapters` implement ports for:

   * Jellyfin API
   * image processing (Pillow)
   * backup storage
   * config provider (TOML + env + CLI)
   * event sinks / logging
5. `cli`:

   * maps CLI arguments to DTOs
   * invokes bootstrap runner
   * maps results to **exit codes** and human-readable messages.
6. `bootstrap`:

   * is the **single composition root** for wiring adapters and ports
   * CLI may not instantiate adapters directly.
7. `observability` captures run metrics/events **without global state**.
8. `shared` holds cross-cutting error types and type aliases, but **no business logic**.

### 4.2 Composition Root Rules

1. Entrypoint for wiring: `bootstrap/runner.py`.
2. Runner flow:

   1. Load config (TOML)
   2. Apply environment overrides
   3. Apply CLI override precedence
   4. Validate resulting config
   5. Build adapters
   6. Build `RunContext`
   7. Execute the requested use-case.
3. CLI must call **only one** bootstrap function for each command.
4. Use-cases depend only on ports/interfaces; **no adapter imports** outside `bootstrap/`.

### 4.3 OOP/SOLID Enforcement

1. **Abstraction**

   * All external integrations sit behind typed ports in `domain/ports.py`.

2. **Encapsulation**

   * Entities/value objects validate invariants at construction:

     * `ModeSettings`
     * `ScalePlan`
     * `RunRequest`
     * `DiscoveredAsset`
     * `ProcessOutcome`
     * `ProcessResult`
     * `RestoreResult`

3. **Inheritance**

   * `BaseCommand` and `BaseModeProcessor` abstract shared command/processor behavior.

4. **Polymorphism**

   * `LogoProcessor`, `ThumbProcessor`, `BackdropProcessor`, `ProfileProcessor` implement a common `ModeProcessor` interface.

5. **SOLID Principles**

   1. **S**: one use-case class per workflow (`run`, `restore`, etc.).
   2. **O**: new mode added by new processor + registry entry, without rewriting workflows.
   3. **L**: processors substitutable through interface contracts.
   4. **I**: narrow ports (`ImageReadPort`, `ImageWritePort`, `DiscoveryPort`, `BackupPort`, etc.).
   5. **D**: use-cases depend on ports; adapters are injected at the composition root.

---

## 5. Domain Modeling, Ports, and Policies

### 5.1 Core Domain Types

Implement domain types with constructor validation:

1. `ModeSettings`
2. `ScalePlan`
3. `RunRequest`
4. `DiscoveredAsset`
5. `ProcessOutcome`
6. `ProcessResult`
7. `RestoreResult`
8. Domain enums for modes, scale behaviors, logo padding modes, etc.

Error taxonomy:

1. `ValidationError`
2. `ConnectivityError`
3. `PolicyRefusal`
4. `ProcessingError`
5. `FatalError`

### 5.2 Ports

Define interfaces for:

1. `JellyfinGatewayPort`
2. `ImageEnginePort`
3. `BackupStorePort`
4. `ConfigProviderPort`
5. `EventSinkPort`
6. `ClockPort`

   * **Only** `ClockPort` may read time / sleep; no direct `time.sleep` outside its adapter.

### 5.3 Policies & Services

Policies:

1. `WritePolicy`

   * mandatory and authoritative for all write actions
   * enforced at:

     * app-service boundary, and
     * inside `JellyfinGateway` adapter (dual enforcement fail-safe).
   * dry-run invariant: **no POST/DELETE** may execute in dry-run mode.

2. `RestoreSafetyPolicy`

   * enforces:

     * risky restore operations require explicit force override
     * fingerprint checks vs server/manifest
     * refusal behavior on mismatch unless `--i-know-what-im-doing`.

3. `RateLimitPolicy`

   * controls inter-request throttle and backoff behavior
   * uses `ClockPort` for sleeping/time reads
   * deterministic in tests via fake clock.

Domain services:

1. Image scaling/padding/normalization (consistent with existing semantics).
2. Backdrop workflow logic (aligned with `BackdropReplacementTransaction` state machine).
3. Backup policy logic for modes and restore operations.
4. Safety policy helpers to evaluate restore/write decisions.

---

## 6. Safety Policies, Backdrop Transactions & Restore Rules

### 6.1 Safety Invariants

1. `WritePolicy` enforced at:

   * app-service boundary
   * `JellyfinGateway` adapter.
2. Dry-run invariant:

   * **no POST/DELETE** when dry-run is active.
3. Restore safety invariants:

   * risky restore operations require explicit force flag
   * unknown/malformed transaction or manifest state **never auto-continues**.
4. Unknown transaction state:

   * default is **refuse** with an actionable message.

### 6.2 Backdrop Transaction Model

1. New transaction service: `BackdropReplacementTransaction`.
2. States:

   * `STAGED`
   * `NORMALIZED`
   * `DELETED`
   * `UPLOADED`
   * `FINALIZED`
   * `FAILED`
3. Persistent record file:

   * `backup_root/staging/<item_id>/transaction.json`
4. Required fields in `transaction.json`:

   * `schema_version`
   * `jfin_version`
   * `created_at`
   * `updated_at`
   * `server_fingerprint`
   * `item_id`
   * `expected_backdrop_count`
   * `uploaded_indices`
   * `current_state`
   * `last_error`
5. Startup behavior for incomplete transactions:

   * **Refuse by default**, with a clear remediation message.
6. Recovery commands:

   * `--resume`: resumes valid transaction; skips already uploaded indices unless forced.
   * `--cleanup-staging`: removes staging directories and transaction records explicitly.
7. Schema handling:

   * Unknown `schema_version` or missing critical fields ⇒ refusal, **no fallback**.

### 6.3 Backdrop Lifecycle & Safety

* Backdrop phase flow must include:

  1. `stage`
  2. `normalize`
  3. `delete`
  4. `upload`
  5. `finalize`
* Partial failure retention:

  * ensure that in cases of failure, backups and staging remain recoverable.
* Interruption detection:

  * detect crash/interrupt and refuse to proceed until user resolves with `--resume` or `--cleanup-staging`.

### 6.4 Restore Rules and Force Flag

1. `RestoreSafetyPolicy` must:

   * inspect manifests and fingerprints
   * refuse restoring when fingerprints mismatch, unless forced.
2. Force override:

   * flag name is **exactly** `--i-know-what-im-doing`.
   * required for:

     * `restore-all`
     * any restore that overrides fingerprint mismatches.
3. Risky restores:

   * require explicit consent via the force flag.

---

## 7. Filesystem & Docker-Ready Runtime Contract

### 7.1 Filesystem Contract

1. Backup root is **configurable** and normalized to an absolute path at runtime.
2. Staging path is always under backup root:

   * e.g. `backup_root/staging/…`
   * must survive container restarts.
3. Startup preflight must:

   * verify backup root existence or create it
   * verify write permissions (fail early with clear error if not writable).
4. No temporary state outside the configured backup root (except process-local memory).
5. Run manifest location:

   * `backup_root/run_<run_id>/manifest.json`.

### 7.2 Docker-Ready Behavior (Without Docker Artifacts)

1. **No** Dockerfile/compose changes as part of this overhaul.
2. Runtime behavior must be container-ready:

   * no hardcoded absolute paths
   * config is env-overridable
   * logging goes to stdout/stderr
   * deterministic, non-interactive CLI behavior
   * stateless processing except for the configured backup path.
3. Documentation must include a **container runtime contract** and required env vars.

---

## 8. Config Resolution & Schema Details

1. Config sources:

   * TOML files
   * Environment variables
   * CLI overrides
2. Precedence:

   * **CLI > env > TOML** (fixed contract).
3. `config validate`:

   * prints the **effective config**, including source (TOML/env/CLI) per key
   * redacts sensitive values (e.g. API key)
   * performs **semantic validation**:

     * mode rules
     * backup root writability
     * restore safety configuration
     * logo padding behavior and NO_SCALE semantics.
4. Config provider implementation:

   * TOML loader + env overlay + CLI overlay with source tracking.
5. Python runtime baseline:

   * documented as `3.13+` consistently across README, packaging, CI, and migration guides.

---

## 9. CLI Contract

1. Subcommands:

   * `run`
   * `restore`
   * `test-connection`
   * `config init`
   * `config validate`

2. Parser rules:

   * strict argument exclusivity and unambiguous combinations
   * command-specific flags and options only.

3. Exit code mapping:

   * map errors/results to stable exit codes with clear precedence (`fatal` → `4` wins).

4. Restore-specific behavior:

   * risky operations require `--i-know-what-im-doing`.

5. Operator-facing behavior:

   * refusal messages must always include **reason + remediation command** (e.g. “run with `--resume`” or “run with `--i-know-what-im-doing`”).

---

## 10. Observability: Events & Metrics

### 10.1 Typed Events

Implement events such as:

1. `RunStarted`
2. `DiscoveryFinished`
3. `ImagePlanned`
4. `BackupWritten`
5. `UploadAttempted`
6. `UploadFailed`
7. `RestoreRefused`
8. `RunFinished`

### 10.2 Metrics & Event Sinks

1. Metrics accumulator:

   * tracks counts for success/skip/warning/error, etc.
   * ensures **run metrics parity** with previous behavior.
2. Event sinks:

   * `LoggingEventSink` (logs events)
   * `MetricsEventSink` (updates counters/aggregates)
   * optional `JsonlEventSink` (append-only structured logging).
3. No module-global state:

   * sinks and metrics are tied to `RunContext` and injected, not imported as globals.

---

## 11. Backup Metadata & Manifests

1. Run manifest:

   * Path: `backup_root/run_<run_id>/manifest.json`.

2. Manifest fields include:

   * server fingerprint
   * JFIN version
   * timestamps
   * item/image decisions
   * original/normalized dimensions
   * content types
   * processing mode
   * outcome status (`ProcessOutcome`).

3. Restore logic:

   * reads manifest for fingerprint and decision context
   * applies `RestoreSafetyPolicy` before performing restore actions.

---

## 12. Test Strategy (Full Rewrite)

### 12.1 Test Layout

1. `tests/unit/domain/`

   * policies, entities, value objects.
2. `tests/unit/app/`

   * use-case orchestration with mocked ports.
3. `tests/unit/adapters/`

   * Jellyfin gateway
   * Pillow engine
   * filesystem backup store
   * config loader/provider.
4. `tests/contract/`

   * `PortContractSuite` per port
   * same suite runs against real adapters and fakes.
5. `tests/workflows/`

   * backdrop transaction flows (happy path, crash recovery, refusal paths)
   * restore workflows
   * run/test-connection flows.
6. `tests/cli/`

   * subcommand parse/validation
   * config/precedence behavior
   * exit-code mapping and refusal messaging.
7. `tests/golden/`

   * curated image corpus:

     * palette behavior
     * alpha handling
     * EXIF
     * padding/crop behaviors
   * deterministic comparison harness:

     * fixed encoder params where possible
     * metadata normalization/stripping
     * tolerant pixel diff but strict size/mode/format assertions.

### 12.2 Mandatory Scenario Coverage

From all versions, the mandatory scenarios include:

1. Dry-run:

   * blocks all POST/DELETE both in service layer and at the `JellyfinGateway` adapter.
2. Backdrop lifecycle:

   * full lifecycle (`stage` → `normalize` → `delete` → `upload` → `finalize`)
   * partial-failure retention behavior.
3. Backdrop interruption:

   * detection of incomplete transactions
   * default refusal on next run
   * `--resume` behavior skipping already uploaded indices unless forced.
4. Staging cleanup:

   * `--cleanup-staging` removes staging and updates events/metrics correctly.
5. Scaling behaviors:

   * `NO_SCALE` mode with and without forced upload (`force_upload_noscale`).
6. Logo padding:

   * `add`, `remove`, `none` plus sensitivity edge cases.
7. Restore behaviors:

   * restore single/all
   * invalid backup index patterns
   * fingerprint mismatch refusal and force override via `--i-know-what-im-doing`.
8. Config:

   * precedence (CLI > env > TOML)
   * redaction behavior
   * semantic validation errors.
9. CLI:

   * invalid flag combinations
   * deterministic exit codes
   * refusal remediation text.
10. Metrics and events:

* run metrics/event accounting parity for v0 counter semantics, plus v1 outcome-model contracts (`V1-OBS-001`, `V1-OBS-002`) and migration delta coverage (`DELTA-OBS-001`).

11. Golden tests:

* no spurious breakages in image outputs
* documented “update goldens” workflow.

12. Unknown/invalid transaction schema/state:

* always refused by default, with actionable messaging.

### 12.3 Test Quality Targets

1. All old tests are replaced; no dependency on legacy global state patterns.
2. Deterministic fixtures/builders for:

   * images
   * Jellyfin payloads
   * config scenarios.
3. Strong type coverage for tests (mypy-clean tests if enabled).
4. Contract suites and golden tests are **mandatory** in CI for v1.0 branch merges.

---

## 13. CI, Quality Gates & Maintainability

### 13.1 CI Jobs

1. `ruff format --check`
2. `ruff check`
3. `mypy src`
4. `pytest`
5. `bandit -r src`
6. `pip-audit`

CI Python versions:

* `3.13`
* latest stable Python

(older matrix entries with `3.10` are superseded).

### 13.2 Code Size / Complexity Policy

1. CI will generate advisory reports for:

   * file size
   * class size
   * function complexity.
2. Target guidelines:

   * file target ≤ **250 LOC**
   * class target ≤ **150 LOC**
   * function target ≤ **40 LOC**
3. Flexible exceptions allowed with documented rationale.
4. Hard red-flag threshold:

   * any file **> 500 LOC** is **release-blocking** by acceptance policy.
5. Maintainability reports are **advisory in CI**, but the >500 LOC rule is enforced by review/acceptance.

---

## 14. Execution Plan

### 14.1 High-Level Workstreams (Conceptual)

1. Foundation and tooling (`pyproject.toml`, CI jobs, baseline Python).
2. Domain modeling (types, policies, error taxonomy).
3. Port contracts (interfaces for discovery/image I/O/backup/events).
4. Adapter implementations (Jellyfin, Pillow, backup filesystem, config provider, logging).
5. Application use-cases and app services.
6. CLI rewrite with subcommands and exit-code mapping.
7. Test suite rewrite (unit, contract, workflow, CLI, golden).
8. Delete legacy structure after parity and migration gates; release `v1.0.0`.

### 14.2 Suggested Detailed Execution Sequence (PR Slices)

**PR1: Foundation + Tooling + Boundaries**

1. Add `pyproject.toml` for deps/tools (`ruff`, `mypy`, `pytest`, `bandit`, `pip-audit`).
2. Update CI to run required jobs on Python `3.13` + latest stable.
3. Add architecture import-boundary tests.
4. Add package scaffolding directories/files.
5. Add minimal `bootstrap/runner.py` and subcommand stubs returning `NotImplemented` with exit code `1`.

**PR2: Domain Contracts First**

1. Implement domain types with constructor validation:

   * `ModeSettings`, `ScalePlan`, `RunRequest`, `DiscoveredAsset`, `ProcessOutcome`, `ProcessResult`, `RestoreResult`.
2. Implement error taxonomy (`ValidationError`, `ConnectivityError`, `PolicyRefusal`, `ProcessingError`, `FatalError`).
3. Define ports (`JellyfinGatewayPort`, `ImageEnginePort`, `BackupStorePort`, `ConfigProviderPort`, `EventSinkPort`, `ClockPort`).
4. Define policies (`WritePolicy`, `RestoreSafetyPolicy`, `RateLimitPolicy`).
5. Add port contract skeleton tests in `tests/contract`.

**PR3: Observability + RunContext**

1. Implement typed events:

   * `RunStarted`, `DiscoveryFinished`, `ImagePlanned`, `BackupWritten`, `UploadAttempted`, `UploadFailed`, `RestoreRefused`, `RunFinished`.
2. Implement `RunContext` and metrics accumulator.
3. Implement event sink adapters (`LoggingEventSink`, `MetricsEventSink`, optional `JsonlEventSink`).
4. Add metrics parity tests for `OBS-001` v0 semantics and v1 outcome-model contracts (`V1-OBS-001`, `V1-OBS-002`) with `DELTA-OBS-001` coverage.

**PR4: Config Provider + Filesystem Contract**

1. Implement TOML loader + env overlay + CLI overlay with source tracking.
2. Implement **redacted** effective-config output for `config validate`.
3. Add semantic validators for:

   * modes,
   * restore safety settings,
   * backup path and writability.
4. Implement startup filesystem preflight:

   * absolute backup root normalization
   * create-if-missing
   * writability check.
5. Add tests for precedence and redaction behavior.

**PR5: Adapters (Transport/Gateway/Image/Backup)**

1. Implement HTTP transport with retry behavior for transient network/5xx failures.
2. Implement Jellyfin gateway adapter with:

   * clear mapping from port operations to HTTP calls
   * **write-gate enforcement** via `WritePolicy`.
3. Implement Pillow image engine adapter preserving current behavior semantics.
4. Implement filesystem backup store + run manifest writer.
5. Add adapter contract tests against real adapters and fakes.

**PR6: App Services + Use Cases**

1. Implement reusable `app/services`:

   * normalization coordinator
   * backup/upload coordinator
   * discovery processor
   * result aggregator.
2. Implement use-cases:

   * `run`
   * `restore`
   * `test_connection`
   * `config_init`
   * `config_validate`
3. Enforce `WritePolicy` at service boundary (completing dual enforcement with adapter).
4. Add workflow tests for run/restore/test flows.

**PR7: Backdrop Transaction + Restore Safety**

1. Implement `BackdropReplacementTransaction` state machine.
2. Persist `transaction.json` under `backup_root/staging/<item_id>/`.
3. Enforce required schema fields and schema-version refusal behavior.
4. Implement startup detection and default refusal for incomplete transactions.
5. Implement `--resume` and `--cleanup-staging`.
6. Implement `RestoreSafetyPolicy` fingerprint checks and `--i-know-what-im-doing` handling.
7. Add full crash/recovery/idempotency tests including `uploaded_indices`.

**PR8: CLI Finalization + Exit Contract**

1. Build final subcommand parser and strict exclusivity rules.
2. Map errors/results to stable exit codes with precedence (`fatal` always `4`).
3. Ensure refusal messages include reason + remediation.
4. Add CLI tests for invalid combos, refusal messaging, and deterministic exit codes.

**PR9: Golden Tests + Parity Matrix + Legacy Deletion**

1. Add curated golden corpus and deterministic comparison harness.
2. Document an “update goldens” workflow.
3. Build behavior parity matrix, mapping old behavior to:

   * preserved
   * renamed
   * or intentionally removed.
4. Update migration docs and README with Python `3.13+` consistency.
5. Delete legacy modules once parity gate is complete and CI is green.
6. Tag `v1.0.0` after all acceptance gates pass.

---

## 15. Legacy Parity, Migration & Release

1. Build a **behavior parity matrix** before removing legacy modules.

   * Map each old flag/config behavior to:

     * preserved
     * renamed
     * removed (intentional).
   * Explicitly track:

     * `force_upload_noscale`
     * dry-run write gating
     * logo padding sensitivity
     * backdrop sequencing
     * restore exclusivity.
2. Legacy files can only be deleted after:

   * parity matrix completion
   * migration docs updated
   * all CI and tests are green.
3. Release `v1.0.0` with:

   * migration guide
   * config mapping table
   * Python `3.13+` support clarified.

---

## 16. Acceptance Criteria (Definition of Done)

1. New architecture merged with hexagonal boundaries, explicit ports/adapters, and **single composition root**.
2. No global mutable runtime state remains; `RunContext` is the explicit runtime state model.
3. Import boundaries are enforced in CI.
4. `WritePolicy` dual enforcement (service + adapter) proven by tests.
5. Backdrop transaction model and recovery rules fully implemented:

   * incomplete transactions refused by default
   * resume/cleanup commands implemented and tested.
6. Restore safety policy enforced:

   * fingerprint-aware
   * force flag `--i-know-what-im-doing` required for risky operations.
7. Entire test suite (unit, contract, workflow, CLI, golden) passes.
8. No source file exceeds **500 LOC**; maintainability report is generated in CI.
9. No overlapping/conflicting module responsibilities in architecture review.
10. Parity matrix and migration docs complete before legacy deletion.
11. User docs updated for:

    * v1.0 CLI/config changes
    * Python `3.13+` requirements
    * container runtime contract.
12. `v1.0.0` tag is created only after all above gates are green.

---

## 17. Assumptions & Defaults

1. Delivery model is a **big-bang rewrite** on a dedicated branch; no long-term backward compatibility shims beyond entrypoint continuity.
2. Breaking changes are acceptable and expected for v1.0.
3. Python runtime support is **3.13+ only**.
4. Unknown transaction schemas/states **always refuse by default**.
5. Risky restore operations **require** explicit force override (`--i-know-what-im-doing`).
6. Docker artifacts (Dockerfiles/compose) are intentionally **excluded** from this cycle; only runtime behavior must be container-ready.
7. Ports/contracts are **frozen before adapter completion**; contract tests are authoritative for adapter behavior.
8. Maintainability size rules are advisory in CI but strictly enforced for the >500 LOC threshold.
