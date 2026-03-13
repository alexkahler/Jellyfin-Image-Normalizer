"""Provide config core helpers."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Literal

from . import state
from .config_validation_checks import (
    validate_config_types as _validate_config_types_impl,
)
from .constants import DEFAULT_ITEM_TYPES

LogoPadding = Literal["add", "remove", "none"]


@dataclass
class ModeRuntimeSettings:
    """Represent ModeRuntimeSettings behavior and state."""

    target_width: int
    target_height: int
    allow_upscale: bool
    allow_downscale: bool
    jpeg_quality: int
    webp_quality: int
    logo_padding: LogoPadding = "add"
    logo_padding_remove_sensitivity: float = 0.0


@dataclass
class DiscoverySettings:
    """Represent DiscoverySettings behavior and state."""

    library_names: list[str]
    include_item_types: list[str]
    enable_image_types: list[str]
    recursive: bool


class ConfigError(Exception):
    """Represent ConfigError behavior and state."""

    pass


def parse_str_list(value: Any) -> list[str]:
    """Parse str list."""
    if value is None:
        return []
    if isinstance(value, str):
        raw_parts = value.replace("|", ",").split(",")
    elif not isinstance(value, list):
        return []
    else:
        raw_parts = value

    cleaned = (str(part).strip() for part in raw_parts)
    return list(dict.fromkeys(part for part in cleaned if part))


def parse_item_types(value: Any) -> list[str]:
    """Parse item types."""
    if value is None:
        raw_parts: list[str] = []
    elif not isinstance(value, (str, list)):
        raise ConfigError("item_types must be a string or a list of strings.")
    else:
        raw_parts = parse_str_list(value)

    if not raw_parts:
        return list(DEFAULT_ITEM_TYPES)

    type_mapping = {"movie": "Movie", "movies": "Movie", "series": "Series"}  # nosec B105
    try:
        canonical = [type_mapping[part.strip().lower()] for part in raw_parts]
    except KeyError as exc:
        raise ConfigError("item_types must contain only movies and/or series.") from exc
    return list(dict.fromkeys(canonical))


def apply_cli_overrides(args: Any, cfg: dict[str, Any]) -> dict[str, Any]:
    """Run apply cli overrides."""
    merged = copy.deepcopy(cfg)

    for key in ("jf_url", "jf_api_key"):
        value = getattr(args, key, None)
        if value:
            merged[key] = value

    if "libraries" not in merged or merged["libraries"] is None:
        merged["libraries"] = {}
    if getattr(args, "libraries", None):
        merged["libraries"]["names"] = parse_str_list(args.libraries)
    if getattr(args, "item_types", None):
        merged["item_types"] = args.item_types

    for flag in ("dry_run", "backup", "force_upload_noscale"):
        if getattr(args, flag, False):
            merged[flag] = True

    for mode in ("logo", "thumb", "profile", "backdrop"):
        mode_cfg = merged.setdefault(mode, {})

        dim_override = getattr(args, f"{mode}_target_size", None)
        if dim_override:
            mode_cfg["width"], mode_cfg["height"] = dim_override

        if getattr(args, "no_upscale", False):
            mode_cfg["no_upscale"] = True
        if getattr(args, "no_downscale", False):
            mode_cfg["no_downscale"] = True

    quality_overrides = {
        "thumb_jpeg_quality": ("thumb", "jpeg_quality"),
        "backdrop_jpeg_quality": ("backdrop", "jpeg_quality"),
        "profile_webp_quality": ("profile", "webp_quality"),
    }
    for arg_name, (mode, key) in quality_overrides.items():
        value = getattr(args, arg_name, None)
        if value is not None:
            merged[mode][key] = value

    if getattr(args, "jf_delay_ms", None) is not None:
        merged["jf_delay_ms"] = args.jf_delay_ms

    return merged


def _validate_positive_override(value: Any, label: str) -> int | None:
    """Run  validate positive override."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigError(f"{label} must be a positive integer (got {value!r}).")
    return value


def _derive_canvas_size(
    base_width: int,
    base_height: int,
    arg_width: Any,
    arg_height: Any,
) -> tuple[int, int]:
    """Derive canvas size."""
    override_w = _validate_positive_override(arg_width, "CLI width override")
    override_h = _validate_positive_override(arg_height, "CLI height override")

    if override_w is not None and override_h is not None:
        return override_w, override_h
    if override_w is not None and base_width > 0:
        inferred_height = max(1, int(round(base_height * (override_w / base_width))))
        return override_w, inferred_height
    if override_h is not None and base_height > 0:
        inferred_width = max(1, int(round(base_width * (override_h / base_height))))
        return inferred_width, override_h
    return base_width, base_height


def validate_config_types(cfg: dict[str, Any]) -> None:
    """Validate config types."""
    _validate_config_types_impl(
        cfg,
        parse_item_types_fn=parse_item_types,
        config_error_type=ConfigError,
        state_module=state,
    )
