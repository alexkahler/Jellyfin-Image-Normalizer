"""Provide pipeline profiles helpers."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Callable

from PIL import Image

from .client import JellyfinClient
from .config import ModeRuntimeSettings
from .discovery import find_user_by_name, profile_display_name
from .imaging import (
    apply_exif_orientation,
    build_normalized_image,
    encode_image_to_bytes,
    handle_no_scale,
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
    plan_and_backup_image_fn: Callable[..., Any],
    state_module: Any,
) -> bool:
    """Normalize profile user."""
    user_id = user.get("Id")
    if not user_id:
        state_module.log.warning("[API-SKIP] Missing user Id in user record, skipping.")
        state_module.stats.record_warning(count_processed=True)
        return False

    user_label = profile_display_name(user)

    if not user.get("PrimaryImageTag"):
        state_module.log.info(
            "[SKIP] %s has no PrimaryImageTag; skipping profile image.",
            user_label,
        )
        state_module.stats.record_skip(count_processed=True)
        return False

    image_response = jf_client.get_user_image(user_id)
    if image_response is None:
        state_module.log.error(
            "[API-SKIP] Could not fetch profile image for %s", user_label
        )
        state_module.stats.record_error(user_label, "Could not fetch profile image")
        return False

    data, content_type = image_response

    try:
        with Image.open(io.BytesIO(data)) as opened_img:
            img: Image.Image = apply_exif_orientation(opened_img)
            orig_mode = img.mode

            plan = plan_and_backup_image_fn(
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
                """Run upload original profile."""
                before_failures = len(state_module.api_failures)
                upload_ok = jf_client.set_user_profile_image(
                    user_id=user_id,
                    data=data,
                    content_type=content_type or "application/octet-stream",
                    failures=state_module.api_failures,
                )
                return upload_ok, state_module.latest_api_error(before_failures)

            no_scale_result = handle_no_scale(
                plan=plan,
                dry_run=dry_run,
                force_upload=force_upload_noscale,
                upload_fn=upload_original_profile,
                record_label=user_label,
                default_error="API upload failed for NO_SCALE profile image",
                stats=state_module.stats,
            )
            if no_scale_result is not None:
                return no_scale_result

            if dry_run:
                state_module.stats.record_success()
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

            before_failures = len(state_module.api_failures)
            upload_ok = jf_client.set_user_profile_image(
                user_id=user_id,
                data=payload,
                content_type=normalized_content_type,
                failures=state_module.api_failures,
            )
            if upload_ok:
                state_module.stats.record_success()
                return True

            upload_error = state_module.latest_api_error(before_failures)
            state_module.stats.record_error(
                user_label,
                upload_error or "API upload failed for profile image",
            )
            return False

    except Exception as exc:
        state_module.log.exception(
            "[ERROR] Failed to process profile for %s", user_label
        )
        state_module.stats.record_error(user_label, str(exc))
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
    normalize_profile_user_fn: Callable[..., bool],
    state_module: Any,
) -> None:
    """Process profiles."""
    users = jf_client.list_users(is_disabled=False)
    if not users:
        state_module.log.warning(
            "[WARN] No active users returned from Jellyfin; skipping profile processing."
        )
        state_module.stats.record_warning()
        return
    available_profiles = sum(1 for user in users if user.get("PrimaryImageTag"))
    state_module.stats.record_images_found(available_profiles)

    for user in users:
        normalize_profile_user_fn(
            user=user,
            settings=settings,
            dry_run=dry_run,
            jf_client=jf_client,
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
    normalize_profile_user_fn: Callable[..., bool],
    state_module: Any,
) -> int | None:
    """Process single profile."""
    if is_restore:
        state_module.log.warning(
            "Restore is not supported for profile images; skipping."
        )
        state_module.stats.record_warning()
        return 1

    if jf_client is None:
        state_module.log.critical("Jellyfin client is required for profile images.")
        state_module.stats.record_error("profile", "Missing Jellyfin client")
        return 1

    users = jf_client.list_users(is_disabled=False)
    user = find_user_by_name(users, username)
    if user is None:
        state_module.log.critical("User '%s' not found or disabled.", username)
        state_module.stats.record_error(username, "User not found or disabled")
        return 1

    if not user.get("PrimaryImageTag"):
        state_module.log.info(
            "[SKIP] User '%s' has no profile image to normalize.", username
        )
        state_module.stats.record_skip(count_processed=True)
        return 0 if dry_run else 1

    state_module.stats.record_images_found(1)
    state_module.log.info(
        "Processing profile for user '%s' - Target: %sx%s, Dry-run=%s",
        username,
        settings.target_width,
        settings.target_height,
        dry_run,
    )
    normalize_profile_user_fn(
        user=user,
        settings=settings,
        dry_run=dry_run,
        jf_client=jf_client,
        force_upload_noscale=force_upload_noscale,
        make_backup=make_backup,
        backup_root=backup_root,
        backup_mode=backup_mode,
    )
    return None
