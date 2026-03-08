from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Callable, Literal, TypeGuard

from . import state
from .constants import DEFAULT_ITEM_TYPES

LogoPadding = Literal["add", "remove", "none"]


@dataclass
class ModeRuntimeSettings:
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
    library_names: list[str]
    include_item_types: list[str]
    enable_image_types: list[str]
    recursive: bool


class ConfigError(Exception):
    pass


def parse_str_list(value: Any) -> list[str]:
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
    errors: list[str] = []

    def is_bool(value: Any) -> TypeGuard[bool]:
        return isinstance(value, bool)

    def is_int(value: Any) -> TypeGuard[int]:
        return isinstance(value, int) and not isinstance(value, bool)

    def is_number(value: Any) -> TypeGuard[int | float]:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def expect(
        container: dict[str, Any],
        key: str,
        context: str,
        validator: Callable[[Any], bool],
        expectation: str,
    ) -> None:
        if key in container and not validator(container[key]):
            errors.append(f"{context}.{key} must be {expectation}.")

    def expect_string(
        container: dict[str, Any], key: str, context: str, allow_empty: bool = True
    ) -> None:
        if key in container:
            value = container[key]
            if not isinstance(value, str):
                errors.append(f"{context}.{key} must be a string.")
            elif not allow_empty and not value:
                errors.append(f"{context}.{key} must be a non-empty string.")

    def expect_string_list(value: Any, context: str) -> None:
        if isinstance(value, str):
            return
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return
        errors.append(f"{context} must be a string or a list of strings.")

    for required in ("jf_url", "jf_api_key"):
        if required not in cfg or cfg.get(required) is None:
            errors.append(f"{required} is required and must be a non-empty string.")
            continue
        expect_string(cfg, required, "config", allow_empty=False)

    expect(cfg, "timeout", "config", is_number, "a number")
    for key in ("jf_delay_ms", "api_retry_count", "api_retry_backoff_ms"):
        expect(cfg, key, "config", is_int, "an integer")
    for key in ("verify_tls", "fail_fast", "dry_run", "backup", "force_upload_noscale"):
        expect(cfg, key, "config", is_bool, "a boolean")
    for key in ("backup_mode", "backup_dir"):
        expect_string(cfg, key, "config")

    if "operations" in cfg:
        expect_string_list(cfg["operations"], "config.operations")
    try:
        parse_item_types(cfg.get("item_types"))
    except ConfigError as exc:
        errors.append(str(exc))

    logging_cfg = cfg.get("logging")
    if logging_cfg is not None:
        if not isinstance(logging_cfg, dict):
            errors.append("config.logging must be a table/object.")
        else:
            for key in ("file_path", "file_level", "cli_level"):
                expect_string(logging_cfg, key, "config.logging")
            for key in ("file_enabled", "silent"):
                expect(logging_cfg, key, "config.logging", is_bool, "a boolean")

    libraries_cfg = cfg.get("libraries")
    if libraries_cfg is not None:
        if isinstance(libraries_cfg, dict):
            if "names" in libraries_cfg:
                expect_string_list(libraries_cfg["names"], "config.libraries.names")
            elif libraries_cfg:
                errors.append(
                    "config.libraries.names is required when providing the libraries table."
                )
        elif not isinstance(libraries_cfg, (list, str)):
            errors.append(
                "config.libraries must be a table/object or a list/string of library names."
            )

    for mode in ("logo", "thumb", "profile", "backdrop"):
        mode_cfg = cfg.get(mode)
        if mode_cfg is None:
            continue
        context = f"config.{mode}"
        if not isinstance(mode_cfg, dict):
            errors.append(f"{context} must be a table/object.")
            continue

        for key in ("width", "height"):
            expect(mode_cfg, key, context, is_int, "an integer")
        for key in ("no_upscale", "no_downscale"):
            expect(mode_cfg, key, context, is_bool, "a boolean")

        if mode == "logo":
            if "no_padding" in mode_cfg:
                state.log.warning(
                    "Config key 'logo.no_padding' has been removed. "
                    'Use logo.padding = "none" instead of no_padding=true.'
                )
                state.stats.record_warning()
                errors.append(
                    "config.logo.no_padding has been removed. "
                    'Use logo.padding = "none" instead of no_padding=true.'
                )
            expect_string(mode_cfg, "padding", context)
            expect(
                mode_cfg,
                "padding_remove_sensitivity",
                context,
                is_number,
                "a number",
            )

        if mode in {"thumb", "backdrop"}:
            expect(mode_cfg, "jpeg_quality", context, is_int, "an integer")
        if mode == "profile":
            expect(mode_cfg, "webp_quality", context, is_int, "an integer")

        for key in ("width", "height"):
            value = mode_cfg.get(key)
            if is_int(value) and value <= 0:
                errors.append(f"{context}.{key} must be greater than zero.")

        if mode in {"thumb", "backdrop"}:
            quality = mode_cfg.get("jpeg_quality")
            if is_int(quality) and not 1 <= quality <= 95:
                errors.append("jpeg_quality must be between 1 and 95.")

        if mode == "profile":
            quality = mode_cfg.get("webp_quality")
            if is_int(quality) and not 1 <= quality <= 100:
                errors.append("config.profile.webp_quality must be between 1 and 100.")

        if mode == "logo":
            padding = mode_cfg.get("padding")
            if isinstance(padding, str) and padding.strip().lower() not in {
                "add",
                "remove",
                "none",
            }:
                errors.append(
                    'config.logo.padding must be one of "add", "remove", or "none".'
                )
            sensitivity = mode_cfg.get("padding_remove_sensitivity")
            if is_number(sensitivity) and sensitivity < 0:
                errors.append("config.logo.padding_remove_sensitivity must be >= 0.")

    if errors:
        raise ConfigError("Invalid configuration values: " + "; ".join(errors))
