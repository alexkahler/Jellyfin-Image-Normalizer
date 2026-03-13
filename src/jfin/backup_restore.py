"""Provide backup restore helpers."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .backup_restore_helpers import extract_backdrop_index
from .client import JellyfinClient


@dataclass(frozen=True, slots=True)
class RestoreDeps:
    """Represent RestoreDeps behavior and state."""

    state_module: Any
    image_type_from_filename_fn: Callable[[str], str | None]
    content_type_from_extension_fn: Callable[[str], str]
    image_type_to_mode: Mapping[str, str]
    mode_to_image_type: Mapping[str, str]


def restore_backup_payload(
    *,
    path: Path,
    item_id: str,
    image_type: str,
    jf_client: JellyfinClient,
    dry_run: bool,
    backdrop_index: int | None,
    deps: RestoreDeps,
) -> bool:
    """Restore backup payload."""
    state_module = deps.state_module
    try:
        data = path.read_bytes()
    except Exception as exc:
        state_module.log.error("Failed to read backup %s: %s", path, exc)
        state_module.stats.record_error(str(path), f"read failed: {exc}")
        return False
    if dry_run:
        state_module.log.debug(
            "DRY RUN - Would restore %s for %s from %s",
            image_type,
            item_id,
            path,
        )
        state_module.stats.record_success()
        return True
    content_type = deps.content_type_from_extension_fn(path.suffix)
    before_failures = len(state_module.api_failures)
    mode = deps.image_type_to_mode.get(image_type)
    if mode == "profile" or image_type.lower() == "profile":
        upload_ok = jf_client.set_user_profile_image(
            user_id=item_id,
            data=data,
            content_type=content_type,
            failures=state_module.api_failures,
        )
    else:
        upload_ok = jf_client.set_item_image_bytes(
            item_id=item_id,
            image_type=image_type,
            data=data,
            content_type=content_type,
            backdrop_index=backdrop_index,
            failures=state_module.api_failures,
        )
    upload_error = state_module.latest_api_error(before_failures)
    if upload_ok:
        state_module.log.info("[RESTORE] Uploaded backup %s for %s", path, item_id)
        state_module.stats.record_success()
        return True
    state_module.stats.record_error(str(path), upload_error or "restore upload failed")
    return False


def restore_single_image_group(
    *,
    item_id: str,
    image_type: str,
    paths: list[Path],
    jf_client: JellyfinClient,
    dry_run: bool,
    deps: RestoreDeps,
) -> int:
    """Restore single image group."""
    if not paths:
        return 0
    state_module = deps.state_module
    sorted_paths = sorted(paths)
    if len(sorted_paths) > 1:
        state_module.log.error(
            "Multiple backups found for %s (%s); using %s and skipping the rest.",
            item_id,
            image_type,
            sorted_paths[0],
        )
        state_module.stats.record_error(item_id, f"multiple {image_type} backups found")
    return int(
        restore_backup_payload(
            path=sorted_paths[0],
            item_id=item_id,
            image_type=image_type,
            jf_client=jf_client,
            dry_run=dry_run,
            backdrop_index=None,
            deps=deps,
        )
    )


def restore_backdrop_group(
    *,
    item_id: str,
    paths: list[Path],
    jf_client: JellyfinClient,
    dry_run: bool,
    deps: RestoreDeps,
) -> int:
    """Restore backdrop group."""
    if not paths:
        return 0
    state_module = deps.state_module
    index_to_path: dict[int, Path] = {}
    for path in paths:
        idx = extract_backdrop_index(path.name)
        if idx is None:
            state_module.log.error(
                "Invalid backdrop filename %s for item %s; skipping all backdrops.",
                path.name,
                item_id,
            )
            state_module.stats.record_error(str(path), "invalid backdrop filename")
            return 0
        if idx in index_to_path:
            state_module.log.error(
                "Duplicate backdrop index %d for item %s; skipping all backdrops.",
                idx,
                item_id,
            )
            state_module.stats.record_error(item_id, f"duplicate backdrop index {idx}")
            return 0
        index_to_path[idx] = path
    ordered_indices = sorted(index_to_path.keys())
    if (
        not ordered_indices
        or ordered_indices[0] != 0
        or ordered_indices != list(range(ordered_indices[-1] + 1))
    ):
        state_module.log.error(
            "Backdrop indices must start at 0 and be contiguous for item %s; found %s",
            item_id,
            ordered_indices,
        )
        state_module.stats.record_error(
            item_id, "backdrop indices not contiguous from 0"
        )
        return 0

    successes = 0
    for idx in ordered_indices:
        if restore_backup_payload(
            path=index_to_path[idx],
            item_id=item_id,
            image_type="Backdrop",
            jf_client=jf_client,
            dry_run=dry_run,
            backdrop_index=idx,
            deps=deps,
        ):
            successes += 1
    return successes


def restore_from_backups(
    *,
    backup_root: Path,
    jf_client: JellyfinClient,
    operations: list[str],
    dry_run: bool,
    deps: RestoreDeps,
) -> None:
    """Restore from backups."""
    state_module = deps.state_module
    operation_set = set(operations)
    restored = 0
    for dirpath, _, filenames in os.walk(backup_root):
        dir_path = Path(dirpath)
        try:
            rel_parts = dir_path.relative_to(backup_root).parts
        except ValueError:
            rel_parts = ()
        if rel_parts and rel_parts[0] == "staging":
            continue
        if not filenames:
            continue
        item_id = dir_path.name
        if len(item_id) < 2:
            continue
        files_by_type: dict[str, list[Path]] = {}
        for fname in filenames:
            try:
                image_type = deps.image_type_from_filename_fn(fname)
            except ValueError:
                continue
            if not image_type:
                continue
            mode = deps.image_type_to_mode.get(image_type)
            if mode not in operation_set:
                continue
            files_by_type.setdefault(image_type, []).append(dir_path / fname)
        if not files_by_type:
            continue
        state_module.stats.record_item_processed(item_id)
        for image_type, paths in files_by_type.items():
            if image_type == "Backdrop":
                restored += restore_backdrop_group(
                    item_id=item_id,
                    paths=paths,
                    jf_client=jf_client,
                    dry_run=dry_run,
                    deps=deps,
                )
            else:
                restored += restore_single_image_group(
                    item_id=item_id,
                    image_type=image_type,
                    paths=paths,
                    jf_client=jf_client,
                    dry_run=dry_run,
                    deps=deps,
                )
    state_module.log.info("Restore completed. Uploaded %s backup images.", restored)


def restore_single_item_from_backup(
    *,
    backup_root: Path,
    jf_client: JellyfinClient,
    mode: str,
    target_id: str,
    dry_run: bool,
    deps: RestoreDeps,
) -> bool:
    """Restore single item from backup."""
    state_module = deps.state_module
    image_type = deps.mode_to_image_type.get(mode)
    if not image_type:
        state_module.log.critical("Unsupported mode '%s' for restore.", mode)
        state_module.stats.record_error("restore", f"unsupported mode {mode}")
        return False
    target_dir = backup_root / target_id[:2] / target_id
    if not target_dir.exists():
        state_module.log.error("No backup directory found for %s.", target_id)
        state_module.stats.record_error(target_id, "Backup not found")
        return False
    state_module.stats.record_item_processed(target_id)
    files_by_type: dict[str, list[Path]] = {}
    for child in target_dir.iterdir():
        if not child.is_file():
            continue
        try:
            img_type = deps.image_type_from_filename_fn(child.name)
        except ValueError:
            continue
        if img_type:
            files_by_type.setdefault(img_type, []).append(child)
    if image_type == "Backdrop":
        successes = restore_backdrop_group(
            item_id=target_id,
            paths=files_by_type.get("Backdrop", []),
            jf_client=jf_client,
            dry_run=dry_run,
            deps=deps,
        )
        return successes > 0
    paths = files_by_type.get(image_type, [])
    if not paths:
        state_module.log.error("No backup found for %s (mode=%s).", target_id, mode)
        state_module.stats.record_error(target_id, "Backup not found")
        return False
    successes = restore_single_image_group(
        item_id=target_id,
        image_type=image_type,
        paths=paths,
        jf_client=jf_client,
        dry_run=dry_run,
        deps=deps,
    )
    return successes > 0
