# Changelog

## 0.1.1
* Added automatic pre-flight Jellyfin connectivity check before processing, with clear logging when unreachable.
* Hardened connectivity checks: detect unauthorized/forbidden/503 responses and abort when Jellyfin reports it is shutting down during pre-flight or `--test-jf`.
* Switched Jellyfin auth to the MediaBrowser Authorization header (Token/Client/Version), removing legacy X-Emby-Token usage.
* Changed: logo/thumb discovery now uses `/Items` with configurable item types via `[modes].item_types`/`--item-types`. When `libraries.names` is set, libraries are resolved via `/Library/MediaFolders` and `/Items` is called per library; when no filters are set, `/Items` is called once without `ParentId` (recursive).
* Fixed logging behavior for better descriptive summary.
* Chore/ci setup by @alexkahler in https://github.com/alexkahler/Jellyfin-Image-Normalizer/pull/1

## 0.1.0
- Initial version