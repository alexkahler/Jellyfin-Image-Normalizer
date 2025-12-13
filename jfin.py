#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Any, cast


def parse_size_pair(value: str) -> tuple[int, int]:
    """Parse WIDTHxHEIGHT size strings into a positive integer tuple for argparse."""
    if not isinstance(value, str) or "x" not in value.lower():
        raise argparse.ArgumentTypeError(
            "Expected WIDTHxHEIGHT (e.g., 1000x562)."
        )
    width_str, height_str = value.lower().split("x", 1)
    try:
        width = int(width_str)
        height = int(height_str)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Width and height must be integers (e.g., 1000x562)."
        )
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError(
            "Width and height must be positive integers."
        )
    return width, height

from jfin_core import state
from jfin_core.backup import (
    normalize_backup_mode,
    restore_from_backups,
    restore_single_item_from_backup,
)   
from jfin_core.client import JellyfinClient
from jfin_core.config import (
    apply_cli_overrides,
    build_jellyfin_client_from_config,
    build_mode_runtime_settings,
    ConfigError,
    ModeRuntimeSettings,
    default_config_path,
    generate_default_config,
    load_config_from_path,
    parse_operations,
    validate_config_types,
    validate_config_for_mode,
)
from jfin_core.constants import (
    DEFAULT_CONFIG_NAME,
    RECOMMENDED_ASPECT_LABEL_BY_MODE,
    RECOMMENDED_CANVAS_BY_MODE,
    VALID_MODES,
)
from jfin_core.discovery import find_user_by_name
from jfin_core.logging_utils import log_run_start, log_run_summary, setup_logging
from jfin_core.pipeline import (
    process_libraries_via_api,
    process_profiles,
    process_single_profile,
    process_single_item_api,
)


def parse_args() -> argparse.Namespace:
    #FIXME Missing docstring
    parser = argparse.ArgumentParser(
        description=(
            "Normalize Jellyfin images (logos, thumbs, profiles) via the Jellyfin API.\n\n"
            "- Logos: scale to fit inside canvas (defaults from config), preserve aspect ratio and pad with transparency.\n"
            "- Thumbs: scale to cover canvas (defaults from config), preserve aspect ratio and center crop.\n"
            "- Profile: cover-scale, center crop, and encode to WebP (defaults from config).\n\n"
            "Configuration (Jellyfin URL, API key, discovery filters, sizes, etc.) "
            "is loaded from a TOML config file. Use --generate-config to create one."
        )
    )

    parser.add_argument(
        "--config",
        help=(
            f"Path to TOML config file (default: {DEFAULT_CONFIG_NAME} next to script)."
        ),
    )

    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="Generate a default config file and exit. Does not process images.",
    )

    parser.add_argument(
        "--test-jf",
        action="store_true",
        help="Test Jellyfin connection (using config/CLI settings) and exit.",
    )

    parser.add_argument(
        "--mode",
        help=(
            "Image types to handle, e.g. 'logo', 'thumb', 'profile', 'backdrop', "
            "or a pipe-separated list like '"'logo|thumb'"'. Overrides the config "
            "'operations' value if provided."
        ),
    )

    parser.add_argument(
        "--logo-target-size",
        metavar="WIDTHxHEIGHT",
        type=parse_size_pair,
        help="Override logo canvas size with WIDTHxHEIGHT (e.g., 800x310).",
    )
    parser.add_argument(
        "--thumb-target-size",
        metavar="WIDTHxHEIGHT",
        type=parse_size_pair,
        help="Override thumb canvas size with WIDTHxHEIGHT (e.g., 1000x562).",
    )
    parser.add_argument(
        "--backdrop-target-size",
        metavar="WIDTHxHEIGHT",
        type=parse_size_pair,
        help="Override backdrop canvas size with WIDTHxHEIGHT (e.g., 1920x1080).",
    )
    parser.add_argument(
        "--profile-target-size",
        metavar="WIDTHxHEIGHT",
        type=parse_size_pair,
        help="Override profile canvas size with WIDTHxHEIGHT (e.g., 256x256).",
    )

    parser.add_argument(
        "--thumb-jpeg-quality",
        type=int,
        default=None,
        help="JPEG quality for thumb output (1-95). Overrides config thumb.jpeg_quality.",
    )

    parser.add_argument(
        "--backdrop-jpeg-quality",
        type=int,
        default=None,
        help="JPEG quality for backdrop output (1-95). Overrides config backdrop.jpeg_quality.",
    )

    parser.add_argument(
        "--profile-webp-quality",
        type=int,
        default=None,
        help="WebP quality for profile output (1-100). Overrides config profile.webp_quality.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report actions, do not modify files or call the API.",
    )

    parser.add_argument(
        "--backup",
        action="store_true",
        help="Save originals to the configured backup folder before uploading replacements.",
    )

    parser.add_argument(
        "--single",
        help=(
            "Process a single Jellyfin item by id (logo/thumb/backdrop). "
            "Use --mode to filter which image types run."
        ),
    )

    parser.add_argument(
        "--restore",
        action="store_true",
        help=(
            "Restore images from the backup folder via the API. Use with --mode to pick which image types."
        ),
    )

    parser.add_argument(
        "--restore-all",
        action="store_true",
        help=(
            "Restore all backup images (logo, thumb, profile) from the backup folder. "
            "Must be used alone (aside from optional --config/logging flags)."
        ),
    )

    parser.add_argument(
        "--no-upscale",
        action="store_true",
        help="Do not upscale images; only allow downscaling.",
    )

    parser.add_argument(
        "--no-downscale",
        action="store_true",
        help="Do not downscale images; only allow upscaling.",
    )

    parser.add_argument(
        "--logo-padding",
        choices=("add", "remove", "none"),
        default=None,
        help=(
            "Logo padding policy: add (pad to canvas), remove (crop transparent "
            "border before scaling; never pad), or none (no add/remove; only "
            "scale). Overrides config logo.padding."
        ),
    )

    parser.add_argument(
        "--jf-url",
        help="Override Jellyfin base URL from config (e.g. https://jellyfin.example.com).",
    )

    parser.add_argument(
        "--jf-api-key",
        help="Override Jellyfin API key from config.",
    )

    parser.add_argument(
        "--libraries",
        help="Comma- or pipe-separated library names to include. Overrides config.",
    )

    parser.add_argument(
        "--item-types",
        help="Item types to include for discovery (movies|series, pipe/comma-separated). Overrides config.",
    )

    parser.add_argument(
        "--jf-delay-ms",
        type=int,
        help="Delay in milliseconds between API calls (overrides config jf_delay_ms).",
    )

    parser.add_argument(
        "--force-upload-noscale",
        action="store_true",
        help=(
            "For NO_SCALE images (already at target size), force an upload to "
            "Jellyfin anyway. Useful for re-registering pre-normalized artwork."
        ),
    )

    parser.add_argument(
        "--silent",
        "-s",
        action="store_true",
        help="Suppress CLI output (file logging continues).",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging to CLI (overrides logging.cli_level).",
    )

    return parser.parse_args()


def validate_generate_config_args(argv: list[str]) -> None:
    """
    Ensure --generate-config is not combined with operational arguments.

    Permitted tokens: --generate-config, an optional --config path value, and CLI verbosity flags (-s/--silent, -v/--verbose).
    Any other operational or sizing flags trigger a fatal validation error before config generation runs.
    """
    allowed = {"--generate-config", "--config", "--silent", "-s", "--verbose", "-v"}
    extras: list[str] = []
    skip_next = False

    for token in argv:
        if skip_next:
            skip_next = False
            continue

        if token == "--config":
            skip_next = True
            continue
        if token.startswith("--config="):
            continue
        if token in allowed:
            continue

        extras.append(token)

    if extras:
        state.log.critical("--generate-config cannot be combined with other arguments (found: %s).", ", ".join(extras))
        state.stats.record_error("arguments", "generate-config combined with other args")
        raise SystemExit(1)


def validate_restore_all_args(argv: list[str]) -> None:
    """
    Ensure --restore-all is not combined with other operational arguments.

    Allows only logging and config path flags alongside --restore-all.
    """
    allowed = {"--restore-all", "--config", "--silent", "-s", "--verbose", "-v"}
    extras: list[str] = []
    skip_next = False

    for token in argv:
        if skip_next:
            skip_next = False
            continue

        if token == "--config":
            skip_next = True
            continue
        if token.startswith("--config="):
            continue
        if token in allowed:
            continue

        extras.append(token)

    if extras:
        state.log.critical("--restore-all cannot be combined with other arguments (found: %s).", ", ".join(extras))
        state.stats.record_error("arguments", "restore-all combined with other args")
        raise SystemExit(1)


def validate_test_jf_args(argv: list[str]) -> None:
    """
    Ensure --test-jf is not combined with other operational arguments.

    Allows only Jellyfin connection overrides, config path, and logging flags.
    """
    allowed = {
        "--test-jf",
        "--config",
        "--silent",
        "-s",
        "--verbose",
        "-v",
        "--jf-url",
        "--jf-api-key",
        "--jf-delay-ms",
    }
    extras: list[str] = []
    skip_next = False

    for token in argv:
        if skip_next:
            skip_next = False
            continue

        if token in {"--config", "--jf-url", "--jf-api-key", "--jf-delay-ms"}:
            skip_next = True
            continue
        if token.startswith("--config=") or token.startswith("--jf-url=") or token.startswith("--jf-api-key=") or token.startswith("--jf-delay-ms="):
            continue
        if token in allowed:
            continue

        extras.append(token)

    if extras:
        state.log.critical(
            "--test-jf cannot be combined with other arguments (found: %s).",
            ", ".join(extras),
        )
        state.stats.record_error("arguments", "test-jf combined with other args")
        raise SystemExit(1)


def warn_unused_cli_overrides(args: argparse.Namespace, operations: list[str]) -> None:
    """
    Emit warnings for CLI overrides that have no effect with the requested operations.

    Examples: --thumb-jpeg-quality without thumb mode, --profile-webp-quality without profile mode,
    target-size flags without their mode, or --logo-padding without logo mode.
    Each warning is logged and counted so the operator is aware that a flag was ignored.
    """
    ops = set(operations)
    if getattr(args, "no_upscale", False) and getattr(args, "no_downscale", False):
        state.log.warning(
            "--no-upscale and --no-downscale together disable all scaling."
        )
        state.stats.record_warning()
    if args.thumb_jpeg_quality is not None and "thumb" not in ops:
        state.log.warning("--thumb-jpeg-quality has no effect because 'thumb' mode is not selected.")
        state.stats.record_warning()
    if args.backdrop_jpeg_quality is not None and "backdrop" not in ops:
        state.log.warning("--backdrop-jpeg-quality has no effect because 'backdrop' mode is not selected.")
        state.stats.record_warning()
    if args.profile_webp_quality is not None and "profile" not in ops:
        state.log.warning("--profile-webp-quality has no effect because 'profile' mode is not selected.")
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
            state.log.warning("%s has no effect because '%s' mode is not selected.", flag, mode)
            state.stats.record_warning()
    if getattr(args, "item_types", None) and not ({"logo", "thumb", "backdrop"} & ops):
        state.log.warning(
            "--item-types has no effect without 'logo', 'thumb', or 'backdrop' modes selected."
        )
        state.stats.record_warning()


def warn_unrecommended_aspect_ratios(
    settings_by_mode: dict[str, ModeRuntimeSettings],
) -> None:
    """
    Emit warnings when configured target sizes diverge from recommended ratios.

    Aspect ratios are compared as `round(width / height, 2)` to tolerate common
    "16:9-ish" rounded canvases like 1000x562.
    """
    for mode, settings in settings_by_mode.items():
        recommended_canvas = RECOMMENDED_CANVAS_BY_MODE.get(mode)
        if recommended_canvas is None:
            continue

        rec_width, rec_height = recommended_canvas
        rec_ratio = round(rec_width / rec_height, 2)
        actual_ratio = round(settings.target_width / settings.target_height, 2)
        if actual_ratio == rec_ratio:
            continue

        label = RECOMMENDED_ASPECT_LABEL_BY_MODE.get(
            mode, f"{rec_width}x{rec_height}"
        )
        state.log.warning(
            "Unusual %s aspect ratio: configured %sx%s has %.2f (w/h); "
            "recommended %s (~%.2f), e.g. %sx%s.",
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
    """
    Perform a single connectivity check against Jellyfin before any processing.

    The check calls /System/Info via JellyfinClient.test_connection(). If the server is
    unreachable, shutting down, or the API key is rejected, we log a critical error,
    record the failure, and exit early to avoid kicking off discovery or uploads while
    offline or unstable.
    """
    if jf_client.test_connection():
        return

    state.log.critical(
        "Could not connect to Jellyfin server; aborting before processing."
    )
    state.stats.record_error("connectivity", "Pre-flight Jellyfin connection failed.")
    raise SystemExit(1)


def main() -> None:
    args = parse_args()

    config_path = Path(args.config).expanduser() if args.config else default_config_path()

    operations: list[str] = []
    run_started = False
    exit_code = 0
    logging_settings: dict[str, Any] = {}

    try:
        _, logging_settings = setup_logging({"logging": {}}, args)

        if args.generate_config:
            validate_generate_config_args(sys.argv[1:])
            generate_default_config(config_path)
            raise SystemExit(0)

        try:
            cfg = load_config_from_path(config_path)
        except ConfigError as exc:
            state.log.critical(str(exc))
            state.stats.record_error("configuration", str(exc))
            raise SystemExit(1)

        cfg = apply_cli_overrides(args, cfg)

        try:
            validate_config_types(cfg)
        except ConfigError as exc:
            state.log.critical(str(exc))
            state.stats.record_error("configuration", str(exc))
            raise SystemExit(1)

        _, logging_settings = setup_logging(cfg, args)

        if args.restore_all:
            validate_restore_all_args(sys.argv[1:])
        if args.test_jf:
            validate_test_jf_args(sys.argv[1:])
        if args.restore and args.backup:
            state.log.critical("--backup cannot be used with --restore.")
            state.stats.record_error("arguments", "backup used with restore")
            raise SystemExit(1)

        force_upload_noscale = bool(cfg.get("force_upload_noscale", False))
        backup_mode = normalize_backup_mode(cfg.get("backup_mode", "partial"))
        if args.restore_all:
            operations = sorted(VALID_MODES)
        else:
            operations = ["test-jf"] if args.test_jf else parse_operations(args.mode, cfg.get("operations"))
        restore_requested = bool(args.restore or args.restore_all)
        dry_run = bool(args.dry_run or cfg.get("dry_run", False))
        writes_enabled = not dry_run
        make_backup = bool(args.backup or cfg.get("backup", False))
        backup_root = Path(cfg.get("backup_dir", "backup")).expanduser()

        log_run_start(
            config_path=config_path,
            cfg=cfg,
            operations=operations,
            dry_run=dry_run,
            writes_enabled=writes_enabled,
            backup=make_backup,
            silent=logging_settings["silent"],
            cli_level=logging_settings["cli_level"],
            file_level=logging_settings["file_level"],
            log_file=Path(logging_settings["file_path"]),
        )
        run_started = True

        if args.test_jf:
            jf_url = cfg.get("jf_url") or args.jf_url
            jf_api_key = cfg.get("jf_api_key") or args.jf_api_key
            if not jf_url or not jf_api_key:
                state.log.critical(
                    "--test-jf requires --jf-url and --jf-api-key flags or valid jf_url/jf_api_key values in config."
                )
                state.stats.record_error("test-jf", "Missing jf_url/jf_api_key")
                raise SystemExit(1)

            jf_client = build_jellyfin_client_from_config(cfg)
            ok = jf_client.test_connection()
            if ok:
                state.stats.record_success()
            else:
                state.stats.record_error("test-jf", "Connection test failed.")
            raise SystemExit(0 if ok else 1)

        if args.single and not args.mode:
            state.log.critical("--single requires an explicit --mode to determine target type.")
            state.stats.record_error("arguments", "--single missing --mode")
            raise SystemExit(1)
        warn_unused_cli_overrides(args, operations)

        jf_client: JellyfinClient | None = None
        jf_url = cfg.get("jf_url")
        jf_api_key = cfg.get("jf_api_key")
        if not jf_url or not jf_api_key:
            state.log.critical(
                "jf_url and jf_api_key must be set in config (or overridden via CLI) "
                "when processing images or running outside dry-run mode."
            )
            state.stats.record_error("configuration", "Missing jf_url/jf_api_key")
            raise SystemExit(1)

        jf_client = build_jellyfin_client_from_config(cfg)
        run_preflight_check(jf_client)

        settings_by_mode: dict[str, ModeRuntimeSettings] = {}
        for mode in operations:
            validate_config_for_mode(cfg, mode)

            mode_cfg = cfg[mode]
            try:
                settings_by_mode[mode] = build_mode_runtime_settings(mode, mode_cfg, args)
            except ConfigError as exc:
                state.log.critical(str(exc))
                state.stats.record_error("configuration", str(exc))
                raise SystemExit(1)

        warn_unrecommended_aspect_ratios(settings_by_mode)

        if args.single:
            ops_set = set(operations)
            if "profile" in ops_set:
                if operations != ["profile"]:
                    state.log.critical("--single with profile mode cannot be combined with other modes.")
                    state.stats.record_error("arguments", "--single profile combined with other modes")
                    raise SystemExit(1)

                if restore_requested:
                    users = jf_client.list_users(is_disabled=False)
                    user = find_user_by_name(users, args.single)
                    if user is None:
                        state.log.critical("User '%s' not found or disabled.", args.single)
                        state.stats.record_error(args.single, "User not found or disabled")
                        raise SystemExit(1)
                    target_id = user.get("Id")
                    if not target_id:
                        state.log.critical("Resolved user '%s' is missing an Id.", args.single)
                        state.stats.record_error(args.single, "User missing Id")
                        raise SystemExit(1)
                    ok = restore_single_item_from_backup(
                        backup_root=backup_root,
                        jf_client=jf_client,
                        mode="profile",
                        target_id=target_id,
                        dry_run=dry_run,
                    )
                    raise SystemExit(0 if ok else 1)

                process_single_profile(
                    username=args.single,
                    settings=settings_by_mode["profile"],
                    dry_run=dry_run,
                    jf_client=jf_client,
                    force_upload_noscale=force_upload_noscale,
                    is_restore=False,
                    make_backup=make_backup,
                    backup_root=backup_root,
                    backup_mode=backup_mode,
                )
                raise SystemExit(0)

            # Single item id across selected item modes.
            if restore_requested:
                ok_all = True
                for mode in operations:
                    ok = restore_single_item_from_backup(
                        backup_root=backup_root,
                        jf_client=jf_client,
                        mode=mode,
                        target_id=args.single,
                        dry_run=dry_run,
                    )
                    ok_all = ok_all and ok
                raise SystemExit(0 if ok_all else 1)

            ok_all = True
            for mode in operations:
                ok = process_single_item_api(
                    item_id=args.single,
                    mode=mode,
                    settings_by_mode=settings_by_mode,
                    jf_client=cast(JellyfinClient, jf_client),
                    dry_run=dry_run,
                    force_upload_noscale=force_upload_noscale,
                    make_backup=make_backup,
                    backup_root=backup_root,
                    backup_mode=backup_mode,
                )
                ok_all = ok_all and ok
            raise SystemExit(0 if ok_all else 1)

        if restore_requested:
            if jf_client is None:
                state.log.critical("Jellyfin client is required for restore.")
                state.stats.record_error("restore", "Missing Jellyfin client")
                raise SystemExit(1)

            restore_from_backups(
                backup_root=backup_root,
                jf_client=jf_client,
                operations=operations,
                dry_run=dry_run,
            )
            raise SystemExit(0)

        opeation_modes = [m for m in operations if m in ("logo", "thumb", "backdrop")]
        if opeation_modes:
            if jf_client is None:
                state.log.critical("Jellyfin client is required for library processing.")
                state.stats.record_error("configuration", "Missing Jellyfin client")
                raise SystemExit(1)

            process_libraries_via_api(
                cfg=cfg,
                operations=opeation_modes,
                mode_settings={mode: settings_by_mode[mode] for mode in opeation_modes},
                jf_client=jf_client,
                dry_run=dry_run,
                force_upload_noscale=force_upload_noscale,
                make_backup=make_backup,
                backup_root=backup_root,
                backup_mode=backup_mode,
            )

        if "profile" in operations:
            settings = settings_by_mode["profile"]
            process_profiles(
                settings=settings,
                dry_run=dry_run,
                jf_client=cast(JellyfinClient, jf_client),
                force_upload_noscale=force_upload_noscale,
                make_backup=make_backup,
                backup_root=backup_root,
                backup_mode=backup_mode,
            )

    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
    except Exception:
        state.log.exception("Unhandled exception during run.")
        state.stats.record_error("run", "Unhandled exception")
        exit_code = 1
    finally:
        if run_started:
            if state.downscaled_images:
                state.log.info("=== DOWNSCALED IMAGES (larger than target) ===")
                for path, ow, oh, nw, nh in state.downscaled_images:
                    state.log.info(" - %s: %sx%s -> %sx%s", path, ow, oh, nw, nh)
                state.log.info("Total downscaled: %s", len(state.downscaled_images))

            if state.upscaled_images:
                state.log.info("=== UPSCALED IMAGES (smaller than target) ===")
                for path, ow, oh, nw, nh in state.upscaled_images:
                    state.log.info(" - %s: %sx%s -> %sx%s", path, ow, oh, nw, nh)
                state.log.info("Total upscaled: %s", len(state.upscaled_images))

            if state.api_failures:
                state.log.error("%s API uploads failed.", len(state.api_failures))
                for entry in state.api_failures:
                    state.log.error("API failure: %s", entry)

            log_run_summary(state.stats)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
