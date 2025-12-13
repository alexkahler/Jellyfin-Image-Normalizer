# Changelog

## 0.2.0

### Added
* Backdrop normalization pipeline:
  * New `backdrop` mode alongside `logo`, `thumb`, and `profile`, with a dedicated multi-phase API flow that fetches all backdrops, normalizes them in memory, deletes the originals, verifies via a 404 HEAD check, and re-uploads in same order.
  * New `[backdrop]` section in `config.toml`/`config.example.toml` with width/height and `jpeg_quality` settings, and discovery/processing wiring so backdrops are discovered via `BackdropImageTags` and included when `operations` contains `"backdrop"`.
* Backdrop-aware backup/restore:
  * Backups now support a `Backdrop` image type with filenames like `backdrop.jpg`, `backdrop1.jpg`, `backdrop2.jpg`, etc., and restore logic that enforces contiguous indices starting at 0 (any gap/duplicate is treated as an error and skips that item’s backdrops).
  * CLI restore operations (`--restore`, `--restore-all`, `--restore --single`) now handle backdrops in addition to logos/thumbs/profiles, and keep behavior predictable in dry-run mode.
* CLI and docs:
  * `--mode=backdrop` support for both library runs and `--single` item runs.
  * New docs for backdrop behavior and configuration in `README.md`, `docs/feature-tour.md`, `docs/advanced-usage.md` (single-item backdrop runs), and `docs/TECHNICAL_NOTES.md` (developer-facing pipeline details).
  * New CLI flags for specifying target size and quality for individual image types, such as `--*-target-size` and `--*-jpeg-quality` (where * = backdrop or thumb) or `--profile-webp-quality`.

### Changed
* Jellyfin HEAD requests (`get_item_image_head`) now use the same retry/backoff policy as GET helpers but can be invoked without retry for fast verification; the backdrop delete/verify phase uses a no-retry HEAD to quickly confirm that index `0` is empty before uploading.
* Backdrop uploads now report partial failures correctly:
  * If any backdrop upload fails, the item is reported as a failure (return value `False` from the per-item backdrop normalizer).
  * Staged originals are retained on disk for manual inspection when uploads are incomplete, instead of being cleaned up unconditionally.

### Fixed
* Clarified behavior and fixed edge cases in the backdrop pipeline:
  * Staging now guards against unknown or invalid content-types and I/O issues when writing staged files, logging a clear error and aborting safely instead of crashing.
  * 404 handling for delete/verify is explicitly modeled as “image missing” only in the verification HEAD call, matching Jellyfin’s current behavior.

## 0.1.1
* Added automatic pre-flight Jellyfin connectivity check before processing, with clear logging when unreachable.
* Hardened connectivity checks: detect unauthorized/forbidden/503 responses and abort when Jellyfin reports it is shutting down during pre-flight or `--test-jf`.
* Switched Jellyfin auth to the MediaBrowser Authorization header (Token/Client/Version), removing legacy X-Emby-Token usage.
* Changed: logo/thumb discovery now uses `/Items` with configurable item types via `[modes].item_types`/`--item-types`. When `libraries.names` is set, libraries are resolved via `/Library/MediaFolders` and `/Items` is called per library; when no filters are set, `/Items` is called once without `ParentId` (recursive).
* Fixed logging behavior for better descriptive summary.
* Chore/ci setup by @alexkahler in https://github.com/alexkahler/Jellyfin-Image-Normalizer/pull/1
* fix: changed changelog order by @alexkahler in https://github.com/alexkahler/Jellyfin-Image-Normalizer/pull/2
* fix: correct python version in ci workflow by @alexkahler in https://github.com/alexkahler/Jellyfin-Image-Normalizer/pull/3
* fix/conftest by @alexkahler in https://github.com/alexkahler/Jellyfin-Image-Normalizer/pull/4
* fix: removed incorrect v.0.1.2 message by @alexkahler in https://github.com/alexkahler/Jellyfin-Image-Normalizer/pull/5

## 0.1.0
- Initial version
