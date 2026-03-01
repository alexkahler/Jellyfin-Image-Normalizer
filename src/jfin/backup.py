import os
import re
from pathlib import Path
from typing import Any

from . import state
from .client import JellyfinClient
from .constants import (
    FILENAME_CONFIG,
    IMAGE_TYPE_TO_MODE,
    MODE_TO_IMAGE_TYPE,
    VALID_BACKUP_MODES,
)


def guess_extension_from_content_type(content_type: str | None) -> str:
    """Map a content-type string to a file extension for backups."""
    ct = (content_type or "").lower()
    if "png" in ct:
        return ".png"
    if "jpeg" in ct or "jpg" in ct:
        return ".jpg"
    if "webp" in ct:
        return ".webp"
    raise ValueError(
        f"Cannot guess file extension from content-type '{content_type}'")


def content_type_from_extension(extension: str) -> str:
    """Inverse mapping from file extension to a reasonable content-type."""
    ext = extension.lower()
    if ext in (".png",):
        return "image/png"
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".webp":
        return "image/webp"
    raise ValueError(
        f"Cannot guess content-type from file extension '{extension}'")


def backup_path_for_image(
    backup_root: Path,
    item_id: str,
    image_type: str,
    extension: str,
    backdrop_index: int | None,
) -> Path:
    """Compute backup path using the <first2>/<item_id>/stem.ext layout."""
    subdir = backup_root / item_id[:2] / item_id
    subdir.mkdir(parents=True, exist_ok=True)
    stem = FILENAME_CONFIG.get(image_type, image_type.lower())
    if backdrop_index is not None and backdrop_index > 0:
        stem = f"{stem}{backdrop_index}"
    return subdir / f"{stem}{extension}"


def normalize_backup_mode(raw_mode: Any) -> str:
    """Return a normalized backup mode string with a safe default."""
    mode = "partial" if raw_mode is None else str(raw_mode).strip().lower()
    if mode not in VALID_BACKUP_MODES:
        state.log.warning(
            "Unknown backup_mode '%s'; defaulting to 'partial'.", raw_mode)
        return "partial"
    return mode


def should_backup_for_plan(decision: str, backup_mode: str) -> bool:
    """
    Decide if an image should be backed up based on scale decision and mode.

    In partial mode, only SCALE_UP/DOWN images are backed up. In full mode,
    all images are backed up regardless of the scale decision.
    """
    normalized_mode = normalize_backup_mode(backup_mode)
    if normalized_mode == "full":
        return True
    return decision != "NO_SCALE"


def save_backup(
    *,
    backup_root: Path,
    item_id: str,
    image_type: str,
    data: bytes,
    content_type: str | None,
    overwrite_existing: bool = False,
    backdrop_index: int | None,
) -> Path:
    """
    Persist a backup copy of the original image.

    When ``overwrite_existing`` is True, existing backups are replaced only
    when their contents differ.
    """
    extension = guess_extension_from_content_type(
        content_type=content_type,
    )
    path = backup_path_for_image(
        backup_root=backup_root,
        item_id=item_id,
        image_type=image_type,
        extension=extension,
        backdrop_index=backdrop_index,
    )
    if path.exists():
        if overwrite_existing:
            try:
                current_bytes = path.read_bytes()
            except Exception as exc:
                state.log.warning(
                    "Could not read existing backup %s (%s); overwriting.",
                    path,
                    exc,
                )
                current_bytes = None

            if current_bytes == data:
                state.log.debug("  -> Backup already up to date at %s", path)
                return path

            path.write_bytes(data=data)
            state.log.debug("  -> Backup updated at %s", path)
        else:
            state.log.debug("  -> Backup already exists at %s", path)
    else:
        path.write_bytes(data=data)
        state.log.debug("  -> Backup saved to %s", path)
    return path


def image_type_from_filename(filename: str) -> str | None:
    """Return the configured image type for a backup filename."""
    stem = Path(filename).stem.lower()
    for img_type, configured_stem in FILENAME_CONFIG.items():
        c = configured_stem.lower()
        if stem == c:
            return img_type
        if img_type == "Backdrop" and re.fullmatch(
            fr"{re.escape(c)}\d*",
            stem,
        ):
            return img_type
    raise ValueError(f"Unrecognized image type for filename: {filename}")


def _extract_backdrop_index(filename: str) -> int | None:
    """
    Return the zero-based backdrop index encoded in a backup filename.

    The configured stem (e.g., ``backdrop``) corresponds to index 0. A numeric
    suffix (``backdrop1.jpg``) maps to that integer index. Returns None when
    the filename does not follow the expected pattern.
    """
    stem = Path(filename).stem
    backdrop_stem = FILENAME_CONFIG.get("Backdrop", "backdrop")
    if not stem.startswith(backdrop_stem):
        return None

    suffix = stem[len(backdrop_stem):]
    if suffix == "":
        return 0
    if suffix.isdigit():
        return int(suffix)
    return None


def get_staging_dir(backup_root: Path, item_id: str) -> Path:
    """Return the staging directory for an item, creating it if needed."""
    staging_dir = backup_root / "staging" / item_id
    staging_dir.mkdir(parents=True, exist_ok=True)
    return staging_dir


def cleanup_staging_dir(backup_root: Path, item_id: str) -> None:
    """Remove the staging directory for a specific item after processing."""
    staging_dir = backup_root / "staging" / item_id
    if staging_dir.exists():
        try:
            import shutil
            shutil.rmtree(staging_dir)
            state.log.debug("  -> Staging directory removed: %s", staging_dir)
        except Exception as e:
            state.log.warning(
                "Failed to remove staging directory %s: %s", staging_dir, e)


def cleanup_all_staging(backup_root: Path) -> None:
    """Remove the entire staging directory if it's empty after processing."""
    staging_parent = backup_root / "staging"
    if staging_parent.exists():
        try:
            import shutil
            # Only remove if empty
            if not any(staging_parent.iterdir()):
                shutil.rmtree(staging_parent)
                state.log.debug(
                    "  -> Staging parent directory removed: %s",
                    staging_parent,
                )
        except Exception as e:
            state.log.debug(
                "Could not remove staging parent (may not be empty): %s", e)


def _restore_backup_payload(
    *,
    path: Path,
    item_id: str,
    image_type: str,
    jf_client: JellyfinClient,
    dry_run: bool,
    backdrop_index: int | None,
) -> bool:
    """
    Restore a single backup file (logo, thumb, profile, or backdrop).

    Reads bytes from disk, infers content type, and uploads through the
    Jellyfin client unless ``dry_run`` is True. Statistics are recorded.
    """
    try:
        data = path.read_bytes()
    except Exception as exc:
        state.log.error("Failed to read backup %s: %s", path, exc)
        state.stats.record_error(str(path), f"read failed: {exc}")
        return False

    if dry_run:
        state.log.debug(
            "DRY RUN - Would restore %s for %s from %s",
            image_type,
            item_id,
            path,
        )
        state.stats.record_success()
        return True

    content_type = content_type_from_extension(path.suffix)
    before_failures = len(state.api_failures)

    mode = IMAGE_TYPE_TO_MODE.get(image_type)
    if mode == "profile" or image_type.lower() == "profile":
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
            backdrop_index=backdrop_index,
            failures=state.api_failures,
        )

    upload_error = state.latest_api_error(before_failures)
    if upload_ok:
        state.log.info("[RESTORE] Uploaded backup %s for %s", path, item_id)
        state.stats.record_success()
        return True

    state.stats.record_error(
        str(path), upload_error or "restore upload failed")
    return False


def _restore_single_image_group(
    *,
    item_id: str,
    image_type: str,
    paths: list[Path],
    jf_client: JellyfinClient,
    dry_run: bool,
) -> int:
    """
    Restore a non-backdrop image group for a single item.

    If multiple backups exist (e.g., profile.jpg and profile.png), the first is
    restored and one error is recorded to surface the duplicate.
    """
    if not paths:
        return 0

    sorted_paths = sorted(paths)
    if len(sorted_paths) > 1:
        state.log.error(
            "Multiple backups found for %s (%s); using %s and skipping "
            "the rest.",
            item_id,
            image_type,
            sorted_paths[0],
        )
        state.stats.record_error(
            item_id, f"multiple {image_type} backups found")

    return int(
        _restore_backup_payload(
            path=sorted_paths[0],
            item_id=item_id,
            image_type=image_type,
            jf_client=jf_client,
            dry_run=dry_run,
            backdrop_index=None,
        )
    )


def _restore_backdrop_group(
    *,
    item_id: str,
    paths: list[Path],
    jf_client: JellyfinClient,
    dry_run: bool,
) -> int:
    """
    Restore all backdrop backups for a single item.

    Filenames must encode contiguous indices starting at 0 (backdrop.jpg,
    backdrop1.jpg, backdrop2.jpg, ...). Any gap, unknown pattern, or duplicate
    index skips the entire backdrop restore to keep behavior deterministic.
    """
    if not paths:
        return 0

    index_to_path: dict[int, Path] = {}
    for path in paths:
        idx = _extract_backdrop_index(path.name)
        if idx is None:
            state.log.error(
                "Invalid backdrop filename %s for item %s; skipping all "
                "backdrops.",
                path.name,
                item_id,
            )
            state.stats.record_error(str(path), "invalid backdrop filename")
            return 0
        if idx in index_to_path:
            state.log.error(
                "Duplicate backdrop index %d for item %s; skipping all "
                "backdrops.",
                idx,
                item_id,
            )
            state.stats.record_error(
                item_id, f"duplicate backdrop index {idx}")
            return 0
        index_to_path[idx] = path

    ordered_indices = sorted(index_to_path.keys())
    if (
        not ordered_indices
        or ordered_indices[0] != 0
        or ordered_indices != list(range(ordered_indices[-1] + 1))
    ):
        state.log.error(
            "Backdrop indices must start at 0 and be contiguous for item %s; "
            "found %s",
            item_id,
            ordered_indices,
        )
        state.stats.record_error(
            item_id, "backdrop indices not contiguous from 0")
        return 0

    successes = 0
    for idx in ordered_indices:
        path = index_to_path[idx]
        # Upload in ascending index order for deterministic behavior.
        if _restore_backup_payload(
            path=path,
            item_id=item_id,
            image_type="Backdrop",
            jf_client=jf_client,
            dry_run=dry_run,
            backdrop_index=idx,
        ):
            successes += 1
    return successes


def restore_from_backups(
    *,
    backup_root: Path,
    jf_client: JellyfinClient,
    operations: list[str],
    dry_run: bool,
) -> None:
    """
    Restore item images for the requested operations.

    Behavior notes:
    - Supports logo, thumb/landscape, profile, and backdrop images.
    - Backdrops must be contiguous starting at index 0 (backdrop.jpg,
      backdrop1.jpg, ...). Any gap or duplicate index skips all backdrops
      for that item and records one error.
    - Duplicate non-backdrop backups upload the first file by name and log
      one error to surface the duplicate.
    - Unknown filenames are ignored.
    - In ``dry_run`` mode, uploads are skipped but successes are still
      recorded for each eligible file.
    """
    if not backup_root.exists():
        state.log.critical("Backup directory does not exist: %s", backup_root)
        state.stats.record_error("restore", "Backup directory missing")
        raise SystemExit(1)

    operation_set = set(operations)
    restored = 0

    for dirpath, _, filenames in os.walk(backup_root):
        dir_path = Path(dirpath)
        try:
            rel_parts = dir_path.relative_to(backup_root).parts
        except ValueError:
            rel_parts = ()

        # Skip staging artifacts
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
                image_type = image_type_from_filename(fname)
            except Exception:
                continue
            if not image_type:
                continue

            mode = IMAGE_TYPE_TO_MODE.get(image_type)
            if mode not in operation_set:
                continue

            files_by_type.setdefault(image_type, []).append(dir_path / fname)

        if not files_by_type:
            continue

        state.stats.record_item_processed(item_id)

        for image_type, paths in files_by_type.items():
            if image_type == "Backdrop":
                restored += _restore_backdrop_group(
                    item_id=item_id,
                    paths=paths,
                    jf_client=jf_client,
                    dry_run=dry_run,
                )
            else:
                restored += _restore_single_image_group(
                    item_id=item_id,
                    image_type=image_type,
                    paths=paths,
                    jf_client=jf_client,
                    dry_run=dry_run,
                )

    state.log.info("Restore completed. Uploaded %s backup images.", restored)


def restore_single_item_from_backup(
    *,
    backup_root: Path,
    jf_client: JellyfinClient,
    mode: str,
    target_id: str,
    dry_run: bool,
    backdrop_index: int | None = None,
) -> bool:
    """
    Restore a single item's assets for the requested mode
    (logo, thumb, backdrop, or profile).

    Backdrop handling mirrors the backup layout:
    - ``backdrop.jpg`` represents index 0.
    - ``backdrop1.jpg``, ``backdrop2.jpg``, ... map to indices 1, 2, ...
    - Indices must start at 0 and be contiguous; otherwise the backdrop
      restore for that item is aborted and one error recorded.

    The ``backdrop_index`` parameter is ignored; indices are derived from
    filenames to keep behavior deterministic.

    Duplicate non-backdrop backups result in one upload (first filename by
    sort order) and one recorded error. Unknown filenames are ignored. In
    ``dry_run`` mode uploads are skipped but successes are still counted for
    each eligible backup discovered.
    """
    image_type = MODE_TO_IMAGE_TYPE.get(mode)
    if not image_type:
        state.log.critical("Unsupported mode '%s' for restore.", mode)
        state.stats.record_error("restore", f"unsupported mode {mode}")
        return False

    target_dir = backup_root / target_id[:2] / target_id
    if not target_dir.exists():
        state.log.error("No backup directory found for %s.", target_id)
        state.stats.record_error(target_id, "Backup not found")
        return False

    state.stats.record_item_processed(target_id)

    files_by_type: dict[str, list[Path]] = {}
    for child in target_dir.iterdir():
        if not child.is_file():
            continue
        try:
            img_type = image_type_from_filename(child.name)
        except Exception:
            continue
        if img_type:
            files_by_type.setdefault(img_type, []).append(child)

    if image_type == "Backdrop":
        backdrop_paths = files_by_type.get("Backdrop", [])
        successes = _restore_backdrop_group(
            item_id=target_id,
            paths=backdrop_paths,
            jf_client=jf_client,
            dry_run=dry_run,
        )
        return successes > 0

    paths = files_by_type.get(image_type, [])
    if not paths:
        state.log.error("No backup found for %s (mode=%s).", target_id, mode)
        state.stats.record_error(target_id, "Backup not found")
        return False

    successes = _restore_single_image_group(
        item_id=target_id,
        image_type=image_type,
        paths=paths,
        jf_client=jf_client,
        dry_run=dry_run,
    )
    return successes > 0
