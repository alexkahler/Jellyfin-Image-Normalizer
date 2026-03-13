"""Provide helper functions for backup restore flows."""

from __future__ import annotations

from pathlib import Path

from .constants import FILENAME_CONFIG


def extract_backdrop_index(filename: str) -> int | None:
    """Extract a numeric backdrop index from one backup filename."""
    stem = Path(filename).stem
    backdrop_stem = FILENAME_CONFIG.get("Backdrop", "backdrop")
    if not stem.startswith(backdrop_stem):
        return None
    suffix = stem[len(backdrop_stem) :]
    if suffix == "":
        return 0
    if suffix.isdigit():
        return int(suffix)
    return None
