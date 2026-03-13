"""Provide cli runtime helpers."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, cast

from .client import JellyfinClient
from .config import ModeRuntimeSettings


def run_main(
    *,
    args: argparse.Namespace,
    argv: list[str],
    cli_module: Any,
    state_module: Any,
) -> int:
    """Run main."""
    config_path = (
        Path(args.config).expanduser()
        if args.config
        else cli_module.default_config_path()
    )
    operations: list[str] = []
    run_started = False
    exit_code = 0
    logging_settings: dict[str, Any] = {}
    try:
        _, logging_settings = cli_module.setup_logging({"logging": {}}, args)
        if args.generate_config:
            cli_module.validate_generate_config_args(argv)
            cli_module._enforce_route("config_init", "n/a")
            cli_module.generate_default_config(config_path)
            return 0
        try:
            cfg = cli_module.load_config_from_path(config_path)
        except cli_module.ConfigError as exc:
            state_module.log.critical(str(exc))
            state_module.stats.record_error("configuration", str(exc))
            return 1
        cfg = cli_module.apply_cli_overrides(args, cfg)
        try:
            cli_module.validate_config_types(cfg)
        except cli_module.ConfigError as exc:
            state_module.log.critical(str(exc))
            state_module.stats.record_error("configuration", str(exc))
            return 1
        _, logging_settings = cli_module.setup_logging(cfg, args)
        if args.restore_all:
            cli_module.validate_restore_all_args(argv)
        if args.test_jf:
            cli_module.validate_test_jf_args(argv)
        if args.restore and args.backup:
            state_module.log.critical("--backup cannot be used with --restore.")
            state_module.stats.record_error("arguments", "backup used with restore")
            return 1

        force_upload_noscale = bool(cfg.get("force_upload_noscale", False))
        backup_mode = cli_module.normalize_backup_mode(
            cfg.get("backup_mode", "partial")
        )
        if args.restore_all:
            operations = sorted(cli_module.VALID_MODES)
        else:
            operations = (
                ["test-jf"]
                if args.test_jf
                else cli_module.parse_operations(args.mode, cfg.get("operations"))
            )
        restore_requested = bool(args.restore or args.restore_all)
        dry_run = bool(args.dry_run or cfg.get("dry_run", False))
        writes_enabled = not dry_run
        make_backup = bool(args.backup or cfg.get("backup", False))
        backup_root = Path(cfg.get("backup_dir", "backup")).expanduser()
        cli_module.log_run_start(
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
            cli_module._enforce_route("test_connection", "n/a")
            jf_url = cfg.get("jf_url") or args.jf_url
            jf_api_key = cfg.get("jf_api_key") or args.jf_api_key
            if not jf_url or not jf_api_key:
                state_module.log.critical(
                    "--test-jf requires --jf-url and --jf-api-key flags or valid jf_url/jf_api_key values in config."
                )
                state_module.stats.record_error("test-jf", "Missing jf_url/jf_api_key")
                return 1

            test_jf_client = cli_module.build_jellyfin_client_from_config(cfg)
            ok = test_jf_client.test_connection()
            if ok:
                state_module.stats.record_success()
            else:
                state_module.stats.record_error("test-jf", "Connection test failed.")
            return 0 if ok else 1
        if restore_requested:
            cli_module._enforce_route("restore", "logo|thumb|backdrop|profile")
        if args.single and not args.mode:
            state_module.log.critical(
                "--single requires an explicit --mode to determine target type."
            )
            state_module.stats.record_error("arguments", "--single missing --mode")
            return 1
        cli_module.warn_unused_cli_overrides(args, operations)
        jf_client: JellyfinClient | None = None
        jf_url = cfg.get("jf_url")
        jf_api_key = cfg.get("jf_api_key")
        if not jf_url or not jf_api_key:
            state_module.log.critical(
                "jf_url and jf_api_key must be set in config (or overridden via CLI) when processing images or running outside dry-run mode."
            )
            state_module.stats.record_error(
                "configuration", "Missing jf_url/jf_api_key"
            )
            return 1
        jf_client = cli_module.build_jellyfin_client_from_config(cfg)
        cli_module.run_preflight_check(jf_client)
        settings_by_mode: dict[str, ModeRuntimeSettings] = {}
        for mode in operations:
            cli_module.validate_config_for_mode(cfg, mode)
            mode_cfg = cfg[mode]
            try:
                settings_by_mode[mode] = cli_module.build_mode_runtime_settings(
                    mode, mode_cfg, args
                )
            except cli_module.ConfigError as exc:
                state_module.log.critical(str(exc))
                state_module.stats.record_error("configuration", str(exc))
                return 1
        cli_module.warn_unrecommended_aspect_ratios(settings_by_mode)
        if not restore_requested:
            for route_mode in operations:
                if route_mode in cli_module.VALID_MODES:
                    cli_module._enforce_route("run", route_mode)
        if args.single:
            ops_set = set(operations)
            if "profile" in ops_set:
                if operations != ["profile"]:
                    state_module.log.critical(
                        "--single with profile mode cannot be combined with other modes."
                    )
                    state_module.stats.record_error(
                        "arguments", "--single profile combined with other modes"
                    )
                    return 1
                if restore_requested:
                    users = jf_client.list_users(is_disabled=False)
                    user = cli_module.find_user_by_name(users, args.single)
                    if user is None:
                        state_module.log.critical(
                            "User '%s' not found or disabled.", args.single
                        )
                        state_module.stats.record_error(
                            args.single, "User not found or disabled"
                        )
                        return 1
                    target_id = user.get("Id")
                    if not target_id:
                        state_module.log.critical(
                            "Resolved user '%s' is missing an Id.", args.single
                        )
                        state_module.stats.record_error(args.single, "User missing Id")
                        return 1
                    ok = cli_module.restore_single_item_from_backup(
                        backup_root=backup_root,
                        jf_client=jf_client,
                        mode="profile",
                        target_id=target_id,
                        dry_run=dry_run,
                    )
                    return 0 if ok else 1
                cli_module.process_single_profile(
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
                return 0
            if restore_requested:
                ok_all = True
                for mode in operations:
                    ok = cli_module.restore_single_item_from_backup(
                        backup_root=backup_root,
                        jf_client=jf_client,
                        mode=mode,
                        target_id=args.single,
                        dry_run=dry_run,
                    )
                    ok_all = ok_all and ok
                return 0 if ok_all else 1
            ok_all = True
            for mode in operations:
                ok = cli_module.process_single_item_api(
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
            return 0 if ok_all else 1
        if restore_requested:
            if jf_client is None:
                state_module.log.critical("Jellyfin client is required for restore.")
                state_module.stats.record_error("restore", "Missing Jellyfin client")
                return 1
            cli_module.restore_from_backups(
                backup_root=backup_root,
                jf_client=jf_client,
                operations=operations,
                dry_run=dry_run,
            )
            return 0
        operation_modes = [m for m in operations if m in ("logo", "thumb", "backdrop")]
        if operation_modes:
            if jf_client is None:
                state_module.log.critical(
                    "Jellyfin client is required for library processing."
                )
                state_module.stats.record_error(
                    "configuration", "Missing Jellyfin client"
                )
                return 1
            cli_module.process_libraries_via_api(
                cfg=cfg,
                operations=operation_modes,
                mode_settings={
                    mode: settings_by_mode[mode] for mode in operation_modes
                },
                jf_client=jf_client,
                dry_run=dry_run,
                force_upload_noscale=force_upload_noscale,
                make_backup=make_backup,
                backup_root=backup_root,
                backup_mode=backup_mode,
            )
        if "profile" in operations:
            settings = settings_by_mode["profile"]
            cli_module.process_profiles(
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
        state_module.log.exception("Unhandled exception during run.")
        state_module.stats.record_error("run", "Unhandled exception")
        exit_code = 1
    finally:
        if run_started:
            if state_module.downscaled_images:
                state_module.log.info("=== DOWNSCALED IMAGES (larger than target) ===")
                for path, ow, oh, nw, nh in state_module.downscaled_images:
                    state_module.log.info(" - %s: %sx%s -> %sx%s", path, ow, oh, nw, nh)
                state_module.log.info(
                    "Total downscaled: %s", len(state_module.downscaled_images)
                )
            if state_module.upscaled_images:
                state_module.log.info("=== UPSCALED IMAGES (smaller than target) ===")
                for path, ow, oh, nw, nh in state_module.upscaled_images:
                    state_module.log.info(" - %s: %sx%s -> %sx%s", path, ow, oh, nw, nh)
                state_module.log.info(
                    "Total upscaled: %s", len(state_module.upscaled_images)
                )
            if state_module.api_failures:
                state_module.log.error(
                    "%s API uploads failed.", len(state_module.api_failures)
                )
                for entry in state_module.api_failures:
                    state_module.log.error("API failure: %s", entry)
            cli_module.log_run_summary(state_module.stats)
    return exit_code
