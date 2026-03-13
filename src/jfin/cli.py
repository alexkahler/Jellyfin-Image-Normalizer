#!/usr/bin/env python3
"""Provide cli helpers."""

import argparse
import sys
from typing import Any, cast

from . import state
from .backup import (
    normalize_backup_mode,
    restore_from_backups,
    restore_single_item_from_backup,
)
from .cli_runtime import run_main as _run_main_impl
from .cli_runtime_args import parse_args as _parse_args_impl
from .client import JellyfinClient
from .cli_validation import (
    CliValidationError,
    validate_generate_config_args as _validate_generate_config_args,
    validate_restore_all_args as _validate_restore_all_args,
    validate_test_jf_args as _validate_test_jf_args,
)
from .config import (
    ConfigError,
    ModeRuntimeSettings,
    apply_cli_overrides,
    build_jellyfin_client_from_config,
    build_mode_runtime_settings,
    default_config_path,
    generate_default_config,
    load_config_from_path,
    parse_operations,
    validate_config_for_mode,
    validate_config_types,
)
from .constants import (
    DEFAULT_CONFIG_NAME,
    RECOMMENDED_ASPECT_LABEL_BY_MODE,
    RECOMMENDED_CANVAS_BY_MODE,
    VALID_MODES,
)
from .discovery import find_user_by_name
from .logging_utils import log_run_start, log_run_summary, setup_logging
from .pipeline import (
    process_libraries_via_api,
    process_profiles,
    process_single_profile,
    process_single_item_api,
)
from .route_fence import RouteFenceError, resolve_route, route_fence_json_path

# Keep runtime dependencies on this module namespace so helper execution and
# monkeypatch-based tests can resolve them through `jfin.cli`.
_RUNTIME_DEPS = (
    normalize_backup_mode,
    restore_from_backups,
    restore_single_item_from_backup,
    ConfigError,
    apply_cli_overrides,
    build_jellyfin_client_from_config,
    build_mode_runtime_settings,
    default_config_path,
    generate_default_config,
    load_config_from_path,
    parse_operations,
    validate_config_for_mode,
    validate_config_types,
    VALID_MODES,
    find_user_by_name,
    log_run_start,
    log_run_summary,
    setup_logging,
    process_libraries_via_api,
    process_profiles,
    process_single_profile,
    process_single_item_api,
)

# Explicitly listed v1 routes that now have runtime dispatch support.
_V1_RUNTIME_IMPLEMENTED_ROUTE_KEYS = {("config_init", "n/a"), ("run", "logo")}


def _run_cli_validation_or_exit(validation_fn: Any, argv: list[str]) -> None:
    """Run one CLI validator and map contract failures to exit code 1."""
    try:
        validation_fn(argv)
    except CliValidationError as exc:
        raise SystemExit(1) from exc


def validate_generate_config_args(argv: list[str]) -> None:
    """Validate generate-config argument combinations."""
    _run_cli_validation_or_exit(_validate_generate_config_args, argv)


def validate_restore_all_args(argv: list[str]) -> None:
    """Validate restore-all argument combinations."""
    _run_cli_validation_or_exit(_validate_restore_all_args, argv)


def validate_test_jf_args(argv: list[str]) -> None:
    """Validate test-jf argument combinations."""
    _run_cli_validation_or_exit(_validate_test_jf_args, argv)


def parse_size_pair(value: str) -> tuple[int, int]:
    """Parse size pair."""
    if not isinstance(value, str) or "x" not in value.lower():
        raise argparse.ArgumentTypeError("Expected WIDTHxHEIGHT (e.g., 1000x562).")
    width_str, height_str = value.lower().split("x", 1)
    try:
        width = int(width_str)
        height = int(height_str)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Width and height must be integers (e.g., 1000x562)."
        )
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("Width and height must be positive integers.")
    return width, height


def parse_args() -> argparse.Namespace:
    """Parse args."""
    return _parse_args_impl(
        default_config_name=DEFAULT_CONFIG_NAME,
        parse_size_pair_fn=parse_size_pair,
    )


def warn_unused_cli_overrides(args: argparse.Namespace, operations: list[str]) -> None:
    """Warn when unused cli overrides."""
    ops = set(operations)
    if getattr(args, "no_upscale", False) and getattr(args, "no_downscale", False):
        state.log.warning(
            "--no-upscale and --no-downscale together disable all scaling."
        )
        state.stats.record_warning()
    if args.thumb_jpeg_quality is not None and "thumb" not in ops:
        state.log.warning(
            "--thumb-jpeg-quality has no effect because 'thumb' mode is not selected."
        )
        state.stats.record_warning()
    if args.backdrop_jpeg_quality is not None and "backdrop" not in ops:
        state.log.warning(
            "--backdrop-jpeg-quality has no effect because 'backdrop' mode is not selected."
        )
        state.stats.record_warning()
    if args.profile_webp_quality is not None and "profile" not in ops:
        state.log.warning(
            "--profile-webp-quality has no effect because 'profile' mode is not selected."
        )
        state.stats.record_warning()
    if getattr(args, "logo_padding", None) is not None and "logo" not in ops:
        state.log.warning(
            "--logo-padding has no effect because 'logo' mode is not selected."
        )
        state.stats.record_warning()

    dim_warnings = [
        ("logo", args.logo_target_size, "--logo-target-size"),
        ("thumb", args.thumb_target_size, "--thumb-target-size"),
        ("backdrop", args.backdrop_target_size, "--backdrop-target-size"),
        ("profile", args.profile_target_size, "--profile-target-size"),
    ]
    for mode, value, flag in dim_warnings:
        if value is not None and mode not in ops:
            state.log.warning(
                "%s has no effect because '%s' mode is not selected.", flag, mode
            )
            state.stats.record_warning()
    if getattr(args, "item_types", None) and not ({"logo", "thumb", "backdrop"} & ops):
        state.log.warning(
            "--item-types has no effect without 'logo', 'thumb', or 'backdrop' modes selected."
        )
        state.stats.record_warning()


def warn_unrecommended_aspect_ratios(
    settings_by_mode: dict[str, ModeRuntimeSettings],
) -> None:
    """Warn when unrecommended aspect ratios."""
    for mode, settings in settings_by_mode.items():
        recommended_canvas = RECOMMENDED_CANVAS_BY_MODE.get(mode)
        if recommended_canvas is None:
            continue

        rec_width, rec_height = recommended_canvas
        rec_ratio = round(rec_width / rec_height, 2)
        actual_ratio = round(settings.target_width / settings.target_height, 2)
        if actual_ratio == rec_ratio:
            continue

        label = RECOMMENDED_ASPECT_LABEL_BY_MODE.get(mode, f"{rec_width}x{rec_height}")
        state.log.warning(
            "Unusual %s aspect ratio: configured %sx%s has %.2f (w/h); recommended %s (~%.2f), e.g. %sx%s.",
            mode,
            settings.target_width,
            settings.target_height,
            actual_ratio,
            label,
            rec_ratio,
            rec_width,
            rec_height,
        )
        state.stats.record_warning()


def run_preflight_check(jf_client: JellyfinClient) -> None:
    """Run preflight check."""
    if jf_client.test_connection():
        return

    state.log.critical(
        "Could not connect to Jellyfin server; aborting before processing."
    )
    state.stats.record_error("connectivity", "Pre-flight Jellyfin connection failed.")
    raise SystemExit(1)


def _enforce_route(command: str, mode: str) -> None:
    """Run  enforce route."""
    try:
        route = resolve_route(command, mode)
    except RouteFenceError as exc:
        state.log.critical(str(exc))
        state.stats.record_error("route-fence", str(exc))
        raise SystemExit(1)

    if route == "v0":
        return

    if route == "v1" and (command, mode) in _V1_RUNTIME_IMPLEMENTED_ROUTE_KEYS:
        return

    route_source = route_fence_json_path()
    message = (
        "route-fence dispatch blocked: command='%s' mode='%s' declares route='%s' "
        "but v1 runtime path is not implemented in this build. Source: %s."
    ) % (command, mode, route, route_source)
    state.log.critical(message)
    state.stats.record_error("route-fence", message)
    raise SystemExit(1)


def main() -> None:
    """Run main."""
    args = parse_args()
    exit_code = _run_main_impl(
        args=args,
        argv=sys.argv[1:],
        cli_module=cast(Any, sys.modules[__name__]),
        state_module=state,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
