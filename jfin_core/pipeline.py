from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from PIL import Image

from . import state
from .backup import (
    cleanup_staging_dir,
    get_staging_dir,
    guess_extension_from_content_type,
    save_backup,
    should_backup_for_plan,
)
from .client import JellyfinClient
from .config import ModeRuntimeSettings, build_discovery_settings
from .constants import IMAGE_TYPE_TO_MODE, MODE_TO_IMAGE_TYPE
from .discovery import (
    DiscoveredItem,
    find_user_by_name,
    profile_display_name,
    discover_all_library_items,
    discover_libraries,
)
from .imaging import (
    ScalePlan,
    apply_exif_orientation,
    build_normalized_image,
    encode_image_to_bytes,
    get_palette_color_count,
    handle_no_scale,
    log_processing_summary,
    make_scale_plan,
    remove_padding_from_logo,
    record_scale_decision,
)


def _plan_and_backup_image(
    *,
    img: Image.Image,
    label: str,
    fit_mode: str,
    settings: ModeRuntimeSettings,
    item_id: str,
    image_type: str,
    raw_bytes: bytes,
    content_type: str | None,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
    dry_run: bool,
    backdrop_index: int | None = None,
) -> ScalePlan:
    """
    Compute the resize plan, persist backups when applicable, and log the processing summary.
    """
    plan = make_scale_plan(
        img=img,
        target_w=settings.target_width,
        target_h=settings.target_height,
        fit_mode=fit_mode,
        allow_upscale=settings.allow_upscale,
        allow_downscale=settings.allow_downscale,
        pad_to_canvas=bool(fit_mode == "fit" and settings.logo_padding == "add"),
    )

    if make_backup and not dry_run and should_backup_for_plan(plan.decision, backup_mode):
        save_backup(
            backup_root=backup_root,
            item_id=item_id,
            image_type=image_type,
            data=raw_bytes,
            content_type=content_type,
            overwrite_existing=True,
            backdrop_index=backdrop_index,
        )

    record_scale_decision(label, plan)
    output_w = settings.target_width
    output_h = settings.target_height
    if plan.is_no_scale:
        output_w, output_h = img.size
    elif fit_mode == "fit" and settings.logo_padding != "add":
        output_w = plan.new_width
        output_h = plan.new_height

    log_processing_summary(
        label,
        plan,
        settings.target_width,
        settings.target_height,
        output_w,
        output_h,
        img.mode,
        img.format,
    )
    return plan


def _normalize_image_bytes(
    *,
    item_id: str,
    label: str,
    image_type: str,
    data: bytes,
    content_type: str | None,
    mode: str,
    settings: ModeRuntimeSettings,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
    dry_run: bool,
    backdrop_index: int | None = None,
) -> tuple[ScalePlan, bytes, str]:
    """
    Return the normalized payload bytes, normalized content-type, and scale plan for a single image.
    """
    def has_pixels_above_alpha_threshold(
        src: Image.Image, sensitivity: float
    ) -> bool:
        rgba = src if src.mode == "RGBA" else src.convert("RGBA")
        alpha = rgba.getchannel("A")
        mask = alpha.point([255 if a > sensitivity else 0 for a in range(256)])
        return mask.getbbox() is not None

    with Image.open(io.BytesIO(data)) as img:
        img = apply_exif_orientation(img)
        orig_mode = img.mode
        fit_mode = "fit" if mode == "logo" else "cover"

        orig_color_count = (
            get_palette_color_count(img)
            if (mode == "logo" and orig_mode == "P")
            else None
        )

        cropped = False
        if mode == "logo" and settings.logo_padding == "remove":
            sensitivity = settings.logo_padding_remove_sensitivity
            fully_transparent = not has_pixels_above_alpha_threshold(
                img, sensitivity
            )
            before_size = img.size
            img, cropped = remove_padding_from_logo(img, sensitivity)

            if fully_transparent:
                state.log.warning(
                    "[WARN] Logo padding removal skipped: image is fully "
                    "transparent at sensitivity=%s.",
                    sensitivity,
                )
                state.stats.record_warning()
            elif (not cropped) and img.size == before_size and img.size == (
                settings.target_width,
                settings.target_height,
            ):
                state.log.warning(
                    "[WARN] Logo padding removal may have failed: image "
                    "remained at target size after crop; borders may contain "
                    "non-obvious pixels."
                )
                state.stats.record_warning()

        plan = _plan_and_backup_image(
            img=img,
            label=label,
            fit_mode=fit_mode,
            settings=settings,
            item_id=item_id,
            image_type=image_type,
            raw_bytes=data,
            content_type=content_type,
            make_backup=make_backup,
            backup_root=backup_root,
            backup_mode=backup_mode,
            dry_run=dry_run,
            backdrop_index=backdrop_index,
        )

        if plan.is_no_scale and not cropped:
            # Skip normalization/encoding when no scaling is needed or allowed.
            return (
                plan,
                data,
                content_type or "application/octet-stream",
            )

        normalized_img, normalized_content_type, fmt = build_normalized_image(
            img=img,
            mode=mode,
            target_width=settings.target_width,
            target_height=settings.target_height,
            new_width=plan.new_width,
            new_height=plan.new_height,
            orig_mode=orig_mode,
            orig_color_count=orig_color_count,
            logo_padding=settings.logo_padding,
        )
        payload = encode_image_to_bytes(
            normalized_img=normalized_img,
            fmt=fmt,
            jpeg_quality=settings.jpeg_quality,
            webp_quality=settings.webp_quality,
        )

    return plan, payload, normalized_content_type


def _process_item_image_payload(
    *,
    item_id: str,
    label: str,
    image_type: str,
    data: bytes,
    content_type: str | None,
    mode: str,
    settings: ModeRuntimeSettings,
    jf_client: JellyfinClient,
    dry_run: bool,
    force_upload_noscale: bool,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
    backdrop_index: int | None = None,
) -> bool:
    """
    Shared processing for a single image payload (item image or backdrop).
    Returns True on success, False on failure.
    """
    try:
        plan, payload, normalized_content_type = _normalize_image_bytes(
            item_id=item_id,
            label=label,
            image_type=image_type,
            data=data,
            content_type=content_type,
            mode=mode,
            settings=settings,
            make_backup=make_backup,
            backup_root=backup_root,
            backup_mode=backup_mode,
            dry_run=dry_run,
            backdrop_index=backdrop_index,
        )

        def upload_original() -> tuple[bool, str | None]:
            before_failures = len(state.api_failures)
            upload_ok = jf_client.set_item_image_bytes(
                item_id=item_id,
                image_type=image_type,
                data=data,
                content_type=content_type or "application/octet-stream",
                backdrop_index=backdrop_index,
                failures=state.api_failures,
            )
            return upload_ok, state.latest_api_error(before_failures)

        if mode == "backdrop":
            # For backdrops we always want a final asset, so do not skip uploads.
            skip_when_no_scale = False
        else:
            skip_when_no_scale = bool(mode in ("logo", "thumb") and not force_upload_noscale)

        no_scale_result = handle_no_scale(
            plan=plan,
            dry_run=dry_run,
            force_upload=force_upload_noscale,
            upload_fn=upload_original,
            record_label=label,
            default_error="API upload failed for NO_SCALE image",
            stats=state.stats,
            skip_when_no_scale=skip_when_no_scale,
        )
        if no_scale_result is not None:
            return no_scale_result

        if dry_run:
            state.stats.record_success()
            return True

        before_failures = len(state.api_failures)
        upload_ok = jf_client.set_item_image_bytes(
            item_id=item_id,
            image_type=image_type,
            data=payload,
            content_type=normalized_content_type,
            backdrop_index=backdrop_index,
            failures=state.api_failures,
        )
        if upload_ok:
            state.stats.record_success()
            return True

        upload_error = state.latest_api_error(before_failures)
        state.stats.record_error(label, upload_error or "API upload failed")
        return False

    except Exception as e:
        state.log.exception("[ERROR] Failed to process %s", label)
        state.stats.record_error(label, str(e))
        return False


def normalize_item_image_api(
    *,
    item: DiscoveredItem,
    image_type: str,
    settings_by_mode: dict[str, ModeRuntimeSettings],
    jf_client: JellyfinClient,
    dry_run: bool,
    force_upload_noscale: bool,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
) -> bool:
    """Fetch, normalize, and upload (when enabled) one item image, delegating backdrops to their dedicated helper."""
    if image_type == "Backdrop":
        # Multi-image type; handled by dedicated helper.
        return normalize_item_backdrops_api(
            item=item,
            settings_by_mode=settings_by_mode,
            jf_client=jf_client,
            dry_run=dry_run,
            force_upload_noscale=force_upload_noscale,
            make_backup=make_backup,
            backup_root=backup_root,
            backup_mode=backup_mode,
        )
    
    mode = IMAGE_TYPE_TO_MODE.get(image_type)
    if not mode:
        state.log.warning("[WARN] Unsupported image type %s; skipping.", image_type)
        state.stats.record_warning()
        return False
    
    settings = settings_by_mode.get(mode)
    if settings is None:
        state.log.warning("[WARN] No settings for mode '%s'; skipping %s.", mode, image_type)
        state.stats.record_warning()
        return False

    label = f"{item.name} ({item.type}) [{image_type}]"
    image_payload = jf_client.get_item_image(item.id, image_type)
    if image_payload is None:
        state.stats.record_error(label, "Failed to fetch image bytes")
        return False

    data, content_type = image_payload
    return _process_item_image_payload(
        item_id=item.id,
        label=label,
        image_type=image_type,
        data=data,
        content_type=content_type,
        mode=mode,
        settings=settings,
        jf_client=jf_client,
        dry_run=dry_run,
        force_upload_noscale=force_upload_noscale,
        make_backup=make_backup,
        backup_root=backup_root,
        backup_mode=backup_mode,
    )


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
) -> bool:
    """Normalize all backdrops for a single item using fetch-normalize-delete-upload phases."""
    image_type = "Backdrop"
    mode = IMAGE_TYPE_TO_MODE.get(image_type)
    if not mode:
        state.log.warning("[WARN] Unsupported image type %s; skipping.", image_type)
        state.stats.record_warning()
        return False

    settings = settings_by_mode.get(mode)
    if settings is None:
        state.log.warning("[WARN] No settings for backdrop mode; skipping.")
        state.stats.record_warning()
        return False

    total = item.backdrop_count or 0
    
    if total == 0:
        state.log.info("Item %s has no backdrops; skipping.", item.id)
        state.stats.record_skip(count_processed=False)
        return False

    # Phase 1: Fetch & stage - fetch all originals to disk with original extensions
    staging_dir = None
    if not dry_run:
        staging_dir = get_staging_dir(backup_root, item.id)
    deletions_started = False

    def cleanup_staging_on_failure() -> None:
        if dry_run or deletions_started:
            return
        cleanup_staging_dir(backup_root, item.id)
    
    staged_files: list[tuple[int, Path | None, str]] = []  # (index, file_path, content_type)
    
    for src_index in range(total):
        label = f"{item.name} [{item.id}] backdrop #{src_index}"
        
        result = jf_client.get_item_image(item_id=item.id, image_type="Backdrop", index=src_index)
        if result is None:
            state.log.error("[ERROR] Backdrop fetch failed at call %d for item %s; aborting before normalization.", src_index, item.id)
            state.stats.record_error(label, "fetch failed")
            cleanup_staging_on_failure()
            return False
        
        data, content_type = result

        # Stage the file with original extension
        if not dry_run and staging_dir:
            try:
                ext = guess_extension_from_content_type(content_type)
                staged_path = staging_dir / f"{src_index}{ext}"
                staged_path.write_bytes(data)
            except Exception as exc:
                state.log.error(
                    "[ERROR] Failed to stage backdrop index %d for item %s: %s",
                    src_index,
                    item.id,
                    exc,
                )
                state.stats.record_error(label, f"staging failed: {exc}")
                cleanup_staging_on_failure()
                return False

            staged_files.append((src_index, staged_path, content_type))
            state.log.debug(
                "  -> Staged backdrop index %d: %s",
                src_index,
                staged_path,
            )
        else:
            # In dry-run, keep in memory for phase 2
            staged_files.append((src_index, None, content_type))
    
    if len(staged_files) != total:
        state.log.error("[ERROR] Fetch phase failed: expected %d backdrops, got %d for item %s.", total, len(staged_files), item.id)
        state.stats.record_error(item.id, f"Fetch failed: expected {total}, got {len(staged_files)}")
        cleanup_staging_on_failure()
        return False
    
    # Phase 2: Normalize & prepare - normalize staged files to memory
    normalized_payloads: list[tuple[int, bytes, str]] = []  # (index, payload_bytes, content_type)
    
    for src_index, staged_path, original_content_type in staged_files:
        label = f"{item.name} [{item.id}] backdrop #{src_index}"

        if dry_run:
            state.log.debug(
                "[DRY-RUN] Would process backdrop index %d for item %s.",
                src_index,
                item.id,
            )
            state.stats.record_success()
            normalized_payloads.append((src_index, b"", original_content_type or "application/octet-stream"))
            continue

        if staged_path is None:
            state.log.error("[ERROR] Missing staged file for backdrop index %d on item %s.", src_index, item.id)
            state.stats.record_error(label, "staged file missing")
            cleanup_staging_on_failure()
            return False

        try:
            data = staged_path.read_bytes()
        except Exception as e:
            state.log.error("[ERROR] Backdrop normalization failed at index %d for item %s: failed to read staged file: %s", src_index, item.id, e)
            state.stats.record_error(label, f"read staged file failed: {e}")
            cleanup_staging_on_failure()
            return False

        try:
            _, normalized_bytes, normalized_content_type = _normalize_image_bytes(
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
            state.log.exception("[ERROR] Backdrop normalization failed at index %d for item %s", src_index, item.id)
            state.stats.record_error(label, str(exc))
            cleanup_staging_on_failure()
            return False

        normalized_payloads.append((src_index, normalized_bytes, normalized_content_type))
    
    if len(normalized_payloads) != total:
        state.log.error("[ERROR] Normalize phase failed: expected %d backdrops, got %d for item %s.", total, len(normalized_payloads), item.id)
        state.stats.record_error(item.id, f"Normalize failed: expected {total}, got {len(normalized_payloads)}")
        cleanup_staging_on_failure()
        return False
    
    # Phase 3: Delete - remove all originals from server
    if dry_run:
        state.log.debug(
            "[DRY-RUN] Would delete %d original backdrops for item %s.",
            total,
            item.id,
        )
    else:
        deletions_started = True
        for _ in range(total):
            delete_ok = jf_client.delete_image(item.id, image_type, 0)
            if not delete_ok:
                state.log.error("[ERROR] Failed to delete original backdrop at index 0 for item %s; aborting without upload.", item.id)
                state.stats.record_error(item.id, "delete phase failed")
                return False
        
        # Verify all originals deleted via 404 check
        verification = jf_client.get_item_image_head(
            item_id=item.id,
            image_type="Backdrop",
            index=0,
            retry=False,  # keep this fast and avoid retry backoff during verification
        )
        if verification is not None:
            state.log.error("[ERROR] 404 verification failed for item %s; images still exist at index 0. Aborting upload phase.", item.id)
            state.stats.record_error(item.id, "404 verification failed")
            return False
        
        state.log.debug("  -> All %d original backdrops deleted and verified (404) for item %s.", total, item.id)
    
    # Phase 4: Upload - upload normalized payloads to indices 0 to total-1
    any_upload_failed = False
    if dry_run:
        state.log.debug(
            "[DRY-RUN] Would upload %d backdrops for item %s at indices 0 to %d.",
            total,
            item.id,
            total - 1,
        )
    else:
        for upload_index, (src_index, payload_bytes, content_type) in enumerate(normalized_payloads):
            label = f"{item.name} [{item.id}] backdrop #{src_index} -> upload index {upload_index}"

            upload_ok = jf_client.set_item_image_bytes(
                item_id=item.id,
                image_type=image_type,
                data=payload_bytes,
                content_type=content_type,
                backdrop_index=upload_index,
                failures=state.api_failures,
            )
            if not upload_ok:
                state.log.error(
                    "[ERROR] Failed to upload normalized backdrop at index %d for item %s.",
                    upload_index,
                    item.id,
                )
                state.stats.record_error(label, "upload failed")
                any_upload_failed = True
                # Do not abort; try to upload remaining backdrops
                continue

            state.stats.record_success()
            state.log.debug(
                "  -> Uploaded backdrop index %d for item %s.",
                upload_index,
                item.id,
            )

    # Phase 5: Cleanup & finalize
    if not dry_run:
        if any_upload_failed:
            # Keep staged originals for manual inspection when uploads fail.
            state.log.error(
                "[ERROR] One or more backdrop uploads failed for item %s; retaining staged originals at %s.",
                item.id,
                staging_dir,
            )
        else:
            cleanup_staging_dir(backup_root, item.id)

    if not dry_run and any_upload_failed:
        return False

    state.log.info("[SUCCESS] All backdrops processed for item %s.", item.id)
    return True


def process_discovered_items(
    *,
    items: list[DiscoveredItem],
    settings_by_mode: dict[str, ModeRuntimeSettings],
    jf_client: JellyfinClient,
    dry_run: bool,
    force_upload_noscale: bool,
    enabled_image_types: list[str],
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
) -> None:
    """Iterate discovered items and normalize the enabled image types via API calls, tracking progress stats."""
    enabled_set = set(enabled_image_types)
    
    total_images = 0
    for item in items:
        for image_type in (item.image_types & enabled_set):
            if image_type == "Backdrop":
                total_images += (item.backdrop_count or 1)
            else:
                total_images += 1
    
    processed_images = 0

    state.stats.record_images_found(total_images)

    if total_images == 0:
        state.log.info("No item images matched the requested types.")
        return

    for item in items:
        if not (item.image_types & enabled_set):
            continue
        state.stats.record_item_processed(item.id)
        for image_type in sorted(item.image_types):
            if image_type not in enabled_set:
                continue
            increment = (item.backdrop_count or 1) if image_type == "Backdrop" else 1
            normalize_item_image_api(
                item=item,
                image_type=image_type,
                settings_by_mode=settings_by_mode,
                jf_client=jf_client,
                dry_run=dry_run,
                force_upload_noscale=force_upload_noscale,
                make_backup=make_backup,
                backup_root=backup_root,
                backup_mode=backup_mode,
            )
            processed_images += increment
            if processed_images % 25 == 0 or processed_images == total_images:
                state.log.info(
                    "Progress: %s/%s images processed via API.",
                    processed_images,
                    total_images,
                )


def process_libraries_via_api(
    *,
    cfg: dict[str, Any],
    operations: list[str],
    mode_settings: dict[str, ModeRuntimeSettings],
    jf_client: JellyfinClient,
    dry_run: bool,
    force_upload_noscale: bool,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
) -> None:
    """Discover libraries/items for the selected operations and process their images through the API workflow."""
    discovery = build_discovery_settings(cfg, operations)
    enabled_image_types = [
        image_type
        for image_type in discovery.enable_image_types
        if IMAGE_TYPE_TO_MODE.get(image_type) in operations
    ]
    if not enabled_image_types:
        state.log.info(
            "No image types enabled for operations %s; skipping library processing.",
            operations,
        )
        return

    libraries = discover_libraries(jf_client, discovery)
    if discovery.library_names and not libraries:
        state.log.warning("No libraries matched filters; nothing to do.")
        return

    items = discover_all_library_items(jf_client, libraries, discovery)
    if not items:
        state.log.info("No items found with requested images in selected libraries.")
        return

    state.log.info(
        "Processing %s items across %s libraries for image types: %s",
        len(items),
        len(libraries) if libraries else "all",
        ", ".join(enabled_image_types),
    )
    process_discovered_items(
        items=items,
        settings_by_mode=mode_settings,
        jf_client=jf_client,
        dry_run=dry_run,
        force_upload_noscale=force_upload_noscale,
        enabled_image_types=enabled_image_types,
        make_backup=make_backup,
        backup_root=backup_root,
        backup_mode=backup_mode,
    )


def normalize_profile_user(
    user: dict[str, Any],
    settings: ModeRuntimeSettings,
    dry_run: bool,
    jf_client: JellyfinClient,
    force_upload_noscale: bool,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
) -> bool:
    """Normalize a single Jellyfin user profile image via the API, updating stats and logging errors."""
    user_id = user.get("Id")
    if not user_id:
        state.log.warning("[API-SKIP] Missing user Id in user record, skipping.")
        state.stats.record_warning(count_processed=True)
        return False

    user_label = profile_display_name(user)

    if not user.get("PrimaryImageTag"):
        state.log.info("[SKIP] %s has no PrimaryImageTag; skipping profile image.", user_label)
        state.stats.record_skip(count_processed=True)
        return False

    image_response = jf_client.get_user_image(user_id)
    if image_response is None:
        state.log.error("[API-SKIP] Could not fetch profile image for %s", user_label)
        state.stats.record_error(user_label, "Could not fetch profile image")
        return False

    data, content_type = image_response

    try:
        with Image.open(io.BytesIO(data)) as img:
            img = apply_exif_orientation(img)
            orig_mode = img.mode

            plan = _plan_and_backup_image(
                img=img,
                label=user_label,
                fit_mode="cover",
                settings=settings,
                item_id=user_id,
                image_type="Primary",
                raw_bytes=data,
                content_type=content_type,
                make_backup=make_backup,
                backup_root=backup_root,
                backup_mode=backup_mode,
                dry_run=dry_run,
            )

            def upload_original_profile() -> tuple[bool, str | None]:
                before_failures = len(state.api_failures)
                upload_ok = jf_client.set_user_profile_image(
                    user_id=user_id,
                    data=data,
                    content_type=content_type or "application/octet-stream",
                    failures=state.api_failures,
                )
                return upload_ok, state.latest_api_error(before_failures)

            no_scale_result = handle_no_scale(
                plan=plan,
                dry_run=dry_run,
                force_upload=force_upload_noscale,
                upload_fn=upload_original_profile,
                record_label=user_label,
                default_error="API upload failed for NO_SCALE profile image",
                stats=state.stats,
            )
            if no_scale_result is not None:
                return no_scale_result

            if dry_run:
                state.stats.record_success()
                return True

            normalized_img, normalized_content_type, fmt = build_normalized_image(
                img=img,
                mode="profile",
                target_width=settings.target_width,
                target_height=settings.target_height,
                new_width=plan.new_width,
                new_height=plan.new_height,
                orig_mode=orig_mode,
                orig_color_count=None,
            )
            payload = encode_image_to_bytes(
                normalized_img=normalized_img,
                fmt=fmt,
                jpeg_quality=85,
                webp_quality=settings.webp_quality,
            )

            before_failures = len(state.api_failures)
            upload_ok = jf_client.set_user_profile_image(
                user_id=user_id,
                data=payload,
                content_type=normalized_content_type,
                failures=state.api_failures,
            )
            if upload_ok:
                state.stats.record_success()
                return True

            upload_error = state.latest_api_error(before_failures)
            state.stats.record_error(
                user_label,
                upload_error or "API upload failed for profile image",
            )
            return False

    except Exception as e:
        state.log.exception("[ERROR] Failed to process profile for %s", user_label)
        state.stats.record_error(user_label, str(e))
        return False


def process_profiles(
    *,
    settings: ModeRuntimeSettings,
    dry_run: bool,
    jf_client: JellyfinClient,
    force_upload_noscale: bool,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
) -> None:
    """Normalize profile images for all active users by delegating to normalize_profile_user."""
    users = jf_client.list_users(is_disabled=False)
    if not users:
        state.log.warning("[WARN] No active users returned from Jellyfin; skipping profile processing.")
        state.stats.record_warning()
        return
    available_profiles = sum(1 for user in users if user.get("PrimaryImageTag"))
    state.stats.record_images_found(available_profiles)

    for user in users:
        normalize_profile_user(
            user=user,
            settings=settings,
            dry_run=dry_run,
            jf_client=jf_client,
            force_upload_noscale=force_upload_noscale,
            make_backup=make_backup,
            backup_root=backup_root,
            backup_mode=backup_mode,
        )


def process_single_item_api(
    *,
    item_id: str,
    mode: str,
    settings_by_mode: dict[str, ModeRuntimeSettings],
    jf_client: JellyfinClient,
    dry_run: bool,
    force_upload_noscale: bool,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
) -> bool:
    """Process a single item by id without library discovery."""
    image_type = MODE_TO_IMAGE_TYPE.get(mode)
    if not image_type:
        state.log.critical("Unsupported mode '%s' for --single item processing.", mode)
        state.stats.record_error("single", f"Unsupported mode {mode}")
        raise SystemExit(1)

    state.stats.record_item_processed(item_id)

    raw: dict[str, Any] | None = None
    backdrop_count: int | None = None
    if image_type == "Backdrop":
        from jfin_core.discovery import _item_backdrop_count

        raw = jf_client.get_item(item_id)
        if raw is None:
            state.log.critical(
                "Failed to fetch item %s for single-backdrop mode.",
                item_id,
            )
            state.stats.record_error("single", "item fetch failed")
            return False

        backdrop_count = _item_backdrop_count(raw)
        if backdrop_count == 0:
            state.log.info("Item %s has no backdrops; nothing to do.", item_id)
            state.stats.record_skip(count_processed=False)
            return False

    dummy_item = DiscoveredItem(
        id=item_id,
        name=(raw.get("Name", item_id) if raw else item_id),
        type=(raw.get("Type", "Item") if raw else "Item"),
        parent_id=(raw.get("ParentId") if raw else None),
        library_id=None,
        library_name=None,
        backdrop_count=backdrop_count,
        image_types={image_type},
    )
    
    state.stats.record_images_found(backdrop_count or 1)
    state.log.info("Processing single item %s as %s", item_id, mode)
    return normalize_item_image_api(
        item=dummy_item,
        image_type=image_type,
        settings_by_mode=settings_by_mode,
        jf_client=jf_client,
        dry_run=dry_run,
        force_upload_noscale=force_upload_noscale,
        make_backup=make_backup,
        backup_root=backup_root,
        backup_mode=backup_mode,
    )


def process_single_profile(
    *,
    username: str,
    settings: ModeRuntimeSettings,
    dry_run: bool,
    jf_client: JellyfinClient | None,
    force_upload_noscale: bool,
    is_restore: bool,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
) -> None:
    """Handle normalization for a single profile by username, aborting cleanly on missing data or restore requests."""
    if is_restore:
        state.log.warning("Restore is not supported for profile images; skipping.")
        state.stats.record_warning()
        raise SystemExit(1)

    if jf_client is None:
        state.log.critical("Jellyfin client is required for profile images.")
        state.stats.record_error("profile", "Missing Jellyfin client")
        raise SystemExit(1)

    users = jf_client.list_users(is_disabled=False)
    user = find_user_by_name(users, username)
    if user is None:
        state.log.critical("User '%s' not found or disabled.", username)
        state.stats.record_error(username, "User not found or disabled")
        raise SystemExit(1)

    if not user.get("PrimaryImageTag"):
        state.log.info("[SKIP] User '%s' has no profile image to normalize.", username)
        state.stats.record_skip(count_processed=True)
        raise SystemExit(0 if dry_run else 1)

    state.stats.record_images_found(1)
    state.log.info(
        "Processing profile for user '%s' - Target: %sx%s, Dry-run=%s",
        username,
        settings.target_width,
        settings.target_height,
        dry_run,
    )
    normalize_profile_user(
        user=user,
        settings=settings,
        dry_run=dry_run,
        jf_client=jf_client,
        force_upload_noscale=force_upload_noscale,
        make_backup=make_backup,
        backup_root=backup_root,
        backup_mode=backup_mode,
    )
