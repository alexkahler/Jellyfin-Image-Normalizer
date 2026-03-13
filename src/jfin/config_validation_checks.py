"""Provide type-validation checks for loaded config dictionaries."""

from __future__ import annotations

from typing import Any, Callable, TypeGuard


def validate_config_types(
    cfg: dict[str, Any],
    *,
    parse_item_types_fn: Callable[[Any], list[str]],
    config_error_type: type[Exception],
    state_module: Any,
) -> None:
    """Validate configuration type and range constraints."""
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
        parse_item_types_fn(cfg.get("item_types"))
    except config_error_type as exc:
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
                state_module.log.warning(
                    "Config key 'logo.no_padding' has been removed. "
                    'Use logo.padding = "none" instead of no_padding=true.'
                )
                state_module.stats.record_warning()
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
        raise config_error_type("Invalid configuration values: " + "; ".join(errors))
