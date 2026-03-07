from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Literal

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
    elif isinstance(value, list):
        raw_parts = value
    else:
        return []

    seen: set[str] = set()
    result: list[str] = []
    for part in raw_parts:
        text = str(part).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def parse_item_types(value: Any) -> list[str]:
    if value is None:
        raw_parts: list[str] = []
    elif isinstance(value, (str, list)):
        raw_parts = parse_str_list(value)
    else:
        raise ConfigError("item_types must be a string or a list of strings.")

    if not raw_parts:
        return list(DEFAULT_ITEM_TYPES)

    canonical: list[str] = []
    for part in raw_parts:
        token = part.strip().lower()
        if token in {"movie", "movies"}:
            mapped = "Movie"
        elif token == "series":  # nosec B105
            mapped = "Series"
        else:
            raise ConfigError("item_types must contain only movies and/or series.")

        if mapped not in canonical:
            canonical.append(mapped)

    return canonical


def apply_cli_overrides(args: Any, cfg: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(cfg)

    if getattr(args, "jf_url", None):
        merged["jf_url"] = args.jf_url
    if getattr(args, "jf_api_key", None):
        merged["jf_api_key"] = args.jf_api_key

    if "libraries" not in merged or merged["libraries"] is None:
        merged["libraries"] = {}
    if getattr(args, "libraries", None):
        merged["libraries"]["names"] = parse_str_list(args.libraries)
    if getattr(args, "item_types", None):
        merged["item_types"] = args.item_types

    if getattr(args, "dry_run", False):
        merged["dry_run"] = True
    if getattr(args, "backup", False):
        merged["backup"] = True

    for mode in ("logo", "thumb", "profile", "backdrop"):
        mode_cfg = merged.setdefault(mode, {})

        dim_override = getattr(args, f"{mode}_target_size", None)
        if dim_override:
            width, height = dim_override
            mode_cfg["width"] = width
            mode_cfg["height"] = height

        if getattr(args, "no_upscale", False):
            mode_cfg["no_upscale"] = True
        if getattr(args, "no_downscale", False):
            mode_cfg["no_downscale"] = True

    if getattr(args, "thumb_jpeg_quality", None) is not None:
        merged["thumb"]["jpeg_quality"] = args.thumb_jpeg_quality
    if getattr(args, "backdrop_jpeg_quality", None) is not None:
        merged["backdrop"]["jpeg_quality"] = args.backdrop_jpeg_quality
    if getattr(args, "profile_webp_quality", None) is not None:
        merged["profile"]["webp_quality"] = args.profile_webp_quality
    if getattr(args, "jf_delay_ms", None) is not None:
        merged["jf_delay_ms"] = args.jf_delay_ms
    if getattr(args, "force_upload_noscale", False):
        merged["force_upload_noscale"] = True

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

    def expect_bool(container: dict[str, Any], key: str, context: str) -> None:
        if key in container and not isinstance(container[key], bool):
            errors.append(f"{context}.{key} must be a boolean.")

    def expect_int(container: dict[str, Any], key: str, context: str) -> None:
        if key in container:
            value = container[key]
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"{context}.{key} must be an integer.")

    def expect_number(container: dict[str, Any], key: str, context: str) -> None:
        if key in container:
            value = container[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                errors.append(f"{context}.{key} must be a number.")

    def expect_string(container: dict[str, Any], key: str, context: str, allow_empty: bool = True) -> None:
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

    expect_number(cfg, "timeout", "config")
    for key in ("jf_delay_ms", "api_retry_count", "api_retry_backoff_ms"):
        expect_int(cfg, key, "config")
    for key in ("verify_tls", "fail_fast", "dry_run", "backup", "force_upload_noscale"):
        expect_bool(cfg, key, "config")
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
            expect_string(logging_cfg, "file_path", "config.logging")
            expect_bool(logging_cfg, "file_enabled", "config.logging")
            expect_string(logging_cfg, "file_level", "config.logging")
            expect_string(logging_cfg, "cli_level", "config.logging")
            expect_bool(logging_cfg, "silent", "config.logging")

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
        if not isinstance(mode_cfg, dict):
            errors.append(f"config.{mode} must be a table/object.")
            continue

        expect_int(mode_cfg, "width", f"config.{mode}")
        expect_int(mode_cfg, "height", f"config.{mode}")
        expect_bool(mode_cfg, "no_upscale", f"config.{mode}")
        expect_bool(mode_cfg, "no_downscale", f"config.{mode}")

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
            expect_string(mode_cfg, "padding", f"config.{mode}")
            expect_number(mode_cfg, "padding_remove_sensitivity", f"config.{mode}")

        if mode in {"thumb", "backdrop"}:
            expect_int(mode_cfg, "jpeg_quality", f"config.{mode}")
        if mode == "profile":
            expect_int(mode_cfg, "webp_quality", f"config.{mode}")

        width = mode_cfg.get("width")
        height = mode_cfg.get("height")
        if isinstance(width, int) and not isinstance(width, bool) and width <= 0:
            errors.append(f"config.{mode}.width must be greater than zero.")
        if isinstance(height, int) and not isinstance(height, bool) and height <= 0:
            errors.append(f"config.{mode}.height must be greater than zero.")

        if mode in {"thumb", "backdrop"}:
            quality = mode_cfg.get("jpeg_quality")
            if isinstance(quality, int) and not isinstance(quality, bool) and not 1 <= quality <= 95:
                errors.append("jpeg_quality must be between 1 and 95.")

        if mode == "profile":
            quality = mode_cfg.get("webp_quality")
            if isinstance(quality, int) and not isinstance(quality, bool) and not 1 <= quality <= 100:
                errors.append("config.profile.webp_quality must be between 1 and 100.")

        if mode == "logo":
            padding = mode_cfg.get("padding")
            if isinstance(padding, str) and padding.strip().lower() not in {"add", "remove", "none"}:
                errors.append('config.logo.padding must be one of "add", "remove", or "none".')
            sensitivity = mode_cfg.get("padding_remove_sensitivity")
            if isinstance(sensitivity, (int, float)) and not isinstance(sensitivity, bool) and sensitivity < 0:
                errors.append("config.logo.padding_remove_sensitivity must be >= 0.")

    if errors:
        raise ConfigError("Invalid configuration values: " + "; ".join(errors))
