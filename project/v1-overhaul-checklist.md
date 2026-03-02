# JFIN v1.0 Big-Bang Overhaul - Complete Migration + Behavior Parity Checklist

## How to Use This Checklist
- [ ] Complete every checkbox in a phase before moving to the next phase.
- [ ] Attach evidence for each completed item: test names, CI job URL, and artifact/doc path.
- [ ] Evidence format is mandatory: ID + test name(s) + artifact/doc path(s) + implementation PR link.
- [ ] For every checkbox with an ID (for example `CLI-001`), update the matching row in `docs/behavior-parity-matrix-v1.md`.
- [ ] Parity IDs apply only to behaviors proven to exist in Phase 0 v0 baseline artifacts.
- [ ] Parity IDs (`CLI-*`, `CFG-*`, `IMG-*`, `RUN-*`, `DISC-*`, `BKP-*`, `RST-*`, `OBS-*`, `ADP-HTTP-*`) require Phase 0 baseline artifacts as evidence.
- [ ] `V1-*` contract IDs require v1 tests plus v1 artifacts (for example Phase 8 help captures) as evidence.
- [ ] `DELTA-*` IDs require migration guidance + rationale + risk documentation, plus tests covering the new behavior.
- [ ] Behaviors introduced in v1 are tracked as `V1-*` IDs and/or `DELTA-*` IDs, not as parity preservation.
- [ ] Mark every matrix row as exactly one status: `preserved`, `renamed`, `removed-intentional`, or `new-v1`.
- [ ] Do not delete or move legacy modules until all parity IDs are closed with evidence.
- [ ] Treat unchecked safety and parity-critical rule items as release blockers.

## Parity Matrix Integration Rules
- [ ] Every behavior row in `docs/behavior-parity-matrix-v1.md` has a unique ID and owner.
- [ ] Parity IDs link to implementation PRs, tests, and Phase 0 baseline artifacts.
- [ ] `new-v1` rows link to `V1-*` contract IDs plus v1 artifacts/tests.
- [ ] `removed-intentional` and `renamed` rows link to `DELTA-*` docs when behavior is user-visible.
- [ ] Every `removed-intentional` ID includes migration guidance and rationale.
- [ ] Every `new-v1` row links to corresponding `V1-*` contract IDs and any related `DELTA-*` IDs.
- [ ] Legacy deletion is blocked until all IDs are closed and reviewed.
- [ ] Release is blocked if any parity ID lacks evidence.
- [ ] Every new-v1 row links to at least one V1-* contract ID (required), and any related DELTA-* IDs (if user-visible).

## Locked Program Decisions
- [ ] Big-bang rewrite on dedicated `feat/v1-overhaul` branch.
- [ ] Breaking changes are accepted for `v1.0.0` when migration mapping is documented.
- [ ] Hexagonal architecture with explicit ports/adapters and single composition root.
- [ ] Runtime state is explicit (`RunContext`); global mutable state is forbidden.
- [ ] Subcommand CLI contract: `run`, `restore`, `test-connection`, `config init`, `config validate`.
- [ ] Dry-run safety invariant: no POST/DELETE while dry-run is active.
- [ ] `WritePolicy` is dual-enforced at app-service boundary and Jellyfin adapter boundary.
- [ ] Incomplete backdrop transactions are refused by default.
- [ ] Risky restore operations require exact force flag `--i-know-what-im-doing`.
- [ ] Python baseline is `3.13+` only across docs, packaging metadata, and CI.
- [ ] Tooling is `pyproject.toml` first.
- [ ] Dockerfile/compose changes are out of scope; Docker-ready runtime behavior is in scope.
- [ ] These are v1 requirements and are expected to differ from v0 baseline behavior.

## Non-Goals / Intentional Deltas
- [ ] Maintain `docs/v1-intentional-deltas.md` with `DELTA-*` IDs for approved behavior changes.
- [ ] Every `DELTA-*` item links old behavior, new behavior, rationale, risk, and migration guidance.
- [ ] Every intentional delta is mirrored in `docs/behavior-parity-matrix-v1.md` as `removed-intentional` or `renamed`.
- [ ] Release is blocked if any implemented behavior change is not represented by a `DELTA-*` ID.
- [ ] [DELTA-EXIT-001] Exit code taxonomy expands from v0 behavior to v1 stable mapping `0..5`.
- [ ] [DELTA-RST-001] `restore --all` equivalent requires `--i-know-what-im-doing`.
- [ ] [DELTA-RST-002] Restore flow refuses fingerprint mismatch by default unless forced.
- [ ] [DELTA-RST-003] Restore safety refusals get dedicated exit code `5`.
- [ ] [DELTA-RST-004] v1 resolves v0 `--restore-all` scope ambiguity (help text vs runtime): define whether backdrop is included in restore-all equivalent, update help/docs, and add tests covering the chosen behavior.
- [ ] [DELTA-CFG-001] v1 enforces deterministic precedence `CLI > env > TOML`.
- [ ] [DELTA-CFG-002] v1 introduces env overrides (`JFIN_SERVER_URL`, `JFIN_API_KEY`).
- [ ] [DELTA-CFG-003] v1 introduces effective-config output with per-key source metadata.
- [ ] [DELTA-OBS-001] v1 changes run summary model from v0 independent counters to exclusive per-asset outcome categorization (migration note: summary numbers may differ in edge cases).

## Mandatory Quality Gates (Run Before Phase Exit)
```bash
python -m ruff format . --check
python -m ruff check .
python -m mypy src
set PYTHONPATH=src && python -m pytest
python -m bandit -r src
python -m pip_audit
```

## v0 Parity Inventory (Must Not Lose) - ID-Tracked

### CLI Capability Inventory (v0 Baseline Behavior)
- [ ] [CLI-001] `python -m jfin` entrypoint remains thin (parses args + dispatches), with behavior captured in Phase 0.
- [ ] [CLI-002] Default processing executes with config defaults when no targeting overrides are provided.
- [ ] [CLI-003] Mode selection supports `logo`, `thumb`, `backdrop`, `profile`.
- [ ] [CLI-004] Library filtering is supported `--libraries` flag with comma or pipe-separated library names.
- [ ] [CLI-005] Item-type filtering is supported with `--item-types` with support for `movies` and `series` (pipe/comma separated).
- [ ] [CLI-006] Single-target item execution is supported for item modes with `--single`.
- [ ] [CLI-007] Single-target user execution is supported for profile mode `--single`.
- [ ] [CLI-008] Per-mode size overrides are supported with `--thumb-target-size`, `--backdrop-target-size` and `--profile-target-size`.
- [ ] [CLI-009] Per-mode quality overrides are supported with `--thumb-jpeg-quality`, `--backdrop-jpeg-quality`, and `--profile-webp-quality`.
- [ ] [CLI-010] Scale guard toggles (up/down) are supported with `--no-upscale` and `--no-downscale`.
- [ ] [CLI-011] Logo padding policy (`add`, `remove`, `none`) and sensitivity override are supported.
- [ ] [CLI-012] No-scale force upload override is supported with `--force-upload-noscale`.
- [ ] [CLI-013] Dry-run is supported (`--dry-run`).
- [ ] [CLI-014] Backup enable/disable and backup mode options are supported with `--backup`.
- [ ] [CLI-015] API delay/backoff/retry controls are supported.
- [ ] [CLI-016] Verbosity controls are supported (`--verbose`).
- [ ] [CLI-017] Mode-scoped restore is supported.
- [ ] [CLI-018] Single-target restore is supported.
- [ ] [CLI-023] Invalid argument combinations are refused with actionable messages.
- [ ] [CLI-030] `silent` mode suppresses CLI noise while file logging remains functional when enabled.
- [ ] [CLI-031] No-op warning behavior for irrelevant flags is explicit and tested when preserved.
- [ ] [CLI-032] v0 `--restore-all` flag exclusivity behavior is captured (rejects non-config/logging operational flags), snapshot-tested.
- [ ] [CLI-033] v0 `--generate-config` exclusivity behavior is captured (rejects operational flags), snapshot-tested.
- [ ] [CLI-034] Single-target mode (`--single` in v0, mapped to `run --single` in v1) treats item target as item UUID and bypasses discovery.
- [ ] [CLI-035] Single-target profile mode performs case-insensitive username matching and clear missing-user failure.
- [ ] [CLI-036] Single-target mode enforces mode/target compatibility with actionable refusals on invalid combinations.
- [ ] [CLI-037] Help/usage text is deterministic (no environment-dependent ordering), snapshot-tested.
- [ ] [CLI-038] Operator-facing summary output format is stable (or DELTA-tracked), snapshot-tested.

### Legacy CLI Flag Mapping Inventory (v0 -> v1)
- [ ] [MAP-CLI-001] Legacy `--mode` behavior mapped/documented.
- [ ] [MAP-CLI-002] Legacy `--single` behavior mapped/documented.
- [ ] [MAP-CLI-003] Legacy `--restore` behavior mapped/documented.
- [ ] [MAP-CLI-004] Legacy `--restore-all` behavior mapped/documented with migration note for new force requirement.
- [ ] [MAP-CLI-005] Legacy `--test-jf` behavior mapped to `test-connection`.
- [ ] [MAP-CLI-006] Legacy `--generate-config` behavior mapped to `config init`.
- [ ] [MAP-CLI-007] Legacy `--config` path behavior mapped/documented.
- [ ] [MAP-CLI-008] Legacy `--dry-run` behavior mapped/documented.
- [ ] [MAP-CLI-009] Legacy `--backup` behavior mapped/documented.
- [ ] [MAP-CLI-010] Legacy `--no-upscale` behavior mapped/documented.
- [ ] [MAP-CLI-011] Legacy `--no-downscale` behavior mapped/documented.
- [ ] [MAP-CLI-012] Legacy `--logo-target-size` behavior mapped/documented.
- [ ] [MAP-CLI-013] Legacy `--thumb-target-size` behavior mapped/documented.
- [ ] [MAP-CLI-014] Legacy `--backdrop-target-size` behavior mapped/documented.
- [ ] [MAP-CLI-015] Legacy `--profile-target-size` behavior mapped/documented.
- [ ] [MAP-CLI-016] Legacy `--thumb-jpeg-quality` behavior mapped/documented.
- [ ] [MAP-CLI-017] Legacy `--backdrop-jpeg-quality` behavior mapped/documented.
- [ ] [MAP-CLI-018] Legacy `--profile-webp-quality` behavior mapped/documented.
- [ ] [MAP-CLI-019] Legacy `--logo-padding` behavior mapped/documented.
- [ ] [MAP-CLI-020] Legacy `--jf-url` behavior mapped/documented.
- [ ] [MAP-CLI-021] Legacy `--jf-api-key` behavior mapped/documented.
- [ ] [MAP-CLI-022] Legacy `--libraries` behavior mapped/documented.
- [ ] [MAP-CLI-023] Legacy `--item-types` behavior mapped/documented.
- [ ] [MAP-CLI-024] Legacy `--jf-delay-ms` behavior mapped/documented.
- [ ] [MAP-CLI-025] Legacy `--force-upload-noscale` behavior mapped/documented.
- [ ] [MAP-CLI-026] Legacy `--silent` / `-s` behavior mapped/documented.
- [ ] [MAP-CLI-027] Legacy `--verbose` / `-v` behavior mapped/documented.
- [ ] [MAP-CLI-028] Every removed legacy CLI flag is marked `removed-intentional` with migration note.

### Config Key + Validation Inventory (v0 Baseline Behavior)
- [ ] [CFG-003] Sensitive values are redacted in outputs/logs.
- [ ] [CFG-006] Server URL is validated for presence/type and produces actionable errors when missing/invalid (baseline-captured).
- [ ] [CFG-007] API key missing/empty is validation error when required by command.
- [ ] [CFG-008] TLS verify and timeout controls are supported and validated.
- [ ] [CFG-009] Runtime retries/backoff/delay settings are validated.
- [ ] [CFG-010] Dry-run config key behavior is preserved.
- [ ] [CFG-011] Backup enable/mode/path keys are preserved or migration-mapped.
- [ ] [CFG-012] Logging config keys are preserved or migration-mapped.
- [ ] [CFG-013] Discovery library/item-type keys are preserved or migration-mapped.
- [ ] [CFG-014] Mode dimension and quality keys are preserved or migration-mapped.
- [ ] [CFG-015] Logo padding and sensitivity keys are preserved or migration-mapped.
- [ ] [CFG-016] Unknown enum values are rejected with readable errors.
- [ ] [CFG-017] Invalid ranges are rejected (dimensions, quality, sensitivity).
- [ ] [CFG-018] Missing required settings fail with actionable messages.
- [ ] [CFG-019] Legacy key mapping table is complete for all v0 keys.
- [ ] [CFG-020] Any intentionally removed key has migration note and parity status.
- [ ] [CFG-021] Generated config is safe-by-default (dry-run enabled) or documented intentional delta.
- [ ] [CFG-022] `fail_fast` semantics (or v1 equivalent) are preserved/mapped and parity-tested.
- [ ] [CFG-023] Target-size parsing preserves one-side-missing aspect-ratio inference (if kept) with minimum 1px clamp.

### Legacy Config Key Mapping Inventory (v0 -> v1)
- [ ] [MAP-CFG-001] `[server].jf_url` mapped/documented.
- [ ] [MAP-CFG-002] `[server].jf_api_key` mapped/documented.
- [ ] [MAP-CFG-003] `[api].verify_tls` mapped/documented.
- [ ] [MAP-CFG-004] `[api].timeout` mapped/documented.
- [ ] [MAP-CFG-005] `[api].jf_delay_ms` mapped/documented.
- [ ] [MAP-CFG-006] `[api].api_retry_count` mapped/documented.
- [ ] [MAP-CFG-007] `[api].api_retry_backoff_ms` mapped/documented.
- [ ] [MAP-CFG-008] `[api].fail_fast` mapped/documented.
- [ ] [MAP-CFG-009] `[api].dry_run` mapped/documented.
- [ ] [MAP-CFG-010] `[backup].backup` mapped/documented.
- [ ] [MAP-CFG-011] `[backup].backup_mode` mapped/documented.
- [ ] [MAP-CFG-012] `[backup].backup_dir` mapped/documented.
- [ ] [MAP-CFG-013] `[backup].force_upload_noscale` mapped/documented.
- [ ] [MAP-CFG-014] `[modes].operations` mapped/documented.
- [ ] [MAP-CFG-015] `[modes].item_types` mapped/documented.
- [ ] [MAP-CFG-016] `[libraries].names` mapped/documented.
- [ ] [MAP-CFG-017] `[logging].file_path` mapped/documented.
- [ ] [MAP-CFG-018] `[logging].file_enabled` mapped/documented.
- [ ] [MAP-CFG-019] `[logging].file_level` mapped/documented.
- [ ] [MAP-CFG-020] `[logging].cli_level` mapped/documented.
- [ ] [MAP-CFG-021] `[logging].silent` mapped/documented.
- [ ] [MAP-CFG-022] `[logo].width` and `[logo].height` mapped/documented.
- [ ] [MAP-CFG-023] `[logo].no_upscale` and `[logo].no_downscale` mapped/documented.
- [ ] [MAP-CFG-024] `[logo].padding` mapped/documented.
- [ ] [MAP-CFG-025] `[logo].padding_remove_sensitivity` mapped/documented.
- [ ] [MAP-CFG-026] `[thumb].width` and `[thumb].height` mapped/documented.
- [ ] [MAP-CFG-027] `[thumb].no_upscale` and `[thumb].no_downscale` mapped/documented.
- [ ] [MAP-CFG-028] `[thumb].jpeg_quality` mapped/documented.
- [ ] [MAP-CFG-029] `[backdrop].width` and `[backdrop].height` mapped/documented.
- [ ] [MAP-CFG-030] `[backdrop].no_upscale` and `[backdrop].no_downscale` mapped/documented.
- [ ] [MAP-CFG-031] `[backdrop].jpeg_quality` mapped/documented.
- [ ] [MAP-CFG-032] `[profile].width` and `[profile].height` mapped/documented.
- [ ] [MAP-CFG-033] `[profile].no_upscale` and `[profile].no_downscale` mapped/documented.
- [ ] [MAP-CFG-034] `[profile].webp_quality` mapped/documented.
- [ ] [MAP-CFG-035] Any removed legacy config key is marked `removed-intentional` with migration note.

### Mode Behavior Inventory
- [ ] [IMG-LOGO-001] Logo mode preserves palette behavior where applicable.
- [ ] [IMG-LOGO-002] Logo mode handles transparency consistently with v0 semantics.
- [ ] [IMG-LOGO-003] Logo mode `padding=add` pads to target canvas.
- [ ] [IMG-LOGO-004] Logo mode `padding=remove` removes transparent border before plan.
- [ ] [IMG-LOGO-005] Logo mode `padding=none` performs no add/remove.
- [ ] [IMG-LOGO-006] Padding-remove sensitivity edge-case decisions are parity-tested.
- [ ] [IMG-LOGO-007] Sensitivity-related warnings/messages are parity-tested.
- [ ] [IMG-LOGO-008] EXIF orientation handling is defined and parity-tested.
- [ ] [IMG-LOGO-009] Logo `P`-mode palette conversion strategy parity (adaptive palette and approximate color-count retention) is golden-tested.
- [ ] [IMG-THUMB-001] Thumb mode uses cover/crop semantics.
- [ ] [IMG-THUMB-002] Thumb mode output format and quality semantics are parity-tested.
- [ ] [IMG-THUMB-003] Thumb JPEG encoder parameter parity (`optimize`/`progressive` + quality bounds) is tested.
- [ ] [IMG-BACKDROP-001] Backdrop mode uses cover/crop semantics.
- [ ] [IMG-BACKDROP-002] Backdrop mode output format and quality semantics are parity-tested.
- [ ] [IMG-BACKDROP-003] Backdrop mode re-uploads even on `NO_SCALE` to keep index behavior consistent.
- [ ] [IMG-BACKDROP-004] Backdrop JPEG encoder parameter parity (`optimize`/`progressive` + quality bounds) is tested.
- [ ] [IMG-PROFILE-001] Profile mode uses cover/crop semantics.
- [ ] [IMG-PROFILE-002] Profile mode WebP quality and alpha behavior are parity-tested.
- [ ] [IMG-PROFILE-003] Profile WebP encoder parameter parity (including method) and alpha-preservation semantics are tested.
- [ ] [IMG-SCALE-001] `SCALE_UP` behavior is deterministic and parity-tested.
- [ ] [IMG-SCALE-002] `SCALE_DOWN` behavior is deterministic and parity-tested.
- [ ] [IMG-SCALE-003] `NO_SCALE` behavior is deterministic and parity-tested.
- [ ] [IMG-SCALE-004] No-scale + force-upload semantics are parity-tested.
- [ ] [IMG-SCALE-005] For non-backdrop modes, `NO_SCALE + force_upload_noscale` still runs upload/failure handling parity path.
- [ ] [IMG-EXIF-001] EXIF orientation logic parity applies across all modes, including tall-image orientation guard behavior.

### Workflow + Discovery + Backup/Restore Inventory
- [ ] [RUN-001] Normal processing performs connectivity preflight before processing begins.
- [ ] [RUN-002] Connectivity preflight uses `/System/Info` semantics and detects auth/connectivity failures.
- [ ] [RUN-003] Preflight failures surface actionable errors and deterministic non-success behavior (v0 baseline captured in Phase 0).
- [ ] [DISC-001] Discovery with no library filter avoids unnecessary library-folder calls.
- [ ] [DISC-002] Discovery with library filters resolves and applies parent filtering correctly.
- [ ] [DISC-003] Discovery item-type mapping behavior is parity-tested.
- [ ] [DISC-004] Discovery short-circuit and pagination behavior is parity-tested.
- [ ] [DISC-005] Discovery requests `EnableImageTypes` derived from selected modes.
- [ ] [DISC-006] Discovery skips items lacking required image tags for requested modes.
- [ ] [BKP-001] Backup path scheme parity is frozen and tested (for example `<first2>/<id>/<stem>.<ext>` if preserved).
- [ ] [BKP-002] Backup naming rules per image type are deterministic and parity-tested.
- [ ] [BKP-003] Partial/full backup mode semantics are parity-tested.
- [ ] [BKP-004] Overwrite policy parity is explicit and tested (for example overwrite only on byte difference if preserved).
- [ ] [RST-001] Restore selection rules for single/all targets are deterministic and parity-tested.
- [ ] [RST-PAR-001] v0 `--restore-all` coverage is captured and frozen (help + runtime). Any mismatch is documented and resolved via DELTA.
- [ ] Decision hook for `RST-PAR-001`: if v0 help text and runtime differ, create/close `DELTA-RST-004` documenting which behavior v1 adopts, then update v1 help/docs accordingly.
- [ ] [RST-004] Missing or invalid restore roots fail with explicit behavior and tests.
- [ ] [RST-005] Restore dry-run performs no writes and records simulated outcomes.
- [ ] [RST-006] Restore-related docs include "not a disaster recovery backup" and UUID caveat (baseline-captured).
- [ ] [RST-007] Restore-all exclusivity refusals are deterministic and actionable (message + exit behavior).
- [ ] [RST-008] Backdrop restore enforces contiguous indices starting at 0; gaps/duplicates are explicit errors.

### HTTP Adapter Behavior Inventory
- [ ] [ADP-HTTP-001] HEAD retry behavior parity is preserved and documented (with explicit exceptions).
- [ ] [ADP-HTTP-002] Backdrop delete verification keeps explicit no-retry HEAD behavior where required.

### Observability Inventory
- [ ] [OBS-001] Outcome counters and summary aggregation match v0 semantics (counters may be non-exclusive); aggregation rules are captured and parity-tested.
- [ ] [OBS-002] Operator-facing summary fields match v0 or are intentional deltas with migration notes.
- [ ] [OBS-003] Progress logging cadence parity (every N images) is preserved or explicitly changed with docs.

## v1 Contract Inventory (New Surface / Not v0 Parity) - ID-Tracked

### CLI Contract Inventory
- [ ] [V1-CLI-001] Subcommand CLI contract is finalized: `run`, `restore`, `test-connection`, `config init`, `config validate`.
- [ ] [V1-CLI-002] `test-connection` maps connectivity/auth failures to exit code `2`.
- [ ] [V1-CLI-003] `config init` generates valid starter config for v1 schema.
- [ ] [V1-CLI-004] `config validate` validates schema + semantics and exits non-zero on invalid config.
- [ ] [V1-CLI-005] Exit code mapping is deterministic and stable (`0`, `1`, `2`, `3`, `4`, `5`).
- [ ] [V1-CLI-006] Partial run failures map to exit code `3`.
- [ ] [V1-CLI-007] Fatal unhandled errors map to exit code `4` with highest precedence.
- [ ] [V1-CLI-008] Restore policy refusals map to exit code `5`.
- [ ] [V1-CLI-009] Connectivity/auth failures map to exit code `2`.
- [ ] [V1-CLI-010] Validation/config errors map to exit code `1`.
- [ ] [V1-CLI-011] Argparse parse errors are normalized to v1 validation exit behavior.
- [ ] [V1-CLI-012] restore --all enforces exclusivity (only config/logging flags allowed).
- [ ] [V1-CLI-013] config init enforces exclusivity (rejects operational flags).

### Config Contract Inventory
- [ ] [V1-CFG-001] Enforce precedence `CLI > environment > TOML`.
- [ ] [V1-CFG-002] Effective config output includes value source per key.
- [ ] [V1-CFG-003] `JFIN_SERVER_URL` override is supported.
- [ ] [V1-CFG-004] `JFIN_API_KEY` override is supported.

### Observability Contract Inventory
- [ ] [V1-OBS-001] v1 defines whether outcomes are exclusive or non-exclusive; the chosen model is documented and tested.
- [ ] [V1-OBS-002] v1 outcome model is mutually exclusive by construction (each processed asset yields exactly one terminal outcome category), and aggregation is derived from those outcomes.

### Backup/Runtime Contract Inventory
- [ ] [V1-BKP-001] Run manifest is written to `backup_root/run_<run_id>/manifest.json` with deterministic pathing, and this behavior is tested.

### Restore Safety Contract Inventory
- [ ] [V1-RST-001] `restore --all` equivalent requires exact force flag `--i-know-what-im-doing`.
- [ ] [V1-RST-002] Fingerprint mismatch refusal is enforced unless forced.
- [ ] [V1-RST-003] Restore safety refusals map to exit code `5`.
- [ ] [V1-RST-004] v1 restore CLI help surfaces the restore caveats ("not DR" + UUID caveat) or points to docs explicitly.

## Intentional Deltas (DELTA-*)
- [ ] Every `DELTA-*` listed in this checklist is linked from migration guide and parity matrix rows.
- [ ] Every v1 contract item without a v0 equivalent is tagged `new-v1` and cross-linked to `DELTA-*` when behavior changes user-facing outcomes.

## Phase 0 - Baseline Freeze and Mechanical Artifact Capture
**Goal:** Capture reproducible v0 baseline artifacts so parity disputes are evidence-based.

- [ ] Create artifact directories:
- [ ] `artifacts/v0/cli/help/`
- [ ] `artifacts/v0/cli/invalid_args/`
- [ ] `artifacts/v0/cli/exit_codes/`
- [ ] `artifacts/v0/images/corpus_inputs/`
- [ ] `artifacts/v0/images/expected_outputs/`
- [ ] `artifacts/v0/config/examples/`
- [ ] `artifacts/v0/discovery/`
- [ ] `artifacts/v0/discovery/request_traces/`
- [ ] `artifacts/v0/backdrop/request_traces/`
- [ ] `artifacts/v0/backup_restore/`
- [ ] `artifacts/v0/run_logs/`
- [ ] `artifacts/v1/discovery/request_traces/`
- [ ] `artifacts/v1/backdrop/request_traces/`
- [ ] Create repeatable capture script/target (for example `scripts/capture_v0_baseline.*` or `make capture-v0-baseline`).
- [ ] Capture and store exact command outputs:
- [ ] `python -m jfin --help`
- [ ] `python -m jfin --generate-config --help`
- [ ] `python -m jfin --test-jf --help`
- [ ] `python -m jfin --restore --help`
- [ ] `python -m jfin --restore-all --help`
- [ ] `python -m jfin --mode logo --help`
- [ ] `python -m jfin --mode profile --help`
- [ ] [BASELINE-CLI-001] All Phase 0 help captures use v0-supported invocations only; unknown-arg/global-help fallback output is rejected as baseline evidence.
- [ ] [BASELINE-CLI-002] Help captures must include the exact command and exit code in the artifact header (or filename convention), so you can prove it didn’t silently fall back to global help.
- [ ] Capture invalid-arg combinations and refusal text snapshots for known rejected combos.
- [ ] Capture invalid baseline combo output: `--generate-config` + operational mode flags.
- [ ] Capture invalid baseline combo output: `--restore-all` + `--single`.
- [ ] Capture invalid baseline combo output: `--restore-all` + mode/image flags.
- [ ] Capture invalid baseline combo output: `--single` without `--mode`.
- [ ] Capture baseline verbosity precedence behavior: `--silent` + `--verbose` resolves deterministically (document precedence), with snapshot evidence.
- [ ] Capture observed v0 exit-code baseline matrix (including argparse parse failures) for success, validation error, auth/connectivity failure, partial failure, refusal, and fatal where reachable.
- [ ] Capture image corpus inputs and expected outputs for all four modes and key edge cases.
- [ ] Capture baseline discovery traces for with-library and without-library scenarios.
- [ ] Capture v0 request traces (method, path, query/body keys) for discovery and backdrop delete/verify flows.
- [ ] Capture baseline backup/restore filesystem layout artifacts and manifests.
- [ ] Capture dry-run logs proving no write operations are executed.
- [ ] Create `docs/behavior-parity-matrix-v1.md` with all IDs from this checklist pre-seeded.
- [ ] Define trace-comparison format for v0/v1 discovery and backdrop request parity reviews.
- [ ] Tag/branch baseline commit before migration work starts.

## Phase 1 - Foundation, Tooling, and Package Skeleton
**Goal:** Establish v1 structure and enforcement before behavior migration.

- [ ] This phase delivers v1 requirements that intentionally differ from v0 baseline.
- [ ] Add/finalize `pyproject.toml` config for `ruff`, `mypy`, `pytest`, `bandit`, `pip-audit`.
- [ ] CI runs required jobs on Python `3.13` and latest stable Python.
- [ ] Update CI matrix to include Python `3.13` and remove unsupported versions for the v1 branch.
- [ ] Ensure README + packaging metadata consistently declare Python `3.13+` for v1.
- [ ] Migrate tool configuration to `pyproject.toml` from legacy config locations.
- [ ] Scaffold packages:
- [ ] `src/jfin/bootstrap/`
- [ ] `src/jfin/cli/`
- [ ] `src/jfin/app/`
- [ ] `src/jfin/app/use_cases/`
- [ ] `src/jfin/app/services/`
- [ ] `src/jfin/domain/`
- [ ] `src/jfin/domain/policies/`
- [ ] `src/jfin/domain/services/`
- [ ] `src/jfin/adapters/`
- [ ] `src/jfin/observability/`
- [ ] `src/jfin/shared/`
- [ ] `src/jfin/__main__.py` remains thin and delegates to bootstrap runner.
- [ ] `bootstrap/runner.py` is the only dependency wiring location.
- [ ] Add import-boundary tests blocking forbidden dependencies.
- [ ] Add temporary command stubs with deterministic non-success exits until implemented.

## Phase 2 - Domain Contracts, Policies, and Error Taxonomy
**Goal:** Freeze domain model and policy behavior.

- [ ] Implement domain enums for modes, scale behaviors, padding behaviors, and outcomes.
- [ ] Implement validated domain models:
- [ ] `ModeSettings`
- [ ] `ScalePlan`
- [ ] `RunRequest`
- [ ] `DiscoveredAsset`
- [ ] `ProcessOutcome`
- [ ] `ProcessResult`
- [ ] `RestoreResult`
- [ ] Implement shared errors:
- [ ] `ValidationError`
- [ ] `ConnectivityError`
- [ ] `PolicyRefusal`
- [ ] `ProcessingError`
- [ ] `FatalError`
- [ ] Define ports:
- [ ] `JellyfinGatewayPort`
- [ ] `ImageEnginePort`
- [ ] `BackupStorePort`
- [ ] `ConfigProviderPort`
- [ ] `EventSinkPort`
- [ ] `ClockPort`
- [ ] Implement policies:
- [ ] `WritePolicy`
- [ ] `RestoreSafetyPolicy`
- [ ] `RateLimitPolicy`
- [ ] Enforce no direct sleep/wall-clock reads outside `ClockPort` adapter.
- [ ] Add policy and constructor invariant tests.

## Phase 3 - Observability and Runtime Context Migration
**Goal:** Remove runtime globals and provide typed operational telemetry.

- [ ] Implement `RunContext` and ensure it carries run-scoped state.
- [ ] Remove active use of module-global runtime stats/failure lists.
- [ ] Implement typed events:
- [ ] `RunStarted`
- [ ] `DiscoveryFinished`
- [ ] `ImagePlanned`
- [ ] `BackupWritten`
- [ ] `UploadAttempted`
- [ ] `UploadFailed`
- [ ] `RestoreRefused`
- [ ] `RunFinished`
- [ ] Implement metrics accumulator with parity to v0 operator-facing summaries.
- [ ] Implement event sinks:
- [ ] `LoggingEventSink`
- [ ] `MetricsEventSink`
- [ ] optional `JsonlEventSink`
- [ ] Implement and verify `OBS-001`, `OBS-002`, and `OBS-003` behaviors.
- [ ] Add event-sequence tests for success, partial failure, restore refusal, and backdrop recovery.
- [ ] Close and evidence all `OBS-*` parity IDs.
- [ ] Close and evidence all `V1-OBS-*` contract IDs.

## Phase 4 - Config Resolution and Filesystem Runtime Contract
**Goal:** Deliver deterministic config + runtime filesystem behavior.

- [ ] Implement schema-first config sections:
- [ ] `[server]`
- [ ] `[runtime]`
- [ ] `[discovery]`
- [ ] `[logging]`
- [ ] `[modes.logo]`
- [ ] `[modes.thumb]`
- [ ] `[modes.backdrop]`
- [ ] `[modes.profile]`
- [ ] Implement deterministic precedence `CLI > env > TOML`.
- [ ] Implement env override contract (including `JFIN_SERVER_URL`, `JFIN_API_KEY`).
- [ ] Implement source-tracked effective-config output.
- [ ] `config validate` performs schema + semantic validation and redacted display.
- [ ] Ensure `config init` output is safe-by-default (`dry_run=true`) or intentional-delta documented.
- [ ] Preserve/map `fail_fast` semantics and validation behavior.
- [ ] Preserve or intentional-delta-document target-size one-side inference and min-1px clamp behavior.
- [ ] Backup root preflight:
- [ ] absolute path normalization
- [ ] create-if-missing
- [ ] writability validation
- [ ] actionable failure on invalid root
- [ ] Ensure staging lives only under `backup_root/staging/`.
- [ ] [V1-BKP-001] Ensure run manifest path is `backup_root/run_<run_id>/manifest.json`.
- [ ] Ensure no persistent state is written outside configured backup root.
- [ ] Add tests for precedence, redaction, invalid config ranges/enums, and preflight behavior.
- [ ] Close and evidence all `CFG-*` parity IDs.
- [ ] Close and evidence all `V1-CFG-*` contract IDs.
- [ ] Close and evidence all `V1-BKP-*` contract IDs.
- [ ] Close and evidence all `MAP-CFG-*` parity IDs.

## Phase 5 - Adapter Implementations
**Goal:** Implement infrastructure adapters behind stable ports.

- [ ] HTTP transport with retry/backoff for transient failures.
- [ ] Jellyfin gateway adapter with explicit port-to-endpoint mapping.
- [ ] Enforce `WritePolicy` inside Jellyfin adapter for write-capable operations.
- [ ] Pillow image adapter preserving parity-critical mode semantics.
- [ ] Filesystem backup store with deterministic backup pathing and manifest writing.
- [ ] Config adapters for TOML, env overrides, and schema.
- [ ] Logging adapter factory.
- [ ] Implement and verify `ADP-HTTP-001` and `ADP-HTTP-002` behaviors.
- [ ] Add adapter unit tests and contract tests against fakes and concrete adapters.
- [ ] Close and evidence all `ADP-HTTP-*` parity IDs.

## Phase 6 - Application Services, Use Cases, and Run Semantics
**Goal:** Implement orchestration behavior with explicit parity rules.

- [ ] Implement app services:
- [ ] normalization coordinator
- [ ] backup/upload coordinator
- [ ] discovery processor
- [ ] result aggregator
- [ ] transaction recovery handler
- [ ] Implement use-cases:
- [ ] `run_batch`
- [ ] `run_single_item`
- [ ] `run_single_profile`
- [ ] `restore_all`
- [ ] `restore_single`
- [ ] `test_connection`
- [ ] `config_init`
- [ ] `config_validate`
- [ ] Ensure use-cases only depend on ports and domain/app models.
- [ ] Ensure no adapter imports outside bootstrap wiring.
- [ ] Enforce `WritePolicy` at service boundary.
- [ ] Implement partial-failure aggregation semantics.
- [ ] Implement and test parity-critical run/discovery rules:
- [ ] [RUN-001] and [RUN-002] connectivity preflight semantics
- [ ] [RUN-003] actionable preflight failure behavior parity
- [ ] [V1-CLI-009] exit code `2` mapping for auth/connectivity
- [ ] [DISC-001] no-library optimization behavior
- [ ] [DISC-002] library-filter path behavior
- [ ] [DISC-003] item-type mapping behavior
- [ ] [DISC-004] discovery iteration/pagination behavior
- [ ] [DISC-005] `EnableImageTypes` selection behavior
- [ ] [DISC-006] required image-tag filtering behavior
- [ ] [CLI-034], [CLI-035], and [CLI-036] single-target mode semantics
- [ ] Add workflow tests covering these rules.
- [ ] Capture v1 request traces (method, path, query/body keys) for discovery parity comparison against v0.

## Phase 7 - Backdrop Transaction Model and Restore Safety
**Goal:** Implement safety-critical backdrop/restore workflows with refusal-first defaults.

- [ ] Implement `BackdropReplacementTransaction` state machine.
- [ ] Implement states:
- [ ] `STAGED`
- [ ] `NORMALIZED`
- [ ] `DELETED`
- [ ] `UPLOADED`
- [ ] `FINALIZED`
- [ ] `FAILED`
- [ ] Persist `transaction.json` under `backup_root/staging/<item_id>/`.
- [ ] Ensure `transaction.json` required fields exist:
- [ ] `schema_version`
- [ ] `jfin_version`
- [ ] `created_at`
- [ ] `updated_at`
- [ ] `server_fingerprint`
- [ ] `item_id`
- [ ] `expected_backdrop_count`
- [ ] `uploaded_indices`
- [ ] `current_state`
- [ ] `last_error`
- [ ] Enforce lifecycle: stage -> normalize -> delete -> upload -> finalize.
- [ ] Refuse unknown transaction states/schemas/critical-field omissions by default.
- [ ] Startup scan refuses incomplete transactions unless explicit remediation is chosen.
- [ ] `--resume` skips already-uploaded indices unless forced.
- [ ] `--cleanup-staging` provides explicit cleanup path.
- [ ] Preserve recoverability on partial failures; no automatic destructive cleanup.
- [ ] Implement `RestoreSafetyPolicy` fingerprint checks and risky restore refusal.
- [ ] Enforce exact force flag `--i-know-what-im-doing` for risky restores and `restore --all`.
- [ ] Restore refusals map to exit code `5`.
- [ ] Close and evidence parity-critical IDs:
- [ ] [IMG-BACKDROP-003]
- [ ] [IMG-BACKDROP-004]
- [ ] [BKP-001], [BKP-002], [BKP-003], [BKP-004]
- [ ] [RST-001], [RST-PAR-001], [RST-004], [RST-005], [RST-006], [RST-007], [RST-008]
- [ ] [V1-RST-001], [V1-RST-002], [V1-RST-003], [V1-RST-004]
- [ ] Add crash/recovery/refusal/forced-override tests.
- [ ] Capture v1 backdrop request traces and compare to v0 delete/verify trace baselines.

## Phase 8 - CLI Contract Finalization and Mapping
**Goal:** Finalize command surface and migration compatibility mapping.

- [ ] Finalize subcommands:
- [ ] `run`
- [ ] `restore`
- [ ] `test-connection`
- [ ] `config init`
- [ ] `config validate`
- [ ] Capture and store exact v1 subcommand help outputs in `artifacts/v1/cli/help/`:
- [ ] `python -m jfin run --help`
- [ ] `python -m jfin restore --help`
- [ ] `python -m jfin test-connection --help`
- [ ] `python -m jfin config init --help`
- [ ] `python -m jfin config validate --help`
- [ ] Implement strict parser exclusivity and command-specific option validation.
- [ ] Implement stable exit code contract with precedence:
- [ ] `0` success
- [ ] `1` validation/config error
- [ ] `2` connectivity/auth error
- [ ] `3` partial failures
- [ ] `4` fatal error (wins precedence)
- [ ] `5` restore safety refusal
- [ ] [EXIT-001] Exit code matrix is defined and tested across success, validation/config, connectivity/auth, partial failures, refusal, and fatal.
- [ ] [EXIT-002] Exit code precedence rules are enforced (`fatal=4` wins).
- [ ] [EXIT-003] Argparse parse errors are normalized to the v1 validation exit behavior.
- [ ] Refusal messaging always includes reason + remediation command.
- [ ] Implement and verify [CLI-032], [CLI-033], [CLI-034], [CLI-035], and [CLI-036].
- [ ] Implement and verify `V1-CLI-*` contract IDs.
- [ ] Complete v0 -> v1 CLI flag mapping table with parity IDs.
- [ ] Close and evidence all `CLI-*` parity IDs.
- [ ] Close and evidence all `V1-CLI-*` contract IDs.
- [ ] Close and evidence all `MAP-CLI-*` parity IDs.
- [ ] Add CLI tests for help text, invalid combinations, refusal copy, and exit determinism.

## Phase 9 - Full Test Suite Rewrite and Coverage Hardening
**Goal:** Replace legacy tests with parity-first architecture-aligned suites.

- [ ] Adopt suites:
- [ ] `tests/unit/domain/`
- [ ] `tests/unit/app/`
- [ ] `tests/unit/adapters/`
- [ ] `tests/contract/`
- [ ] `tests/workflows/`
- [ ] `tests/cli/`
- [ ] `tests/golden/`
- [ ] Ensure no live Jellyfin calls in unit tests; use mocks/fakes.
- [ ] Implement per-port contract suites for fakes + adapters.
- [ ] Add deterministic golden corpus and comparator harness.
- [ ] Add deterministic fixtures/builders for image, payload, and config scenarios.
- [ ] Add mandatory scenario coverage:
- [ ] dry-run blocks POST/DELETE in service and adapter layers
- [ ] backdrop full lifecycle and recoverable partial failure
- [ ] incomplete transaction refusal on startup
- [ ] resume and cleanup behavior
- [ ] no-scale and force-upload behavior
- [ ] non-backdrop `NO_SCALE + force_upload_noscale` upload-path behavior
- [ ] logo padding sensitivity edge-case behavior and messaging
- [ ] restore --all exclusivity and config-init exclusivity behavior
- [ ] restore refusal and force-override behavior
- [ ] backdrop contiguous-index restore behavior
- [ ] config precedence and redaction behavior
- [ ] `fail_fast` behavior and retry/backoff behavior
- [ ] discovery behavior with and without library filters
- [ ] discovery `EnableImageTypes` and image-tag filtering behavior
- [ ] backup path/overwrite semantics behavior
- [ ] event/metrics parity behavior
- [ ] progress logging cadence parity behavior
- [ ] JPEG/WebP encoder parameter parity behavior and EXIF tall-image guard behavior
- [ ] unknown transaction schema/state refusal behavior
- [ ] Close and evidence all `IMG-*`, `RUN-*`, `DISC-*`, `BKP-*`, `RST-*`, `OBS-*`, `ADP-HTTP-*`, `V1-CLI-*`, `V1-CFG-*`, `V1-OBS-*`, `V1-BKP-*`, and `V1-RST-*` IDs.

## Phase 10 - Docs, Parity Sign-Off, Legacy Retirement, and Release
**Goal:** Finalize docs, lock parity, retire legacy modules safely, and ship.

- [ ] Publish migration guide mapping v0 CLI/config to v1 CLI/config.
- [ ] Publish/update parity matrix for all IDs in this checklist.
- [ ] Publish architecture boundaries and composition-root rules.
- [ ] Publish safety docs for write gating, backdrop transactions, and restore policies.
- [ ] Publish backup limitation docs: not disaster recovery + UUID caveat.
- [ ] Ensure restore-related CLI help surfaces caveat messaging or references docs.
- [ ] Publish/maintain `docs/v1-intentional-deltas.md` and reference all `DELTA-*` IDs in migration docs.
- [ ] Publish container runtime contract and env variable requirements.
- [ ] Ensure docs, packaging, and CI consistently declare Python `3.13+`.
- [ ] Move legacy modules to `v0/` only after parity + tests + docs gates are complete:
- [ ] `src/jfin/cli.py`
- [ ] `src/jfin/pipeline.py`
- [ ] `src/jfin/client.py`
- [ ] `src/jfin/config.py`
- [ ] `src/jfin/state.py`
- [ ] `src/jfin/imaging.py`
- [ ] `src/jfin/backup.py`
- [ ] `src/jfin/discovery.py`
- [ ] `src/jfin/logging_utils.py`
- [ ] Delete remaining legacy modules only after review sign-off.
- [ ] Tag `v1.0.0` only after all final acceptance gates are complete.

## Cross-Phase Safety + Parity-Critical Rules (Always True)
- [ ] [SAFE-001] No POST/DELETE operations in dry-run code paths.
- [ ] [SAFE-002] `WritePolicy` enforced in both services and adapter writes.
- [ ] [SAFE-003] Domain layer does not import adapters/CLI/HTTP/filesystem frameworks.
- [ ] [SAFE-004] Use-cases depend on ports only; bootstrap is sole dependency wiring location.
- [ ] [SAFE-005] Unknown transaction state/schema always refuses by default.
- [ ] [SAFE-006] Risky restore operations require `--i-know-what-im-doing`.
- [ ] [SAFE-007] Secrets are redacted from logs/config output.
- [ ] [SAFE-008] CLI behavior is deterministic and non-interactive.
- [ ] [SAFE-009] Stateful writes are limited to configured backup/staging roots.
- [ ] [SAFE-010] No active v1 source file exceeds 500 LOC at release gate (legacy v0 modules may exceed until retirement).
- [ ] [SAFE-011] Connectivity preflight is enforced; v1 maps auth/connectivity failures to exit 2 (see `V1-CLI-009`).
- [ ] [SAFE-012] Backdrop NO_SCALE re-upload parity behavior is preserved or intentionally changed with docs.
- [ ] [SAFE-013] Backup path scheme and overwrite semantics are deterministic and documented.
- [ ] [SAFE-014] Silent mode behavior is explicit and parity-tested.
- [ ] [SAFE-015] Restore caveat messaging (not DR / UUID caveat) appears in docs and v1 help surface (see `V1-RST-004`).
- [ ] [SAFE-016] `restore --all` and `config init` exclusivity safeguards are enforced and contract-tested.
- [ ] [SAFE-017] Discovery/backdrop parity uses v0/v1 trace snapshots, not only unit assertions.

## Final Acceptance Gates (Release Blockers)
- [ ] Architecture complete with explicit ports/adapters and single composition root.
- [ ] `RunContext` fully replaces global mutable runtime state in active paths.
- [ ] Import boundaries enforced in CI and passing.
- [ ] Dual write-gate enforcement proven by tests.
- [ ] Backdrop transaction and recovery rules implemented and tested.
- [ ] Restore safety policy and force semantics implemented and tested.
- [ ] Full test suite passes (`unit`, `contract`, `workflow`, `cli`, `golden`).
- [ ] Quality/security gates pass (`ruff`, `mypy`, `pytest`, `bandit`, `pip-audit`).
- [ ] All parity IDs in matrix are closed with evidence.
- [ ] All intentional deltas are tracked as `DELTA-*` and mapped in parity docs/migration docs.
- [ ] Migration guide and parity matrix are reviewed and complete.
- [ ] User docs reflect v1 CLI/config changes and Python `3.13+`.
- [ ] Container runtime contract docs are complete.
- [ ] All non-`v0/` source files comply with SAFE-010 (<= 500 LOC).
- [ ] `v1.0.0` tag is created only after all blockers are checked.
