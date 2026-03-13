"""Provide CLI argument-combination validation helpers."""

from __future__ import annotations

from . import state

CONFIG_ARG = "--config"  # nosec B105


class CliValidationError(RuntimeError):
    """Raised when restricted command flags are combined with unsupported args."""


def _collect_unexpected_tokens(
    argv: list[str], allowed: set[str], value_flags: set[str]
) -> list[str]:
    """Collect unsupported tokens for one bounded CLI mode."""
    extras: list[str] = []
    skip_next = False

    for token in argv:
        if skip_next:
            skip_next = False
            continue
        if token in value_flags:
            skip_next = True
            continue
        if any(token.startswith(f"{flag}=") for flag in value_flags):
            continue
        if token in allowed:
            continue
        extras.append(token)

    return extras


def _raise_invalid_combination(
    command_flag: str, extras: list[str], stats_detail: str
) -> None:
    """Raise a fail-closed CLI validation error for one command mode."""
    state.log.critical(
        "%s cannot be combined with other arguments (found: %s).",
        command_flag,
        ", ".join(extras),
    )
    state.stats.record_error("arguments", stats_detail)
    raise CliValidationError(stats_detail)


def validate_generate_config_args(argv: list[str]) -> None:
    """Validate generate-config argument combinations."""
    allowed = {"--generate-config", CONFIG_ARG, "--silent", "-s", "--verbose", "-v"}
    extras = _collect_unexpected_tokens(argv, allowed, {CONFIG_ARG})
    if extras:
        _raise_invalid_combination(
            "--generate-config", extras, "generate-config combined with other args"
        )


def validate_restore_all_args(argv: list[str]) -> None:
    """Validate restore-all argument combinations."""
    allowed = {"--restore-all", CONFIG_ARG, "--silent", "-s", "--verbose", "-v"}
    extras = _collect_unexpected_tokens(argv, allowed, {CONFIG_ARG})
    if extras:
        _raise_invalid_combination(
            "--restore-all", extras, "restore-all combined with other args"
        )


def validate_test_jf_args(argv: list[str]) -> None:
    """Validate test-jf argument combinations."""
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
    value_flags = {CONFIG_ARG, "--jf-url", "--jf-api-key", "--jf-delay-ms"}
    extras = _collect_unexpected_tokens(argv, allowed, value_flags)
    if extras:
        _raise_invalid_combination(
            "--test-jf", extras, "test-jf combined with other args"
        )
