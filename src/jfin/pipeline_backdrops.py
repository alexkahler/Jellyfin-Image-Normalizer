from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .client import JellyfinClient
from .config import ModeRuntimeSettings
from .discovery import DiscoveredItem


def normalize_item_backdrops_api(
    *,
    item: DiscoveredItem,
    settings_by_mode: dict[str, ModeRuntimeSettings],
    jf_client: JellyfinClient,
    dry_run: bool,
    force_upload_noscale: bool,  # Intentionally ignored for backdrops; we always reupload to preserve order.
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
    image_type_to_mode: dict[str, str],
    normalize_image_bytes_fn: Callable[..., tuple[Any, bytes, str]],
    guess_extension_from_content_type_fn: Callable[[str | None], str],
    get_staging_dir_fn: Callable[[Path, str], Path],
    cleanup_staging_dir_fn: Callable[[Path, str], None],
    state_module: Any,
) -> bool:
    """Normalize all backdrops for a single item using fetch-normalize-delete-upload phases."""
    _ = force_upload_noscale
    image_type = "Backdrop"
    mode = image_type_to_mode.get(image_type)
    if not mode:
        state_module.log.warning(
            "[WARN] Unsupported image type %s; skipping.", image_type
        )
        state_module.stats.record_warning()
        return False

    settings = settings_by_mode.get(mode)
    if settings is None:
        state_module.log.warning("[WARN] No settings for backdrop mode; skipping.")
        state_module.stats.record_warning()
        return False

    total = item.backdrop_count or 0
    if total == 0:
        state_module.log.info("Item %s has no backdrops; skipping.", item.id)
        state_module.stats.record_skip(count_processed=False)
        return False

    # Phase 1: Fetch & stage - fetch all originals to disk with original extensions.
    staging_dir = None
    if not dry_run:
        staging_dir = get_staging_dir_fn(backup_root, item.id)
    deletions_started = False

    def cleanup_staging_on_failure() -> None:
        if dry_run or deletions_started:
            return
        cleanup_staging_dir_fn(backup_root, item.id)

    staged_files: list[tuple[int, Path | None, str | None]] = []

    for src_index in range(total):
        label = f"{item.name} [{item.id}] backdrop #{src_index}"

        result = jf_client.get_item_image(
            item_id=item.id, image_type="Backdrop", index=src_index
        )
        if result is None:
            state_module.log.error(
                "[ERROR] Backdrop fetch failed at call %d for item %s; aborting before normalization.",
                src_index,
                item.id,
            )
            state_module.stats.record_error(label, "fetch failed")
            cleanup_staging_on_failure()
            return False

        data, content_type = result
        if not dry_run and staging_dir:
            try:
                ext = guess_extension_from_content_type_fn(content_type)
                staged_file_path = staging_dir / f"{src_index}{ext}"
                staged_file_path.write_bytes(data)
            except Exception as exc:
                state_module.log.error(
                    "[ERROR] Failed to stage backdrop index %d for item %s: %s",
                    src_index,
                    item.id,
                    exc,
                )
                state_module.stats.record_error(label, f"staging failed: {exc}")
                cleanup_staging_on_failure()
                return False

            staged_files.append((src_index, staged_file_path, content_type))
            state_module.log.debug(
                "  -> Staged backdrop index %d: %s",
                src_index,
                staged_file_path,
            )
        else:
            # In dry-run, keep in memory for phase 2.
            staged_files.append((src_index, None, content_type))

    if len(staged_files) != total:
        state_module.log.error(
            "[ERROR] Fetch phase failed: expected %d backdrops, got %d for item %s.",
            total,
            len(staged_files),
            item.id,
        )
        state_module.stats.record_error(
            item.id, f"Fetch failed: expected {total}, got {len(staged_files)}"
        )
        cleanup_staging_on_failure()
        return False

    # Phase 2: Normalize & prepare - normalize staged files to memory.
    normalized_payloads: list[tuple[int, bytes, str]] = []

    for src_index, staged_path_opt, original_content_type in staged_files:
        label = f"{item.name} [{item.id}] backdrop #{src_index}"

        if dry_run:
            state_module.log.debug(
                "[DRY-RUN] Would process backdrop index %d for item %s.",
                src_index,
                item.id,
            )
            state_module.stats.record_success()
            normalized_payloads.append(
                (src_index, b"", original_content_type or "application/octet-stream")
            )
            continue

        if staged_path_opt is None:
            state_module.log.error(
                "[ERROR] Missing staged file for backdrop index %d on item %s.",
                src_index,
                item.id,
            )
            state_module.stats.record_error(label, "staged file missing")
            cleanup_staging_on_failure()
            return False

        try:
            data = staged_path_opt.read_bytes()
        except Exception as exc:
            state_module.log.error(
                "[ERROR] Backdrop normalization failed at index %d for item %s: failed to read staged file: %s",
                src_index,
                item.id,
                exc,
            )
            state_module.stats.record_error(label, f"read staged file failed: {exc}")
            cleanup_staging_on_failure()
            return False

        try:
            _, normalized_bytes, normalized_content_type = normalize_image_bytes_fn(
                item_id=item.id,
                label=label,
                image_type=image_type,
                data=data,
                content_type=original_content_type,
                mode=mode,
                settings=settings,
                make_backup=make_backup,
                backup_root=backup_root,
                backup_mode=backup_mode,
                dry_run=False,
                backdrop_index=src_index,
            )
        except Exception as exc:
            state_module.log.exception(
                "[ERROR] Backdrop normalization failed at index %d for item %s",
                src_index,
                item.id,
            )
            state_module.stats.record_error(label, str(exc))
            cleanup_staging_on_failure()
            return False

        normalized_payloads.append((src_index, normalized_bytes, normalized_content_type))

    if len(normalized_payloads) != total:
        state_module.log.error(
            "[ERROR] Normalize phase failed: expected %d backdrops, got %d for item %s.",
            total,
            len(normalized_payloads),
            item.id,
        )
        state_module.stats.record_error(
            item.id,
            f"Normalize failed: expected {total}, got {len(normalized_payloads)}",
        )
        cleanup_staging_on_failure()
        return False

    # Phase 3: Delete - remove all originals from server.
    if dry_run:
        state_module.log.debug(
            "[DRY-RUN] Would delete %d original backdrops for item %s.",
            total,
            item.id,
        )
    else:
        deletions_started = True
        for _ in range(total):
            delete_ok = jf_client.delete_image(item.id, image_type, 0)
            if not delete_ok:
                state_module.log.error(
                    "[ERROR] Failed to delete original backdrop at index 0 for item %s; aborting without upload.",
                    item.id,
                )
                state_module.stats.record_error(item.id, "delete phase failed")
                return False

        verification = jf_client.get_item_image_head(
            item_id=item.id,
            image_type="Backdrop",
            index=0,
            retry=False,  # keep this fast and avoid retry backoff during verification
        )
        if verification is not None:
            state_module.log.error(
                "[ERROR] 404 verification failed for item %s; images still exist at index 0. Aborting upload phase.",
                item.id,
            )
            state_module.stats.record_error(item.id, "404 verification failed")
            return False

        state_module.log.debug(
            "  -> All %d original backdrops deleted and verified (404) for item %s.",
            total,
            item.id,
        )

    # Phase 4: Upload - upload normalized payloads to indices 0 to total-1.
    any_upload_failed = False
    if dry_run:
        state_module.log.debug(
            "[DRY-RUN] Would upload %d backdrops for item %s at indices 0 to %d.",
            total,
            item.id,
            total - 1,
        )
    else:
        for upload_index, (src_index, payload_bytes, content_type) in enumerate(
            normalized_payloads
        ):
            label = (
                f"{item.name} [{item.id}] backdrop #{src_index} -> upload index "
                f"{upload_index}"
            )

            upload_ok = jf_client.set_item_image_bytes(
                item_id=item.id,
                image_type=image_type,
                data=payload_bytes,
                content_type=content_type,
                backdrop_index=upload_index,
                failures=state_module.api_failures,
            )
            if not upload_ok:
                state_module.log.error(
                    "[ERROR] Failed to upload normalized backdrop at index %d for item %s.",
                    upload_index,
                    item.id,
                )
                state_module.stats.record_error(label, "upload failed")
                any_upload_failed = True
                continue

            state_module.stats.record_success()
            state_module.log.debug(
                "  -> Uploaded backdrop index %d for item %s.",
                upload_index,
                item.id,
            )

    # Phase 5: Cleanup & finalize.
    if not dry_run:
        if any_upload_failed:
            # Keep staged originals for manual inspection when uploads fail.
            state_module.log.error(
                "[ERROR] One or more backdrop uploads failed for item %s; retaining staged originals at %s.",
                item.id,
                staging_dir,
            )
        else:
            cleanup_staging_dir_fn(backup_root, item.id)

    if not dry_run and any_upload_failed:
        return False

    state_module.log.info("[SUCCESS] All backdrops processed for item %s.", item.id)
    return True
