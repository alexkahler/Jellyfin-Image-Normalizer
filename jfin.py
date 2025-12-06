#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Any, cast

from jfin_core import state
from jfin_core.backup import normalize_backup_mode
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
from jfin_core.constants import DEFAULT_CONFIG_NAME, VALID_MODES
from jfin_core.discovery import find_user_by_name
from jfin_core.logging_utils import log_run_start, log_run_summary, setup_logging
from jfin_core.pipeline import (
    process_libraries_via_api,
    process_profiles,
    process_single_profile,
    process_single_item_api,
    restore_from_backups,
    restore_single_from_backup,
)


def parse_args() -> argparse.Namespace:
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
            "Image types to handle, e.g. 'logo', 'thumb', 'profile', or a pipe-separated "
            "list like '"'logo|thumb'"'. Overrides the config 'operations' value if provided."
        ),
    )

    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Override target canvas width for this run.",
    )

    parser.add_argument(
        "--height",
        type=int,
        default=None,
        help="Override target canvas height for this run.",
    )

    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=None,
        help="JPEG quality for thumb output (1-95). Overrides config thumb.jpeg_quality.",
    )

    parser.add_argument(
        "--webp-quality",
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
            "Process a single target: username for profile mode, or itemId for logo/thumb."
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
        "--no-padding",
        action="store_true",
        help="Do not pad logos to canvas; output is resized only (logo mode).",
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
        "--operator",
        help="Operator username to run discovery as (overrides config.operator.username).",
    )

    parser.add_argument(
        "--libraries",
        help="Comma- or pipe-separated library names to include (overrides config.libraries.names).",
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


def warn_unused_cli_overrides(args: argparse.Namespace, operations: list[str]) -> None:
    """
    Emit warnings for CLI overrides that have no effect with the requested operations.

    Examples: --jpeg-quality without thumb mode, --webp-quality without profile mode, or --no-padding without logo mode.
    Each warning is logged and counted so the operator is aware that a flag was ignored.
    """
    ops = set(operations)
    if args.jpeg_quality is not None and "thumb" not in ops:
        state.log.warning("--jpeg-quality has no effect because 'thumb' mode is not selected.")
        state.stats.record_warning()
    if args.webp_quality is not None and "profile" not in ops:
        state.log.warning("--webp-quality has no effect because 'profile' mode is not selected.")
        state.stats.record_warning()
    if args.no_padding and "logo" not in ops:
        state.log.warning("--no-padding has no effect because 'logo' mode is not selected.")
        state.stats.record_warning()


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
                state.stats.record_error("test-jf", "Connection test failed")
            raise SystemExit(0 if ok else 1)

        if args.single and len(operations) != 1:
            state.log.critical("--single can only be used with one mode/operation.")
            state.stats.record_error("arguments", "--single used with multiple modes")
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

            if args.single and not restore_requested:
                if mode == "profile":
                    process_single_profile(
                        username=args.single,
                        settings=settings_by_mode[mode],
                        dry_run=dry_run,
                        jf_client=jf_client,
                        force_upload_noscale=force_upload_noscale,
                        is_restore=args.restore,
                        make_backup=make_backup,
                        backup_root=backup_root,
                        backup_mode=backup_mode,
                    )
                    raise SystemExit(0)

                if mode in ("logo", "thumb"):
                    process_single_item_api(
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
                    raise SystemExit(0)

                state.log.critical("--single not supported for mode '%s'.", mode)
                state.stats.record_error("arguments", f"--single not supported for mode {mode}")
                raise SystemExit(1)

        if restore_requested:
            if jf_client is None:
                state.log.critical("Jellyfin client is required for restore.")
                state.stats.record_error("restore", "Missing Jellyfin client")
                raise SystemExit(1)
            if args.single:
                mode = operations[0]
                if mode == "profile":
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
                    ok = restore_single_from_backup(
                        backup_root=backup_root,
                        jf_client=jf_client,
                        mode=mode,
                        target_id=target_id,
                        dry_run=dry_run,
                    )
                else:
                    ok = restore_single_from_backup(
                        backup_root=backup_root,
                        jf_client=jf_client,
                        mode=mode,
                        target_id=args.single,
                        dry_run=dry_run,
                    )
                raise SystemExit(0 if ok else 1)

            restore_from_backups(
                backup_root=backup_root,
                jf_client=jf_client,
                operations=operations,
                dry_run=dry_run,
            )
            raise SystemExit(0)

        library_modes = [m for m in operations if m in ("logo", "thumb")]
        if library_modes:
            if jf_client is None:
                state.log.critical("Jellyfin client is required for library processing.")
                state.stats.record_error("configuration", "Missing Jellyfin client")
                raise SystemExit(1)

            process_libraries_via_api(
                cfg=cfg,
                operations=library_modes,
                mode_settings={mode: settings_by_mode[mode] for mode in library_modes},
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
