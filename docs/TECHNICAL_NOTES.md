# Jellyfin Image Normalizer - Technical Overview

This document explains how the Jellyfin Image Normalizer CLI works so a new team can operate or extend it. It covers runtime flow, configuration, modules, key classes/functions, imaging rules, API usage, and backup/restore behavior.

## Purpose and Scope
- Normalize Jellyfin artwork for three modes: `logo` (transparent fits), `thumb` (landscape/poster cover), and `profile` (user avatars).
- Operates fully via Jellyfin APIs: discover items/users, stream images, normalize in memory with Pillow, and (optionally) upload replacements.
- Safety first: dry-run defaults are baked in; writes require explicit config/CLI approval. Backups are stored before uploads when enabled.

## Architecture at a Glance
- Entry point: `jfin.py` parses CLI flags, loads/merges config, validates modes, and dispatches to the pipeline.
- Core package `jfin_core/`:
  - `config.py`: TOML config loading/generation, CLI overrides, discovery settings, mode runtime settings, client factory.
  - `client.py`: `JellyfinClient` (requests + retry/backoff, dry-run/write gates, image uploads/downloads).
  - `discovery.py`: operator resolution, library and item discovery, containers (`LibraryRef`, `DiscoveredItem`).
  - `imaging.py`: resize planning (`ScalePlan`), EXIF handling, mode-specific builders, encoders, NO_SCALE handling.
  - `pipeline.py`: orchestrates library/profile processing, single-item/user runs, restore, and per-image normalization.
  - `backup.py`: backup path/content-type helpers and backup-mode enforcement.
  - `logging_utils.py`: CLI/file logging configuration and run summaries.
  - `state.py`: shared run id, stats counters, and API failure tracking.
- Tests: `tests/` covers config parsing, imaging decisions, client dry-run safety, discovery, and pipeline behavior (with mocks).

## Configuration Model (`config.toml`)
- Location: defaults to `config.toml` beside the repo root (`jfin_core/config.py:default_config_path`). Generate a starter file with `python jfin.py --generate-config` (optionally `--config <path>.toml`, no other operational flags allowed).
- Format: TOML only. `.json` configs are rejected at load time. Comments are inline `#` entries; there is no `_comments` table. Deprecated keys such as `allow_writes`, `allow_uploads`, `operator.user_id`, or `libraries.name` are rejected during validation.
- Sections: grouped defaults under `[SERVER]`, `[API]`, `[BACKUP]`, `[MODES]` (plus `[logging]`, `[operator]`, `[libraries]`, and mode sections). Keys are lifted to the root for runtime use; only the current schema is supported.
- Required: `jf_url` (base URL) and `jf_api_key` (X-Emby-Token), non-empty strings.
- API behavior: `verify_tls` (bool), `timeout` (sec), `jf_delay_ms` (throttle between requests), `api_retry_count`, `api_retry_backoff_ms`, `fail_fast` (raise on API upload errors), `dry_run` (default true in generated config).
- Operations: `operations` pipe-separated string or array of modes (`logo|thumb|profile`). CLI `--mode` still overrides.
- Backup: `backup` (bool), `backup_mode` (`partial` backs up only scaled images; `full` backs up everything), `backup_dir`, `force_upload_noscale` (re-upload even when no scaling applied).
- Logging: `logging.file_path`, `file_enabled`, `file_level`, `cli_level`, `silent`. CLI `-s/--silent` and `-v/--verbose` override CLI logging.
- Discovery: `operator.username` to choose the user for library queries; `libraries.names` to filter by name (normalized, movie/tv collection types only).
- Mode sections (`logo`, `thumb`, `profile`):
  - Common: `width`, `height`, `no_upscale`, `no_downscale`.
  - Validation: widths/heights must be >0; CLI width/height overrides must also be positive, and a missing side is inferred from the configured aspect ratio (clamped to at least 1px).
  - `logo`: `no_padding` to skip transparent canvas centering.
  - `thumb`: `jpeg_quality` (1-95).
  - `profile`: `webp_quality` (1-100).

Example TOML:
```toml
jf_url = "https://your-jellyfin-url-here"
jf_api_key = "YOUR_API_KEY"
operations = ["logo", "thumb", "profile"]
dry_run = true
backup = true

[logging]
cli_level = "INFO"
file_enabled = true

[logo]
width = 800
height = 310
no_padding = false
```

## CLI Entrypoints (`jfin.py:parse_args`)
- Core flags: `--config`, `--generate-config`, `--test-jf`, `--mode`, `--single <user|itemId>`, `--restore`, `--restore-all` (must be used alone except logging/config flags), `--dry-run`, `--backup`.
- Config path: `--config <file>.toml` (defaults to `config.toml` beside the repo). Non-TOML paths are rejected.
- Imaging overrides: `--width/--height`, `--jpeg-quality`, `--webp-quality`, `--no-upscale`, `--no-downscale`, `--no-padding` (logo only), `--force-upload-noscale`. Width/height overrides must be positive; if only one side is provided, the other is inferred from the configured aspect ratio.
- Jellyfin overrides: `--jf-url`, `--jf-api-key`, `--operator`, `--libraries`, `--jf-delay-ms`.
- Logging toggles: `--silent/-s`, `--verbose/-v`.
- Exclusivity/validation: `--generate-config` rejects any operational flags; `--restore-all` rejects combinations except config/logging flags; `--test-jf` requires `--jf-url`/`--jf-api-key` overrides or populated config values.
- No-op guards: CLI emits warnings when mode-specific flags have no effect (e.g., `--jpeg-quality` without `thumb`, `--webp-quality` without `profile`, `--no-padding` without `logo`).
- Exit behavior: most validation errors raise `SystemExit(1)` after recording stats; `--test-jf` exits immediately after the connectivity check.

## Runtime Flow (High Level)
1) Parse args and resolve `config_path` (CLI or default `config.toml`).  
2) Configure logging early, load the TOML config, merge CLI overrides, and validate config values.  
3) Validate `--restore-all` exclusivity; normalize backup mode.  
4) Determine operations: `test-jf` shortcut, `restore-all` runs all modes, otherwise `parse_operations` from CLI/config.  
5) Build `JellyfinClient` from config (writes enabled when `dry_run=false`).  
6) For each mode, validate required config and build `ModeRuntimeSettings` (width/height, scaling flags, qualities, padding).  
7) Branches:
   - `--single` + `logo|thumb`: call `process_single_item_api` (no discovery) with the provided item id.
   - `--single` + `profile`: call `process_single_profile` (username lookup).
   - `--restore` + `--mode`: restore backups for those modes; with `--single`, restore only the targeted item/user using backup file lookup.
   - `--restore-all`: reuses the same restore path with all modes selected.
   - Normal processing: library modes (`logo`/`thumb`) via discovery + normalize; `profile` via user list.
8) Always log scale decisions, API failures, and run summary before exit.

## Discovery and Library Processing (`pipeline.process_libraries_via_api`)
- Build `DiscoverySettings` from config and requested operations; image types are derived from modes (`Logo`, `Thumb`).
- Resolve operator (`resolve_operator_user`): prefer configured `username`, else first active user from `/Users?isDisabled=false`.
- Discover libraries (`discover_libraries`): `/Users/<userId>/Items` filtered to collection types `movies`/`tvshows` and optional normalized name matches.
- Discover items (`discover_library_items`): paginated `/Users/<userId>/Items` queries with params `ParentId=<libraryId>`, `IncludeItemTypes=Movie,Series,Season,Episode`, `Recursive=true`, `EnableImageTypes`, `ImageTypeLimit=1`. Collect items with requested image tags.
- Normalize images (`process_discovered_items` -> `normalize_item_image_api`):
  - Fetch original via `/Items/<itemId>/Images/<ImageType>`.
  - Apply EXIF orientation, plan resize (`fit` for logos, `cover` for thumbs), and decide SCALE_UP/DOWN/NO_SCALE based on `allow_upscale/allow_downscale`.
  - Optionally back up originals (`backup_mode` gate) to `backup/<first2>/<id>/<stem>.<ext>` using inferred content type.
  - For NO_SCALE: record success; optionally re-upload original when `force_upload_noscale` is true.
  - For scaled images: build normalized image (see Imaging Rules), encode, and upload via `set_item_image_bytes` (base64 payload). Track API failures in `state.api_failures`.
  - Progress logged every 25 images.

## Profile Processing (`pipeline.process_profiles` / `process_single_profile`)
- Pull active users via `/Users?isDisabled=false`. For single-user runs, match case-insensitive username (`find_user_by_name`).
- Skip users without `PrimaryImageTag`. Fetch profile bytes via `/UserImage?userId=<id>`.
- Plan cover resize; optional backup using image type `Primary`. NO_SCALE is treated the same as items (with optional forced upload).
- Build profile image (RGBA cover/crop) and encode as WebP with configured quality. Upload through `set_user_profile_image` (DELETE existing then POST). Dry-run short-circuits uploads.

## Imaging Rules (`jfin_core/imaging.py`)
- `make_scale_plan` computes scale + target size and labels decision (`SCALE_UP`, `SCALE_DOWN`, `NO_SCALE`). Scaling respects `allow_upscale` / `allow_downscale`; disallowed directions clamp to 1.0 (no resize).
- `handle_no_scale` centralizes NO_SCALE behavior (success unless forced upload fails).
- Mode builders:
  - Logo: convert to RGBA, resize with LANCZOS, center on transparent canvas unless `no_padding`; preserve palette (`P` mode) by converting back with adaptive palette and original color count when known; `LA` preserved. Output `image/png`.
  - Thumb: convert to RGB, cover-scale then center-crop to canvas. Output JPEG with `jpeg_quality`, optimized + progressive.
  - Profile: convert to RGBA, cover-scale then crop. Output WebP with `webp_quality` (method=6). Alpha preserved.
- EXIF orientation: `apply_exif_orientation` uses transpose but avoids rotating tall images when orientation implies swap and height >= width.
- Color stats: `get_palette_color_count` attempts to retain palette size for logos (used only when original mode is `P`).

## Jellyfin API Touchpoints (`jfin_core/client.py`)
- GET helpers with retry/backoff: `_get`, `_get_json`; use `X-Emby-Token` header only.
- Discovery: `/System/Info` (connectivity test), `/Users`, `/Users/<id>/Items`, `/Items/<id>/Images/<type>`, `/UserImage?userId=<id>`.
- Uploads:
  - Items: `set_item_image_bytes` POSTs base64 image to `/Items/<id>/Images/<type>` with `Content-Type` set from normalized format. Optional `set_item_image` reads from disk.
  - Profiles: `set_user_profile_image` DELETEs `/UserImage?userId=<id>` then POSTs base64 to the same endpoint. `delete_user_profile_image` treats 404 as success.
- Safety gates: `_writes_allowed` blocks POST/DELETE when `dry_run` is true. `delay` enforces per-request sleep after successful POSTs.
- Failure reporting: `_post_image` appends failure dicts to `state.api_failures` (with item/user id, image_type, path, error) and honors `fail_fast` to raise on first failure.

## Backup and Restore (`jfin_core/backup.py`, `pipeline.restore_from_backups`, `restore_single_from_backup`)
- Backup filenames derive from Jellyfin image type via `FILENAME_CONFIG` (`Logo`->`logo.png`, `Thumb`->`landscape.jpg`, `Primary`->`profile.*`).
- Directory scheme: `<backup_root>/<first2_of_id>/<full_id>/<stem>.<ext>` to avoid large single directories.
- `backup_mode`: `partial` backs up only SCALE_UP/DOWN images; `full` backs up all decisions. Existing backups are overwritten only when bytes differ (with log notes).
- Restore: walk backup tree, infer `image_type` from filename, upload via profile or item upload paths, and log successes/errors (dry-run now logs + counts success without calling the API). Missing backup root is fatal.
- Single restore: `restore_single_from_backup` locates a backup by target id + mode and uploads it (or dry-runs) for `--restore --single --mode=<mode>`.

## Logging, State, and Metrics
- `logging_utils.setup_logging` configures CLI/file handlers with formatter `[run_id=<token>]`. `log_run_start` and `log_run_summary` wrap each run.
- `state.RunStats` counts processed/success/warning/error and failed items (id + reason). Global lists `upscaled_images` / `downscaled_images` capture resizing actions for summary output. `api_failures` store structured upload failures.
- `--silent` suppresses stdout logs (critical still to stderr); verbose enables DEBUG for CLI handler.

## Key Data Classes and Helpers
- `ModeRuntimeSettings` (`jfin_core/config.py`): resolved per-mode sizes, scaling flags, qualities, padding.
- `OperatorSpec`, `DiscoverySettings` (`config.py`): operator + library filters and item/image query settings.
- `LibraryRef`, `DiscoveredItem` (`discovery.py`): carry ids, names, collection types, and discovered image types.
- `ScalePlan` (`imaging.py`): resize decision, factors, and original/target dimensions; used for reporting and NO_SCALE handling.
- `JellyfinClient` (`client.py`): API facade with request helpers, GET methods, upload/delete calls, dry-run gatekeeping.

## Config Migration Notes
- Runtime config is TOML-only (`config.toml` default). Non-TOML paths raise a configuration error.
- Generate a commented template with `python jfin.py --generate-config` (or `--config <path>.toml`).

## Development and Testing Notes
- Dependencies (`requirements.txt`): Pillow, requests, pytest (for local testing).
- Run tests with `python -m pytest`. Tests rely on mocks/stubs; no live Jellyfin calls are performed.
- Config tests cover TOML parsing/validation; runtime JSON configs are no longer supported.
- When adding a new image mode, update `jfin_core/constants.py` (`MODE_CONFIG`, `IMAGE_TYPE_TO_MODE`, `MODE_TO_IMAGE_TYPE`, `FILENAME_CONFIG`), extend config parsing, and add a normalization branch in `imaging.build_normalized_image` plus pipeline wiring.
