"""Characterization tests for CLI behavior contract rows in parity matrix."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.characterization._harness import (
    assert_expected_messages,
    assert_expected_preflight,
    assert_expected_stats_subset,
    build_minimal_runtime_config_text,
    load_baseline_cases,
    run_cli_case,
)

try:
    import tomllib  # noqa: F401

    HAS_TOMLLIB = True
except ModuleNotFoundError:  # pragma: no cover - local py3.10 fallback
    HAS_TOMLLIB = False

pytestmark = pytest.mark.skipif(
    not HAS_TOMLLIB,
    reason="CLI characterization requires Python 3.11+ (tomllib).",
)


BASELINE_PATH = (
    Path(__file__).resolve().parents[1] / "baselines" / "cli_contract_baseline.json"
)


@pytest.fixture(scope="module")
def cli_cases() -> dict[str, dict[str, object]]:
    """Load and cache CLI characterization case expectations."""
    return load_baseline_cases(BASELINE_PATH)


def _write_config(
    tmp_path: Path,
    *,
    operations: str = 'operations = ["logo"]',
    logo_size: tuple[int, int] = (800, 310),
) -> Path:
    """Write a deterministic runtime config for CLI characterization runs."""
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        build_minimal_runtime_config_text(
            operations=operations,
            logo_size=logo_size,
        ),
        encoding="utf-8",
    )
    return config_path


def _assert_case(
    case: dict[str, object],
    result,
) -> None:
    """Assert shared baseline expectations against one CLI run result."""
    assert result.exit_code == case["expected_exit_code"]
    assert_expected_stats_subset(case.get("expected_stats"), result.stats)
    assert_expected_messages(case.get("expected_messages"), result.messages)
    assert_expected_preflight(case.get("expected_preflight"), result.preflight_calls)


def test_cli_restore_all_blocks_operational_flags(
    cli_cases: dict[str, dict[str, object]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """CLI-RESTORE-001 should reject mixed restore-all and operational flags."""
    case = cli_cases["CLI-RESTORE-001"]
    config_path = _write_config(tmp_path)
    result = run_cli_case(
        argv=["--config", str(config_path), "--restore-all", "--restore"],
        monkeypatch=monkeypatch,
        caplog=caplog,
        preflight_mode=str(case.get("expected_preflight")),
    )
    _assert_case(case, result)


def test_cli_generate_config_blocks_operational_flags(
    cli_cases: dict[str, dict[str, object]],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """CLI-GENCFG-001 should reject operational flags with --generate-config."""
    case = cli_cases["CLI-GENCFG-001"]
    result = run_cli_case(
        argv=["--generate-config", "--mode", "logo"],
        monkeypatch=monkeypatch,
        caplog=caplog,
        preflight_mode=str(case.get("expected_preflight")),
    )
    _assert_case(case, result)


def test_cli_test_jf_blocks_operational_flags(
    cli_cases: dict[str, dict[str, object]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """CLI-TESTJF-001 should reject operational flags with --test-jf."""
    case = cli_cases["CLI-TESTJF-001"]
    config_path = _write_config(tmp_path)
    result = run_cli_case(
        argv=["--config", str(config_path), "--test-jf", "--mode", "logo"],
        monkeypatch=monkeypatch,
        caplog=caplog,
        preflight_mode=str(case.get("expected_preflight")),
    )
    _assert_case(case, result)


def test_cli_single_requires_explicit_mode(
    cli_cases: dict[str, dict[str, object]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """CLI-SINGLE-001 should require explicit --mode for --single runs."""
    case = cli_cases["CLI-SINGLE-001"]
    config_path = _write_config(tmp_path)
    result = run_cli_case(
        argv=["--config", str(config_path), "--single", "item123"],
        monkeypatch=monkeypatch,
        caplog=caplog,
        preflight_mode=str(case.get("expected_preflight")),
    )
    _assert_case(case, result)


def test_cli_warns_for_incompatible_overrides(
    cli_cases: dict[str, dict[str, object]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """CLI-OVERRIDE-001 should preserve warning behavior for unused overrides."""
    case = cli_cases["CLI-OVERRIDE-001"]
    config_path = _write_config(tmp_path, operations='operations = ["profile"]')
    result = run_cli_case(
        argv=[
            "--config",
            str(config_path),
            "--mode",
            "profile",
            "--single",
            "demo-user",
            "--thumb-jpeg-quality",
            "90",
        ],
        monkeypatch=monkeypatch,
        caplog=caplog,
        preflight_mode=str(case.get("expected_preflight")),
        patch_profile_single=True,
    )
    _assert_case(case, result)


def test_cli_warns_for_unrecommended_aspect_ratio(
    cli_cases: dict[str, dict[str, object]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """CLI-ASPECT-001 should preserve warning behavior for odd aspect ratios."""
    case = cli_cases["CLI-ASPECT-001"]
    config_path = _write_config(
        tmp_path,
        operations='operations = ["logo"]',
        logo_size=(800, 520),
    )
    result = run_cli_case(
        argv=["--config", str(config_path), "--mode", "logo", "--single", "item123"],
        monkeypatch=monkeypatch,
        caplog=caplog,
        preflight_mode=str(case.get("expected_preflight")),
        patch_item_single=True,
    )
    _assert_case(case, result)
