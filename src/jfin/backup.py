import re
from pathlib import Path
from typing import Any

from . import backup_restore, state
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
    raise ValueError(f"Cannot guess file extension from content-type '{content_type}'")


def content_type_from_extension(extension: str) -> str:
    """Inverse mapping from file extension to a reasonable content-type."""
    ext = extension.lower()
    if ext in (".png",):
        return "image/png"
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".webp":
        return "image/webp"
    raise ValueError(f"Cannot guess content-type from file extension '{extension}'")


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
            "Unknown backup_mode '%s'; defaulting to 'partial'.", raw_mode
        )
        return "partial"
    return mode


def should_backup_for_plan(decision: str, backup_mode: str) -> bool:
    """Decide if an image should be backed up based on mode."""
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
    """Persist a backup copy of the original image."""
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
            rf"{re.escape(c)}\d*",
            stem,
        ):
            return img_type
    raise ValueError(f"Unrecognized image type for filename: {filename}")


def _extract_backdrop_index(filename: str) -> int | None:
    """Compatibility wrapper for backdrop index extraction."""
    return backup_restore.extract_backdrop_index(filename)


def _restore_deps() -> backup_restore.RestoreDeps:
    """Build restore dependency context using module globals."""
    return backup_restore.RestoreDeps(
        state_module=state,
        image_type_from_filename_fn=image_type_from_filename,
        content_type_from_extension_fn=content_type_from_extension,
        image_type_to_mode=IMAGE_TYPE_TO_MODE,
        mode_to_image_type=MODE_TO_IMAGE_TYPE,
    )


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
                "Failed to remove staging directory %s: %s", staging_dir, e
            )


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
            state.log.debug("Could not remove staging parent (may not be empty): %s", e)


def _restore_backup_payload(
    *,
    path: Path,
    item_id: str,
    image_type: str,
    jf_client: JellyfinClient,
    dry_run: bool,
    backdrop_index: int | None,
) -> bool:
    """Compatibility wrapper for single-file restore payload upload."""
    return backup_restore.restore_backup_payload(
        path=path,
        item_id=item_id,
        image_type=image_type,
        jf_client=jf_client,
        dry_run=dry_run,
        backdrop_index=backdrop_index,
        deps=_restore_deps(),
    )


def _restore_single_image_group(
    *,
    item_id: str,
    image_type: str,
    paths: list[Path],
    jf_client: JellyfinClient,
    dry_run: bool,
) -> int:
    """Compatibility wrapper for restoring one non-backdrop image group."""
    return backup_restore.restore_single_image_group(
        item_id=item_id,
        image_type=image_type,
        paths=paths,
        jf_client=jf_client,
        dry_run=dry_run,
        deps=_restore_deps(),
    )


def _restore_backdrop_group(
    *,
    item_id: str,
    paths: list[Path],
    jf_client: JellyfinClient,
    dry_run: bool,
) -> int:
    """Compatibility wrapper for restoring contiguous backdrop groups."""
    return backup_restore.restore_backdrop_group(
        item_id=item_id,
        paths=paths,
        jf_client=jf_client,
        dry_run=dry_run,
        deps=_restore_deps(),
    )


def restore_from_backups(
    *,
    backup_root: Path,
    jf_client: JellyfinClient,
    operations: list[str],
    dry_run: bool,
) -> None:
    """Restore item images for the requested operations."""
    if not backup_root.exists():
        state.log.critical("Backup directory does not exist: %s", backup_root)
        state.stats.record_error("restore", "Backup directory missing")
        raise SystemExit(1)
    backup_restore.restore_from_backups(
        backup_root=backup_root,
        jf_client=jf_client,
        operations=operations,
        dry_run=dry_run,
        deps=_restore_deps(),
    )


def restore_single_item_from_backup(
    *,
    backup_root: Path,
    jf_client: JellyfinClient,
    mode: str,
    target_id: str,
    dry_run: bool,
    backdrop_index: int | None = None,
) -> bool:
    """Restore a single item for the requested mode."""
    return backup_restore.restore_single_item_from_backup(
        backup_root=backup_root,
        jf_client=jf_client,
        mode=mode,
        target_id=target_id,
        dry_run=dry_run,
        deps=_restore_deps(),
    )
