from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .client import JellyfinClient
from .config import ModeRuntimeSettings, build_discovery_settings
from .discovery import (
    DiscoveredItem,
    _item_backdrop_count,
    discover_all_library_items,
    discover_libraries,
)


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
    normalize_item_image_api_fn: Callable[..., bool],
    state_module: Any,
) -> None:
    enabled_set = set(enabled_image_types)

    total_images = 0
    for item in items:
        for image_type in item.image_types & enabled_set:
            if image_type == "Backdrop":
                total_images += item.backdrop_count or 1
            else:
                total_images += 1

    processed_images = 0
    state_module.stats.record_images_found(total_images)

    if total_images == 0:
        state_module.log.info("No item images matched the requested types.")
        return

    for item in items:
        if not (item.image_types & enabled_set):
            continue
        state_module.stats.record_item_processed(item.id)
        for image_type in sorted(item.image_types):
            if image_type not in enabled_set:
                continue
            increment = (item.backdrop_count or 1) if image_type == "Backdrop" else 1
            normalize_item_image_api_fn(
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
                state_module.log.info(
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
    image_type_to_mode: dict[str, str],
    normalize_item_image_api_fn: Callable[..., bool],
    state_module: Any,
) -> None:
    discovery = build_discovery_settings(cfg, operations)
    enabled_image_types = [
        image_type
        for image_type in discovery.enable_image_types
        if image_type_to_mode.get(image_type) in operations
    ]
    if not enabled_image_types:
        state_module.log.info(
            "No image types enabled for operations %s; skipping library processing.",
            operations,
        )
        return

    libraries = discover_libraries(jf_client, discovery)
    if discovery.library_names and not libraries:
        state_module.log.warning("No libraries matched filters; nothing to do.")
        return

    items = discover_all_library_items(jf_client, libraries, discovery)
    if not items:
        state_module.log.info(
            "No items found with requested images in selected libraries."
        )
        return

    state_module.log.info(
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
        normalize_item_image_api_fn=normalize_item_image_api_fn,
        state_module=state_module,
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
    mode_to_image_type: dict[str, str],
    normalize_item_image_api_fn: Callable[..., bool],
    state_module: Any,
) -> bool:
    image_type = mode_to_image_type.get(mode)
    if not image_type:
        state_module.log.critical(
            "Unsupported mode '%s' for --single item processing.",
            mode,
        )
        state_module.stats.record_error("single", f"Unsupported mode {mode}")
        return False

    state_module.stats.record_item_processed(item_id)

    raw: dict[str, Any] | None = None
    backdrop_count: int | None = None
    if image_type == "Backdrop":
        raw = jf_client.get_item(item_id)
        if raw is None:
            state_module.log.critical(
                "Failed to fetch item %s for single-backdrop mode.",
                item_id,
            )
            state_module.stats.record_error("single", "item fetch failed")
            return False

        backdrop_count = _item_backdrop_count(raw)
        if backdrop_count == 0:
            state_module.log.info("Item %s has no backdrops; nothing to do.", item_id)
            state_module.stats.record_skip(count_processed=False)
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

    state_module.stats.record_images_found(backdrop_count or 1)
    state_module.log.info("Processing single item %s as %s", item_id, mode)
    return normalize_item_image_api_fn(
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
