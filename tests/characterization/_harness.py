"""Shared helpers for CLI/config characterization tests."""

from __future__ import annotations

import re
import json
import logging
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import pytest

PREFLIGHT_EXPECTED_VALUES = {"not_reached", "mocked_ok", "mocked_fail"}
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


class _ListHandler(logging.Handler):
    """Capture log message strings into one in-memory list."""

    def __init__(self, sink: list[str]) -> None:
        super().__init__(level=logging.DEBUG)
        self._sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        self._sink.append(record.getMessage())


def _normalize_message(message: str) -> str:
    """Normalize one captured message without removing meaning-bearing text."""
    return ANSI_ESCAPE_RE.sub("", message).strip()


def merge_observed_messages(*message_sources: list[str]) -> list[str]:
    """Merge captured message lists deterministically with minimal normalization.

    Normalization policy:
    - remove ANSI color escape codes,
    - trim leading/trailing whitespace,
    - preserve exact semantic text (no token rewriting, regex matching, or reordering).
    """
    merged: list[str] = []
    seen: set[str] = set()
    for source in message_sources:
        for raw in source:
            normalized = _normalize_message(raw)
            if not normalized or normalized in seen:
                continue
            merged.append(normalized)
            seen.add(normalized)
    return merged


@contextmanager
def capture_logger_messages(logger_name: str) -> Iterator[list[str]]:
    """Capture messages for one logger with scoped install/uninstall lifecycle."""
    logger = logging.getLogger(logger_name)
    captured: list[str] = []
    handler = _ListHandler(captured)
    logger.addHandler(handler)
    try:
        yield captured
    finally:
        try:
            logger.removeHandler(handler)
        except ValueError:
            # Allow safe cleanup when test code reconfigures handlers in-flight.
            pass


@dataclass(frozen=True)
class CliRunResult:
    """Normalized outcome data for one CLI characterization case."""

    exit_code: int
    stats: dict[str, int]
    messages: list[str]
    preflight_calls: int


def load_baseline_cases(path: Path) -> dict[str, Any]:
    """Load and return the baseline `cases` mapping from a JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1:
        raise AssertionError(f"Unsupported baseline version in {path}: {payload}")
    cases = payload.get("cases")
    if not isinstance(cases, dict):
        raise AssertionError(f"Baseline is missing object 'cases': {path}")
    return cases


def assert_expected_messages(
    expected_tokens: list[str] | None,
    observed_messages: list[str],
) -> None:
    """Assert all expected message tokens exist in observed logs/messages."""
    if not expected_tokens:
        return
    haystack = "\n".join(observed_messages)
    for token in expected_tokens:
        assert token in haystack, f"Missing expected message token: {token!r}"


def assert_expected_stats_subset(
    expected_stats: dict[str, int] | None,
    observed_stats: dict[str, int],
) -> None:
    """Assert only provided stat keys match observed values."""
    if not expected_stats:
        return
    for key, expected in expected_stats.items():
        assert key in observed_stats, f"Unknown stats key in baseline: {key}"
        assert observed_stats[key] == expected, (
            f"Stat mismatch for {key}: expected {expected}, got {observed_stats[key]}"
        )


def assert_expected_preflight(
    expected_preflight: str | None,
    observed_calls: int,
) -> None:
    """Assert preflight call behavior based on the expected preflight mode."""
    if expected_preflight is None:
        return
    assert expected_preflight in PREFLIGHT_EXPECTED_VALUES, (
        f"Unexpected expected_preflight value: {expected_preflight}"
    )
    if expected_preflight == "not_reached":
        assert observed_calls == 0, "Preflight was called unexpectedly."
    else:
        assert observed_calls == 1, "Preflight was expected exactly once."


def assert_effective_config_subset(
    expected_effective: dict[str, Any] | None,
    observed_effective: dict[str, Any],
) -> None:
    """Assert expected effective-config keys exist and match observed values."""
    if not expected_effective:
        return
    for key, expected_value in expected_effective.items():
        assert key in observed_effective, f"Missing effective-config key: {key}"
        assert observed_effective[key] == expected_value, (
            f"Effective config mismatch for {key}: "
            f"expected {expected_value!r}, got {observed_effective[key]!r}"
        )


def build_minimal_runtime_config_text(
    *,
    operations: str = 'operations = ["logo"]',
    logo_size: tuple[int, int] = (800, 310),
    thumb_size: tuple[int, int] = (1000, 562),
    backdrop_size: tuple[int, int] = (1920, 1080),
    profile_size: tuple[int, int] = (512, 512),
) -> str:
    """Build a minimal TOML config suitable for deterministic CLI runs."""
    return (
        'jf_url = "https://demo.example.com"\n'
        'jf_api_key = "token"\n'
        f"{operations}\n"
        "dry_run = true\n"
        "\n"
        "[logging]\n"
        "file_enabled = false\n"
        "silent = true\n"
        "\n"
        "[logo]\n"
        f"width = {logo_size[0]}\n"
        f"height = {logo_size[1]}\n"
        "no_upscale = false\n"
        "no_downscale = false\n"
        'padding = "add"\n'
        "\n"
        "[thumb]\n"
        f"width = {thumb_size[0]}\n"
        f"height = {thumb_size[1]}\n"
        "no_upscale = false\n"
        "no_downscale = false\n"
        "jpeg_quality = 85\n"
        "\n"
        "[backdrop]\n"
        f"width = {backdrop_size[0]}\n"
        f"height = {backdrop_size[1]}\n"
        "no_upscale = false\n"
        "no_downscale = false\n"
        "jpeg_quality = 85\n"
        "\n"
        "[profile]\n"
        f"width = {profile_size[0]}\n"
        f"height = {profile_size[1]}\n"
        "no_upscale = false\n"
        "no_downscale = false\n"
        "webp_quality = 80\n"
    )


def run_cli_case(
    *,
    argv: list[str],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    preflight_mode: str,
    patch_profile_single: bool = False,
    patch_item_single: bool = False,
) -> CliRunResult:
    """Execute `jfin.cli.main` with deterministic network/preflight behavior."""
    from jfin import cli, state

    # Ensure deterministic, self-contained case execution even without global fixtures.
    state.reset_state()

    assert preflight_mode in PREFLIGHT_EXPECTED_VALUES, (
        f"Unsupported preflight mode {preflight_mode!r}"
    )

    call_counter = {"preflight": 0}

    class DummyClient:
        """Simple stand-in client to avoid live network calls in tests."""

        def test_connection(self) -> bool:
            return True

        def list_users(self, is_disabled: bool = False) -> list[dict[str, Any]]:
            return []

    def fake_preflight(_jf_client: Any) -> None:
        """Track preflight calls and optionally force failure."""
        call_counter["preflight"] += 1
        if preflight_mode == "mocked_fail":
            raise SystemExit(1)

    monkeypatch.setattr(
        cli, "build_jellyfin_client_from_config", lambda _cfg: DummyClient()
    )
    monkeypatch.setattr(cli, "run_preflight_check", fake_preflight)

    if patch_profile_single:
        monkeypatch.setattr(
            cli,
            "process_single_profile",
            lambda **_kwargs: None,
        )
    if patch_item_single:
        monkeypatch.setattr(
            cli,
            "process_single_item_api",
            lambda **_kwargs: True,
        )

    captured_from_runtime_logger: list[str] = []
    attached_handlers: list[tuple[logging.Logger, logging.Handler]] = []
    original_setup_logging = cli.setup_logging

    def wrapped_setup_logging(
        cfg: dict[str, Any], args: Any
    ) -> tuple[Any, dict[str, Any]]:
        adapter, settings = original_setup_logging(cfg, args)
        handler = _ListHandler(captured_from_runtime_logger)
        adapter.logger.addHandler(handler)
        attached_handlers.append((adapter.logger, handler))
        return adapter, settings

    monkeypatch.setattr(cli, "setup_logging", wrapped_setup_logging)
    monkeypatch.setattr(sys, "argv", ["jfin", *argv])
    try:
        with caplog.at_level(logging.DEBUG):
            with pytest.raises(SystemExit) as excinfo:
                cli.main()
    finally:
        for logger, handler in attached_handlers:
            try:
                logger.removeHandler(handler)
            except ValueError:
                pass

    raw_code = excinfo.value.code
    exit_code = raw_code if isinstance(raw_code, int) else 1
    observed_stats = {
        "errors": state.stats.errors,
        "warnings": state.stats.warnings,
        "successes": state.stats.successes,
    }
    observed_messages = merge_observed_messages(
        [record.getMessage() for record in caplog.records],
        captured_from_runtime_logger,
    )

    # Avoid leaking run state to subsequent calls if this helper is reused directly.
    state.reset_state()

    return CliRunResult(
        exit_code=exit_code,
        stats=observed_stats,
        messages=observed_messages,
        preflight_calls=call_counter["preflight"],
    )
