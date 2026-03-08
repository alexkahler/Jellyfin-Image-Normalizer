# fmt: off
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, cast

import tomllib

from . import state
from .config_core import (
    ConfigError,
    DiscoverySettings,
    LogoPadding,
    ModeRuntimeSettings,
    _derive_canvas_size,
    apply_cli_overrides,
    parse_item_types,
    parse_str_list,
    validate_config_types,
)
from .constants import (
    APP_VERSION,
    DEFAULT_CONFIG_NAME,
    DEFAULT_TOML_TEMPLATE,
    MODE_TO_IMAGE_TYPE,
    SECTION_KEY_MAP,
    VALID_MODES,
)

_PUBLIC_REEXPORTS = (apply_cli_overrides, validate_config_types)


def _merge_section_keys(cfg: dict[str, Any]) -> dict[str, Any]:
    """Lift known section keys to the top level when missing."""
    normalized_sections = {
        name.lower(): value for name, value in cfg.items() if isinstance(value, dict)
    }
    for section, keys in SECTION_KEY_MAP.items():
        table = normalized_sections.get(section)
        if not isinstance(table, dict):
            continue
        for key in keys:
            if key in table and (key not in cfg or isinstance(cfg.get(key), dict)):
                cfg[key] = table[key]
    return cfg


def default_config_path() -> Path:
    """Return the default config path relative to the repository root."""
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / DEFAULT_CONFIG_NAME


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
    config_path.write_text(DEFAULT_TOML_TEMPLATE.strip() + "\n", encoding="utf-8")
    state.log.info("Config file generated at: %s", config_path)
    state.log.info(
        "Please edit this file to match your environment before running the script."
    )


def load_config_from_path(config_path: Path) -> dict[str, Any]:
    """Load and parse a TOML configuration file."""
    if config_path.suffix.lower() != ".toml":
        raise ConfigError(
            "Unsupported config format: expected a .toml file (e.g. config.toml)."
        )

    if not config_path.exists():
        raise ConfigError(
            f"Config file not found: {config_path}. Create one with "
            "--generate-config and review it before running."
        )

    try:
        with config_path.open("rb") as handle:
            cfg = tomllib.load(handle)
    except FileNotFoundError as exc:
        raise ConfigError(
            f"Config file not found: {config_path}. Create one with "
            "--generate-config and review it before running."
        ) from exc
    except Exception as exc:
        raise ConfigError(f"Failed to parse TOML config {config_path}: {exc}") from exc

    if not isinstance(cfg, dict):
        raise ConfigError(
            f"Invalid config structure in {config_path}: expected a TOML table at the root."
        )
    return _merge_section_keys(cfg)


def load_config(config_path: Path) -> dict[str, Any]:
    """Log configuration errors and exit for backward compatibility."""
    try:
        return load_config_from_path(config_path)
    except ConfigError as exc:
        state.log.critical(str(exc))
        sys.exit(1)


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
            "Operations must be a string like 'logo|thumb' or a list of modes in config."
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


def validate_config_for_mode(cfg: dict[str, Any], mode: str) -> None:
    """Ensure required top-level and mode-specific keys exist."""
    for key in ("jf_url", "jf_api_key"):
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


def build_mode_runtime_settings(
    mode: str,
    mode_cfg: dict[str, Any],
    args: Any,
) -> ModeRuntimeSettings:
    """Prepare runtime settings for a mode using config and CLI overrides."""
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
            base_width,
            base_height,
            None,
            None,
        )

    allow_upscale = not (
        mode_cfg.get("no_upscale", False) or getattr(args, "no_upscale", False)
    )
    allow_downscale = not (
        mode_cfg.get("no_downscale", False) or getattr(args, "no_downscale", False)
    )

    jpeg_quality = max(1, min(95, int(mode_cfg.get("jpeg_quality", 85))))
    webp_quality = max(
        1,
        min(
            100,
            int(mode_cfg.get("webp_quality", 80)) if "webp_quality" in mode_cfg else 80,
        ),
    )

    logo_padding: LogoPadding = "add"
    logo_padding_remove_sensitivity = 0.0
    if mode == "logo":
        cfg_padding = mode_cfg.get("padding", "add")
        cfg_padding = cfg_padding.strip().lower() if isinstance(cfg_padding, str) else "add"
        if cfg_padding not in {"add", "remove", "none"}:
            raise ConfigError(
                f"logo.padding must be one of add/remove/none (got {cfg_padding!r})."
            )

        arg_padding = getattr(args, "logo_padding", None)
        if isinstance(arg_padding, str) and arg_padding:
            cfg_padding = arg_padding.strip().lower()
        logo_padding = cast(LogoPadding, cfg_padding)

        sensitivity = mode_cfg.get("padding_remove_sensitivity", 0)
        if isinstance(sensitivity, (int, float)) and not isinstance(sensitivity, bool):
            logo_padding_remove_sensitivity = float(sensitivity)
        if not 0.0 <= logo_padding_remove_sensitivity <= 255.0:
            raise ConfigError(
                f"logo.padding_remove_sensitivity must be between 0 and 255. "
                f"(got {logo_padding_remove_sensitivity})."
            )

    return ModeRuntimeSettings(
        target_width=target_width,
        target_height=target_height,
        allow_upscale=allow_upscale,
        allow_downscale=allow_downscale,
        jpeg_quality=jpeg_quality,
        webp_quality=webp_quality,
        logo_padding=logo_padding,
        logo_padding_remove_sensitivity=logo_padding_remove_sensitivity,
    )


def build_discovery_settings(
    cfg: dict[str, Any],
    operations: list[str],
) -> DiscoverySettings:
    """Build discovery settings with item and image filters."""
    libraries_cfg = cfg.get("libraries")
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

    return JellyfinClient(
        base_url=cast(str, cfg.get("jf_url")),
        api_key=cast(str, cfg.get("jf_api_key")),
        client_version=version,
        timeout=float(cfg.get("timeout", 15.0)),
        verify_tls=bool(cfg.get("verify_tls", True)),
        delay=api_delay_sec,
        retry_count=retry_count,
        backoff_base=backoff_base,
        fail_fast=fail_fast,
        dry_run=dry_run,
    )
