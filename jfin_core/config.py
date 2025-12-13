from __future__ import annotations

import copy
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for Python <3.11
    import tomli as tomllib  # type: ignore[no-redef]

from . import state
from .constants import (
    APP_VERSION,
    DEFAULT_CONFIG_NAME,
    DEFAULT_ITEM_TYPES,
    MODE_TO_IMAGE_TYPE,
    VALID_MODES,
    DEFAULT_TOML_TEMPLATE,
    SECTION_KEY_MAP,
)


@dataclass
class ModeRuntimeSettings:
    """Runtime settings for logo, thumb, and profile modes."""

    target_width: int
    target_height: int
    allow_upscale: bool
    allow_downscale: bool
    jpeg_quality: int
    webp_quality: int
    no_padding: bool


@dataclass
class DiscoverySettings:
    """Resolved discovery parameters for listing libraries and items."""

    library_names: list[str]
    include_item_types: list[str]
    enable_image_types: list[str]
    recursive: bool


class ConfigError(Exception):
    """Raised when configuration files are missing, invalid, or unsupported."""


def _merge_section_keys(cfg: dict[str, Any]) -> dict[str, Any]:
    """Lift known section keys to the top level when missing."""
    normalized_sections = {
        name.lower(): value
        for name, value in cfg.items()
        if isinstance(value, dict)
    }
    for section, keys in SECTION_KEY_MAP.items():
        table = normalized_sections.get(section)
        if not isinstance(table, dict):
            continue
        for key in keys:
            if key in table and (
                key not in cfg or isinstance(cfg.get(key), dict)
            ):
                cfg[key] = table[key]
    return cfg


def default_config_path() -> Path:
    """Return the default config path relative to the repository root."""
    package_root = Path(__file__).resolve().parent.parent
    return package_root / DEFAULT_CONFIG_NAME


def generate_default_config(config_path: Path) -> None:
    """Create a starter TOML config file with safe defaults."""
    if config_path.suffix.lower() != ".toml":
        state.log.critical(
            "Config generation supports only TOML files. "
            "Please use a .toml extension (e.g. config.toml)."
        )
        sys.exit(1)

    if config_path.exists():
        state.log.error("Config file already exists: %s", config_path)
        sys.exit(1)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        DEFAULT_TOML_TEMPLATE.strip() + "\n", encoding="utf-8")

    state.log.info("Config file generated at: %s", config_path)
    state.log.info(
        "Please edit this file to match your environment before running "
        "the script."
    )


def load_config_from_path(config_path: Path) -> dict[str, Any]:
    """
    Load and parse the JFIN configuration file from the given path.

    This function supports only TOML configuration files (`.toml`). The
    resulting dictionary can be normalized into runtime settings (mode
    options, discovery filters, logging, Jellyfin client configuration,
    etc.).

    Raises:
        ConfigError: if the file is missing, not a .toml file, or cannot
            be parsed.
    """
    if config_path.suffix.lower() != ".toml":
        raise ConfigError(
            "Unsupported config format: expected a .toml file "
            "(e.g. config.toml)."
        )

    if not config_path.exists():
        raise ConfigError(
            f"Config file not found: {config_path}. Create one with "
            "--generate-config and review it before running."
        )

    try:
        with config_path.open("rb") as f:
            cfg = tomllib.load(f)
    except FileNotFoundError as exc:
        raise ConfigError(
            f"Config file not found: {config_path}. Create one with "
            "--generate-config and review it before running."
        ) from exc
    except Exception as exc:  # tomllib/tomli raise TOMLDecodeError subclasses
        raise ConfigError(
            f"Failed to parse TOML config {config_path}: {exc}"
        ) from exc

    if not isinstance(cfg, dict):
        raise ConfigError(
            f"Invalid config structure in {config_path}: expected a "
            "TOML table at the root."
        )

    return _merge_section_keys(cfg)


def load_config(config_path: Path) -> dict[str, Any]:
    """Log configuration errors and exit for backward compatibility."""
    try:
        return load_config_from_path(config_path)
    except ConfigError as exc:
        state.log.critical(str(exc))
        sys.exit(1)


def validate_config_types(cfg: dict[str, Any]) -> None:
    """
    Validate the loaded configuration for required keys and expected types.

    Raises:
        ConfigError: if required fields are missing/empty or values have
            invalid types.
    """
    errors: list[str] = []

    def expect_bool(
        container: dict[str, Any], key: str, context: str
    ) -> None:
        if key in container and not isinstance(container[key], bool):
            errors.append(f"{context}.{key} must be a boolean.")

    def expect_int(
        container: dict[str, Any], key: str, context: str
    ) -> None:
        if key in container:
            value = container[key]
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"{context}.{key} must be an integer.")

    def expect_number(
        container: dict[str, Any], key: str, context: str
    ) -> None:
        if key in container:
            value = container[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                errors.append(f"{context}.{key} must be a number.")

    def expect_string(
        container: dict[str, Any],
        key: str,
        context: str,
        allow_empty: bool = True,
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
        if isinstance(value, list) and all(
            isinstance(item, str) for item in value
        ):
            return
        errors.append(f"{context} must be a string or a list of strings.")

    for required in ("jf_url", "jf_api_key"):
        if required not in cfg or cfg.get(required) is None:
            errors.append(
                f"{required} is required and must be a non-empty string.")
            continue
        expect_string(cfg, required, "config", allow_empty=False)
    expect_number(cfg, "timeout", "config")
    expect_int(cfg, "jf_delay_ms", "config")
    expect_int(cfg, "api_retry_count", "config")
    expect_int(cfg, "api_retry_backoff_ms", "config")
    expect_bool(cfg, "verify_tls", "config")
    expect_bool(cfg, "fail_fast", "config")
    expect_bool(cfg, "dry_run", "config")
    expect_bool(cfg, "backup", "config")
    expect_string(cfg, "backup_mode", "config")
    expect_string(cfg, "backup_dir", "config")
    expect_bool(cfg, "force_upload_noscale", "config")

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
                expect_string_list(
                    libraries_cfg["names"], "config.libraries.names"
                )
            elif libraries_cfg:
                errors.append(
                    "config.libraries.names is required when providing the "
                    "libraries table."
                )
        elif isinstance(libraries_cfg, (list, str)):
            pass
        else:
            errors.append(
                "config.libraries must be a table/object or a list/string of "
                "library names."
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
            expect_bool(mode_cfg, "no_padding", f"config.{mode}")
        if mode == "thumb" or mode == "backdrop":
            expect_int(mode_cfg, "jpeg_quality", f"config.{mode}")
        if mode == "profile":
            expect_int(mode_cfg, "webp_quality", f"config.{mode}")

        width = mode_cfg.get("width")
        height = mode_cfg.get("height")
        if (
            isinstance(width, int)
            and not isinstance(width, bool)
            and width <= 0
        ):
            errors.append(f"config.{mode}.width must be greater than zero.")
        if (
            isinstance(height, int)
            and not isinstance(height, bool)
            and height <= 0
        ):
            errors.append(f"config.{mode}.height must be greater than zero.")
        if mode == "thumb" or mode == "backdrop":
            quality = mode_cfg.get("jpeg_quality")
            if isinstance(quality, int) and not isinstance(quality, bool):
                if quality < 1 or quality > 95:
                    errors.append("jpeg_quality must be between 1 and 95.")
        if mode == "profile":
            quality = mode_cfg.get("webp_quality")
            if isinstance(quality, int) and not isinstance(quality, bool):
                if quality < 1 or quality > 100:
                    errors.append(
                        "config.profile.webp_quality must be between "
                        "1 and 100."
                    )

    if errors:
        raise ConfigError("Invalid configuration values: " + "; ".join(errors))


def parse_str_list(value: Any) -> list[str]:
    """Normalize strings or lists into a unique, trimmed list of strings."""
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
    """
    Normalize item type filters into canonical Jellyfin values.

    Raises:
        ConfigError: when an unsupported item type is provided.
    """
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
        elif token == "series":
            mapped = "Series"
        else:
            raise ConfigError(
                "item_types must contain only movies and/or series.")

        if mapped not in canonical:
            canonical.append(mapped)

    return canonical


def parse_operations(arg_mode: str | None, cfg_ops: Any) -> list[str]:
    """Validate requested operations from CLI arguments or config."""
    source = arg_mode if arg_mode else cfg_ops
    if source is None:
        state.log.critical(
            "Specify --mode or set 'operations' in config "
            '(e.g., operations = "logo|thumb" or ["logo", "thumb"]).'
        )
        sys.exit(1)

    if isinstance(source, str):
        raw_ops = source.replace(",", "|").split("|")
    elif isinstance(source, list):
        raw_ops = source
    else:
        state.log.critical(
            "Operations must be a string like 'logo|thumb' or a list of modes "
            "in config."
        )
        sys.exit(1)

    operations: list[str] = []
    for op in raw_ops:
        mode = op.strip()
        if not mode:
            continue
        if mode not in VALID_MODES:
            state.log.critical(
                "Invalid mode '%s'. Valid modes: %s",
                mode,
                ", ".join(sorted(VALID_MODES)),
            )
            sys.exit(1)
        if mode not in operations:
            operations.append(mode)

    if not operations:
        state.log.critical("No valid operations specified.")
        sys.exit(1)

    return operations


def apply_cli_overrides(args: Any, cfg: dict[str, Any]) -> dict[str, Any]:
    """Merge CLI overrides into a deep copy of the loaded config."""
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
        if mode not in merged:
            merged[mode] = {}
        mode_cfg = merged[mode]

        dim_override = getattr(args, f"{mode}_target_size", None)
        if dim_override:
            width, height = dim_override
            mode_cfg["width"] = width
            mode_cfg["height"] = height

        if getattr(args, "no_upscale", False):
            mode_cfg["no_upscale"] = True
        if getattr(args, "no_downscale", False):
            mode_cfg["no_downscale"] = True
        if mode == "thumb" and getattr(args, "thumb_jpeg_quality", None) is not None:
            mode_cfg["jpeg_quality"] = args.thumb_jpeg_quality
        if mode == "backdrop" and getattr(args, "backdrop_jpeg_quality", None) is not None:
            mode_cfg["jpeg_quality"] = args.backdrop_jpeg_quality
        if mode == "profile" and getattr(args, "profile_webp_quality", None) is not None:
            mode_cfg["webp_quality"] = args.profile_webp_quality

    if getattr(args, "jf_delay_ms", None) is not None:
        merged["jf_delay_ms"] = args.jf_delay_ms

    if getattr(args, "force_upload_noscale", False):
        merged["force_upload_noscale"] = True

    return merged


def validate_config_for_mode(cfg: dict[str, Any], mode: str) -> None:
    """Ensure required top-level and mode-specific keys exist."""
    required_top = ["jf_url", "jf_api_key"]
    for key in required_top:
        if not cfg.get(key):
            state.log.critical("Config is missing required key '%s'.", key)
            sys.exit(1)

    if mode not in cfg:
        state.log.critical("Config is missing mode section '%s'.", mode)
        sys.exit(1)

    mode_cfg = cfg[mode]
    for key in ("width", "height"):
        if key not in mode_cfg:
            state.log.critical("Config['%s'] is missing '%s'.", mode, key)
            sys.exit(1)


def _validate_positive_override(value: Any, label: str) -> int | None:
    """Validate CLI width/height overrides and return a positive integer."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigError(
            f"{label} must be a positive integer (got {value!r}).")
    return value


def _derive_canvas_size(
    base_width: int,
    base_height: int,
    arg_width: Any,
    arg_height: Any,
) -> tuple[int, int]:
    """
    Compute target canvas size using CLI overrides when provided.

    The missing side is inferred from the configured aspect ratio.
    Results are clamped to at least 1 px to avoid zero-dimension distortions.
    """
    override_w = _validate_positive_override(arg_width, "CLI width override")
    override_h = _validate_positive_override(arg_height, "CLI height override")

    if override_w is not None and override_h is not None:
        return override_w, override_h
    if override_w is not None and base_width > 0:
        inferred_height = max(
            1, int(round(base_height * (override_w / base_width))))
        return override_w, inferred_height
    if override_h is not None and base_height > 0:
        inferred_width = max(
            1, int(round(base_width * (override_h / base_height))))
        return inferred_width, override_h

    return base_width, base_height


def build_mode_runtime_settings(
    mode: str, mode_cfg: dict[str, Any], args: Any
) -> ModeRuntimeSettings:
    """
    Prepare runtime settings for a mode using config and CLI overrides.

    Raises:
        ConfigError: if CLI width/height overrides are not positive integers.
    """
    base_width = mode_cfg["width"]
    base_height = mode_cfg["height"]

    dim_override = getattr(args, f"{mode}_target_size", None)
    if dim_override:
        target_width, target_height = dim_override
        if target_width <= 0 or target_height <= 0:
            raise ConfigError(
                f"{mode} target size must be positive integers (got {dim_override})."
            )
    else:
        target_width, target_height = _derive_canvas_size(
            base_width, base_height, None, None)

    allow_upscale = not (mode_cfg.get("no_upscale", False)
                         or getattr(args, "no_upscale", False))
    allow_downscale = not (mode_cfg.get("no_downscale", False)
                           or getattr(args, "no_downscale", False))
    no_padding = bool(
        mode_cfg.get("no_padding", False) or (
            getattr(args, "no_padding", False) and mode == "logo")
    )

    jpeg_quality = int(mode_cfg.get("jpeg_quality", 85))
    jpeg_quality = max(1, min(95, jpeg_quality))
    webp_quality = int(mode_cfg.get("webp_quality", 80)
                       ) if "webp_quality" in mode_cfg else 80
    webp_quality = max(1, min(100, webp_quality))

    return ModeRuntimeSettings(
        target_width=target_width,
        target_height=target_height,
        allow_upscale=allow_upscale,
        allow_downscale=allow_downscale,
        jpeg_quality=jpeg_quality,
        webp_quality=webp_quality,
        no_padding=no_padding,
    )


def build_discovery_settings(
    cfg: dict[str, Any], operations: list[str]
) -> DiscoverySettings:
    """Build discovery settings with item and image filters."""
    libraries_cfg = cfg.get("libraries")
    library_names: list[str] = []
    if isinstance(libraries_cfg, dict):
        library_names = parse_str_list(libraries_cfg.get("names"))
    else:
        library_names = parse_str_list(libraries_cfg)

    include_item_types = parse_item_types(cfg.get("item_types"))
    enable_image_types = [
        MODE_TO_IMAGE_TYPE[op_mode]
        for op_mode in operations
        if op_mode in MODE_TO_IMAGE_TYPE
    ]

    return DiscoverySettings(
        library_names=library_names,
        include_item_types=include_item_types,
        enable_image_types=enable_image_types,
        recursive=True,
    )


def build_jellyfin_client_from_config(cfg: dict[str, Any]):
    """Factory to construct a JellyfinClient from config values."""
    from .client import JellyfinClient

    jf_delay_ms = cfg.get("jf_delay_ms", 0)
    api_delay_sec = max(0.0, float(jf_delay_ms) / 1000.0)
    retry_count = int(cfg.get("api_retry_count", 3))
    backoff_ms = int(cfg.get("api_retry_backoff_ms", 500))
    backoff_base = max(0.0, float(backoff_ms) / 1000.0)
    fail_fast = bool(cfg.get("fail_fast", False))
    dry_run = bool(cfg.get("dry_run", True))
    version = str(cfg.get("version") or APP_VERSION)

    base_url = cfg.get("jf_url")
    api_key = cfg.get("jf_api_key")

    return JellyfinClient(
        base_url=cast(str, base_url),
        api_key=cast(str, api_key),
        client_version=version,
        timeout=float(cfg.get("timeout", 15.0)),
        verify_tls=bool(cfg.get("verify_tls", True)),
        delay=api_delay_sec,
        retry_count=retry_count,
        backoff_base=backoff_base,
        fail_fast=fail_fast,
        dry_run=dry_run,
    )
