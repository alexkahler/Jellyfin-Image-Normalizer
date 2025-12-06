from pathlib import Path
from typing import Any

from . import state
from .constants import FILENAME_CONFIG

VALID_BACKUP_MODES = {"full", "partial"}


def guess_extension_from_content_type(content_type: str | None) -> str:
    """Map a content-type string to a file extension for backups."""
    ct = (content_type or "").lower()
    if "png" in ct:
        return ".png"
    if "jpeg" in ct or "jpg" in ct:
        return ".jpg"
    if "webp" in ct:
        return ".webp"
    return ".img"


def content_type_from_extension(extension: str) -> str:
    """Inverse mapping from file extension to a reasonable content-type."""
    ext = extension.lower()
    if ext in (".png",):
        return "image/png"
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".webp":
        return "image/webp"
    return "application/octet-stream"


def backup_path_for_image(backup_root: Path, item_id: str, image_type: str, extension: str) -> Path:
    """Compute backup path using split directory scheme (<first2>/<id>/stem.ext)."""
    subdir = backup_root / item_id[:2] / item_id
    subdir.mkdir(parents=True, exist_ok=True)
    stem = FILENAME_CONFIG.get(image_type, image_type.lower())
    return subdir / f"{stem}{extension}"


def normalize_backup_mode(raw_mode: Any) -> str:
    """Return a normalized backup mode string with a safe default."""
    mode = "partial" if raw_mode is None else str(raw_mode).strip().lower()
    if mode not in VALID_BACKUP_MODES:
        state.log.warning("Unknown backup_mode '%s'; defaulting to 'partial'.", raw_mode)
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
) -> Path:
    """
    Persist a backup copy of the original image.

    When overwrite_existing is True, existing backups are replaced if the bytes differ.
    """
    extension = guess_extension_from_content_type(content_type)
    path = backup_path_for_image(backup_root, item_id, image_type, extension)
    if path.exists():
        if overwrite_existing:
            try:
                current_bytes = path.read_bytes()
            except Exception as exc:
                state.log.warning("Could not read existing backup %s (%s); overwriting.", path, exc)
                current_bytes = None

            if current_bytes == data:
                state.log.info("  -> Backup already up to date at %s", path)
                return path

            path.write_bytes(data)
            state.log.info("  -> Backup updated at %s", path)
        else:
            state.log.info("  -> Backup already exists at %s", path)
    else:
        path.write_bytes(data)
        state.log.info("  -> Backup saved to %s", path)
    return path


def image_type_from_filename(filename: str) -> str | None:
    stem = Path(filename).stem.lower()
    for img_type, configured_stem in FILENAME_CONFIG.items():
        if stem == configured_stem.lower():
            return img_type
    return None
