from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any

from PIL import Image

from . import state
from .backup import (
    content_type_from_extension,
    image_type_from_filename,
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
    resolve_operator_user,
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
    )

    if make_backup and should_backup_for_plan(plan.decision, backup_mode):
        save_backup(
            backup_root=backup_root,
            item_id=item_id,
            image_type=image_type,
            data=raw_bytes,
            content_type=content_type,
            overwrite_existing=True,
        )

    record_scale_decision(label, plan)
    log_processing_summary(
        label,
        plan,
        settings.target_width,
        settings.target_height,
        img.mode,
        img.format,
    )
    return plan


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

    try:
        with Image.open(io.BytesIO(data)) as img:
            img = apply_exif_orientation(img)
            orig_mode = img.mode
            fit_mode = "fit" if mode == "logo" else "cover"

            plan = _plan_and_backup_image(
                img=img,
                label=label,
                fit_mode=fit_mode,
                settings=settings,
                item_id=item.id,
                image_type=image_type,
                raw_bytes=data,
                content_type=content_type,
                make_backup=make_backup,
                backup_root=backup_root,
                backup_mode=backup_mode,
            )

            def upload_original() -> tuple[bool, str | None]:
                before_failures = len(state.api_failures)
                upload_ok = jf_client.set_item_image_bytes(
                    item.id,
                    image_type,
                    data,
                    content_type or "application/octet-stream",
                    failures=state.api_failures,
                )
                return upload_ok, state.latest_api_error(before_failures)

            no_scale_result = handle_no_scale(
                plan=plan,
                dry_run=dry_run,
                force_upload=force_upload_noscale,
                upload_fn=upload_original,
                record_label=label,
                default_error="API upload failed for NO_SCALE image",
                stats=state.stats,
            )
            if no_scale_result is not None:
                return no_scale_result

            if dry_run:
                state.stats.record_success()
                return True

            orig_color_count = (
                get_palette_color_count(img) if (mode == "logo" and orig_mode == "P") else None
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
                no_padding=settings.no_padding,
            )
            payload = encode_image_to_bytes(
                normalized_img=normalized_img,
                fmt=fmt,
                jpeg_quality=settings.jpeg_quality,
                webp_quality=settings.webp_quality,
            )

            before_failures = len(state.api_failures)
            upload_ok = jf_client.set_item_image_bytes(
                item.id,
                image_type,
                payload,
                normalized_content_type,
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
    enabled_set = set(enabled_image_types)
    total_images = sum(len(item.image_types & enabled_set) for item in items)
    processed_images = 0

    if total_images == 0:
        state.log.info("No item images matched the requested types.")
        return

    for item in items:
        for image_type in sorted(item.image_types):
            if image_type not in enabled_set:
                continue
            processed_images += 1
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
            if processed_images % 25 == 0 or processed_images == total_images:
                state.log.info(
                    "Progress: %s/%s images processed via API.",
                    processed_images,
                    total_images,
                )


def _locate_backup_file(backup_root: Path, target_id: str, image_type: str) -> Path | None:
    """
    Locate a backup file for a specific target id and image type, if present.

    Searches under <backup_root>/<first2>/<target_id>/ for filenames that map to the given Jellyfin image_type
    using the configured FILENAME_CONFIG mapping. Returns None when the directory or matching file is missing.
    """
    target_dir = backup_root / target_id[:2] / target_id
    if not target_dir.exists():
        return None

    for child in target_dir.iterdir():
        if child.is_file() and image_type_from_filename(child.name) == image_type:
            return child
    return None


def restore_from_backups(
    *,
    backup_root: Path,
    jf_client: JellyfinClient,
    operations: list[str],
    dry_run: bool,
) -> None:
    if not backup_root.exists():
        state.log.critical("Backup directory does not exist: %s", backup_root)
        state.stats.record_error("restore", "Backup directory missing")
        raise SystemExit(1)

    operation_set = set(operations)
    restored = 0

    for dirpath, _, filenames in os.walk(backup_root):
        for fname in filenames:
            image_type = image_type_from_filename(fname)
            if not image_type:
                continue
            mode = IMAGE_TYPE_TO_MODE.get(image_type)
            if mode not in operation_set:
                continue

            path = Path(dirpath) / fname
            item_id = path.parent.name
            if len(item_id) < 2:
                continue

            try:
                data = path.read_bytes()
            except Exception as e:
                state.log.error("Failed to read backup %s: %s", path, e)
                state.stats.record_error(str(path), f"read failed: {e}")
                continue

            if dry_run:
                state.log.info("DRY RUN - Would restore backup %s for %s", path, item_id)
                state.stats.record_success()
                restored += 1
                continue

            content_type = content_type_from_extension(path.suffix)
            before_failures = len(state.api_failures)

            if mode == "profile":
                upload_ok = jf_client.set_user_profile_image(
                    user_id=item_id,
                    data=data,
                    content_type=content_type,
                    failures=state.api_failures,
                )
            else:
                upload_ok = jf_client.set_item_image_bytes(
                    item_id=item_id,
                    image_type=image_type,
                    data=data,
                    content_type=content_type,
                    failures=state.api_failures,
                )

            upload_error = state.latest_api_error(before_failures)
            if upload_ok:
                restored += 1
                state.log.info("[RESTORE] Uploaded backup %s for %s", path, item_id)
                state.stats.record_success()
            else:
                state.stats.record_error(str(path), upload_error or "restore upload failed")

    state.log.info("Restore completed. Uploaded %s backup images.", restored)


def restore_single_from_backup(
    *,
    backup_root: Path,
    jf_client: JellyfinClient,
    mode: str,
    target_id: str,
    dry_run: bool,
) -> bool:
    """
    Restore a single asset (logo, thumb, or profile) from the backup directory.

    The caller supplies a target Jellyfin id and the normalization mode; the function resolves the backup file,
    infers content-type from the file extension, and either uploads it or logs a dry-run message. Upload failures
    are recorded in state.api_failures and RunStats for visibility to the caller.
    """
    image_type = MODE_TO_IMAGE_TYPE.get(mode)
    if not image_type:
        state.log.critical("Unsupported mode '%s' for restore.", mode)
        state.stats.record_error("restore", f"unsupported mode {mode}")
        return False

    backup_file = _locate_backup_file(backup_root, target_id, image_type)
    if backup_file is None:
        state.log.error("No backup found for %s (mode=%s).", target_id, mode)
        state.stats.record_error(target_id, "Backup not found")
        return False

    try:
        data = backup_file.read_bytes()
    except Exception as exc:
        state.log.error("Failed to read backup %s: %s", backup_file, exc)
        state.stats.record_error(str(backup_file), f"read failed: {exc}")
        return False

    if dry_run:
        state.log.info("DRY RUN - Would restore %s for %s from %s", image_type, target_id, backup_file)
        state.stats.record_success()
        return True

    content_type = content_type_from_extension(backup_file.suffix)
    before_failures = len(state.api_failures)
    if mode == "profile":
        upload_ok = jf_client.set_user_profile_image(
            user_id=target_id,
            data=data,
            content_type=content_type,
            failures=state.api_failures,
        )
    else:
        upload_ok = jf_client.set_item_image_bytes(
            item_id=target_id,
            image_type=image_type,
            data=data,
            content_type=content_type,
            failures=state.api_failures,
        )

    upload_error = state.latest_api_error(before_failures)
    if upload_ok:
        state.log.info("[RESTORE] Uploaded backup %s for %s", backup_file, target_id)
        state.stats.record_success()
        return True

    state.stats.record_error(str(backup_file), upload_error or "restore upload failed")
    return False


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

    operator_user = resolve_operator_user(jf_client, discovery)
    user_id = operator_user.get("Id")
    if not user_id:
        state.log.critical("Resolved operator user has no Id; cannot continue.")
        state.stats.record_error("discovery", "Resolved operator user missing Id")
        raise SystemExit(1)

    libraries = discover_libraries(jf_client, user_id, discovery)
    if not libraries:
        state.log.warning("No libraries matched filters; nothing to do.")
        return

    items = discover_all_library_items(jf_client, user_id, libraries, discovery)
    if not items:
        state.log.info("No items found with requested images in selected libraries.")
        return

    state.log.info(
        "Processing %s items across %s libraries for image types: %s",
        len(items),
        len(libraries),
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
    user_id = user.get("Id")
    if not user_id:
        state.log.warning("[API-SKIP] Missing user Id in user record, skipping.")
        state.stats.record_warning(count_processed=True)
        return False

    user_label = profile_display_name(user)

    if not user.get("PrimaryImageTag"):
        state.log.info("[SKIP] %s has no PrimaryImageTag; skipping profile image.", user_label)
        state.stats.record_warning(count_processed=True)
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
    users = jf_client.list_users(is_disabled=False)
    if not users:
        state.log.warning("[WARN] No active users returned from Jellyfin; skipping profile processing.")
        state.stats.record_warning()
        return

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

    dummy_item = DiscoveredItem(
        id=item_id,
        name=item_id,
        type="Item",
        parent_id=None,
        library_id=None,
        library_name=None,
        image_types={image_type},
    )
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
        state.log.warning("User '%s' has no profile image to normalize.", username)
        state.stats.record_warning(count_processed=True)
        raise SystemExit(0 if dry_run else 1)

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
