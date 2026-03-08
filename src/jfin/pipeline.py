from __future__ import annotations

from pathlib import Path
from typing import Any

from . import state
from .backup import (
    cleanup_staging_dir,
    get_staging_dir,
    guess_extension_from_content_type,
)
from .client import JellyfinClient
from .config import ModeRuntimeSettings
from .constants import IMAGE_TYPE_TO_MODE, MODE_TO_IMAGE_TYPE
from .discovery import DiscoveredItem
from .imaging import ScalePlan
from .pipeline_backdrops import (
    normalize_item_backdrops_api as _normalize_item_backdrops_api,
)
from .pipeline_image_normalization import (
    normalize_image_bytes as _normalize_image_bytes_impl,
    plan_and_backup_image as _plan_and_backup_image_impl,
)
from .pipeline_image_payload import (
    process_item_image_payload as _process_item_image_payload_impl,
)
from .pipeline_orchestration import (
    process_discovered_items as _process_discovered_items_impl,
    process_libraries_via_api as _process_libraries_via_api_impl,
    process_single_item_api as _process_single_item_api_impl,
)
from .pipeline_profiles import (
    normalize_profile_user as _normalize_profile_user_impl,
    process_profiles as _process_profiles_impl,
    process_single_profile as _process_single_profile_impl,
)


def _plan_and_backup_image(
    *,
    img,
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
    return _plan_and_backup_image_impl(**locals())


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
    params = locals()
    params["state_module"] = state
    return _normalize_image_bytes_impl(**params)


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
    params = locals()
    params["normalize_image_bytes_fn"] = _normalize_image_bytes
    params["state_module"] = state
    return _process_item_image_payload_impl(**params)


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
    if image_type == "Backdrop":
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
        state.log.warning(
            "[WARN] No settings for mode '%s'; skipping %s.", mode, image_type
        )
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
    force_upload_noscale: bool,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
) -> bool:
    params = locals()
    params.update(
        {
            "image_type_to_mode": IMAGE_TYPE_TO_MODE,
            "normalize_image_bytes_fn": _normalize_image_bytes,
            "guess_extension_from_content_type_fn": guess_extension_from_content_type,
            "get_staging_dir_fn": get_staging_dir,
            "cleanup_staging_dir_fn": cleanup_staging_dir,
            "state_module": state,
        }
    )
    return _normalize_item_backdrops_api(**params)


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
    params = locals()
    params["normalize_item_image_api_fn"] = normalize_item_image_api
    params["state_module"] = state
    _process_discovered_items_impl(**params)


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
    params = locals()
    params["image_type_to_mode"] = IMAGE_TYPE_TO_MODE
    params["normalize_item_image_api_fn"] = normalize_item_image_api
    params["state_module"] = state
    _process_libraries_via_api_impl(**params)


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
    params = locals()
    params["plan_and_backup_image_fn"] = _plan_and_backup_image
    params["state_module"] = state
    return _normalize_profile_user_impl(**params)


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
    params = locals()
    params["normalize_profile_user_fn"] = normalize_profile_user
    params["state_module"] = state
    _process_profiles_impl(**params)


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
    if mode not in MODE_TO_IMAGE_TYPE:
        state.log.critical("Unsupported mode '%s' for --single item processing.", mode)
        state.stats.record_error("single", f"Unsupported mode {mode}")
        raise SystemExit(1)

    params = locals()
    params["mode_to_image_type"] = MODE_TO_IMAGE_TYPE
    params["normalize_item_image_api_fn"] = normalize_item_image_api
    params["state_module"] = state
    return _process_single_item_api_impl(**params)


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
    params = locals()
    params["normalize_profile_user_fn"] = normalize_profile_user
    params["state_module"] = state
    exit_code = _process_single_profile_impl(**params)
    if exit_code is not None:
        raise SystemExit(exit_code)
