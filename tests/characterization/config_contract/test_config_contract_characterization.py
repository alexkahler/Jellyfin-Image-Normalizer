"""Characterization tests for config behavior contract rows in parity matrix."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

try:
    import tomllib  # noqa: F401

    HAS_TOMLLIB = True
except ModuleNotFoundError:  # pragma: no cover - local py3.10 fallback
    HAS_TOMLLIB = False

if HAS_TOMLLIB:
    from jfin.config import (
        ConfigError,
        apply_cli_overrides,
        build_discovery_settings,
        build_mode_runtime_settings,
        load_config_from_path,
        parse_operations,
        validate_config_types,
    )
else:  # pragma: no cover - runtime guard for local py3.10 collection
    ConfigError = Exception
    apply_cli_overrides = None
    build_discovery_settings = None
    build_mode_runtime_settings = None
    load_config_from_path = None
    parse_operations = None
    validate_config_types = None

from tests.characterization._harness import (
    assert_effective_config_subset,
    assert_expected_messages,
    assert_expected_preflight,
    load_baseline_cases,
)

pytestmark = pytest.mark.skipif(
    not HAS_TOMLLIB,
    reason="Config characterization requires Python 3.11+ (tomllib).",
)


BASELINE_PATH = (
    Path(__file__).resolve().parents[1] / "baselines" / "config_contract_baseline.json"
)


@pytest.fixture(scope="module")
def config_cases() -> dict[str, dict[str, object]]:
    """Load and cache config characterization case expectations."""
    return load_baseline_cases(BASELINE_PATH)


def _assert_config_case(
    case: dict[str, object],
    *,
    observed_effective: dict[str, object],
    observed_messages: list[str] | None = None,
) -> None:
    """Assert shared baseline expectations for config characterization cases."""
    assert case["expected_exit_code"] == 0
    assert_expected_preflight(case.get("expected_preflight"), observed_calls=0)
    assert_expected_messages(case.get("expected_messages"), observed_messages or [])
    assert_effective_config_subset(
        case.get("expected_effective_config"),
        observed_effective,
    )


def test_config_rejects_non_toml_paths(
    config_cases: dict[str, dict[str, object]],
    tmp_path: Path,
) -> None:
    """CFG-TOML-001 should reject non-TOML config paths."""
    case = config_cases["CFG-TOML-001"]
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ConfigError) as excinfo:
        load_config_from_path(config_path)

    _assert_config_case(
        case,
        observed_effective={"rejects_non_toml": True},
        observed_messages=[str(excinfo.value)],
    )


def test_config_parses_toml_and_builds_mode_settings(
    config_cases: dict[str, dict[str, object]],
    tmp_path: Path,
) -> None:
    """CFG-TOML-002 should preserve TOML parsing and mode runtime mapping."""
    case = config_cases["CFG-TOML-002"]
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
        jf_url = "https://demo.example.com"
        jf_api_key = "token"
        operations = ["logo"]

        [logo]
        width = 640
        height = 360
        no_upscale = true
        no_downscale = false
        padding = "none"
        """,
        encoding="utf-8",
    )

    cfg = load_config_from_path(config_path)
    validate_config_types(cfg)
    ops = parse_operations(None, cfg["operations"])
    args = argparse.Namespace(
        logo_target_size=None,
        thumb_target_size=None,
        backdrop_target_size=None,
        profile_target_size=None,
        no_upscale=False,
        no_downscale=False,
        logo_padding=None,
        thumb_jpeg_quality=None,
        backdrop_jpeg_quality=None,
        profile_webp_quality=None,
        item_types=None,
    )
    settings = build_mode_runtime_settings("logo", cfg["logo"], args)

    _assert_config_case(
        case,
        observed_effective={
            "operations": ops,
            "logo_width": settings.target_width,
            "logo_height": settings.target_height,
            "logo_allow_upscale": settings.allow_upscale,
            "logo_padding": settings.logo_padding,
        },
    )


def test_config_rejects_invalid_types(
    config_cases: dict[str, dict[str, object]],
    tmp_path: Path,
) -> None:
    """CFG-TYPE-001 should preserve invalid type rejection semantics."""
    case = config_cases["CFG-TYPE-001"]
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
        jf_url = "https://demo.example.com"
        jf_api_key = "token"
        operations = 123
        backup = "yes"

        [logo]
        width = "wide"
        height = 200
        no_upscale = false
        no_downscale = false
        """,
        encoding="utf-8",
    )

    cfg = load_config_from_path(config_path)
    with pytest.raises(ConfigError) as excinfo:
        validate_config_types(cfg)

    _assert_config_case(
        case,
        observed_effective={"invalid_types_rejected": True},
        observed_messages=[str(excinfo.value)],
    )


def test_config_requires_core_fields(
    config_cases: dict[str, dict[str, object]],
) -> None:
    """CFG-CORE-001 should preserve missing core-field failures."""
    case = config_cases["CFG-CORE-001"]
    with pytest.raises(ConfigError) as excinfo:
        validate_config_types({})

    _assert_config_case(
        case,
        observed_effective={"missing_core_fields_rejected": True},
        observed_messages=[str(excinfo.value)],
    )


def test_config_parse_operations_dedupes_and_orders(
    config_cases: dict[str, dict[str, object]],
) -> None:
    """CFG-OPS-001 should preserve operation dedupe/order behavior."""
    case = config_cases["CFG-OPS-001"]
    operations = parse_operations("logo|thumb|logo", None)
    _assert_config_case(
        case,
        observed_effective={"operations": operations},
    )


def test_config_build_discovery_settings_maps_modes_and_filters(
    config_cases: dict[str, dict[str, object]],
) -> None:
    """CFG-DISC-001 should preserve discovery settings mapping behavior."""
    case = config_cases["CFG-DISC-001"]
    settings = build_discovery_settings(
        {
            "libraries": {"names": ["Movies", "TV"]},
            "item_types": "series",
        },
        ["logo", "profile"],
    )
    _assert_config_case(
        case,
        observed_effective={
            "include_item_types": settings.include_item_types,
            "enable_image_types": settings.enable_image_types,
            "library_names": settings.library_names,
        },
    )


def test_config_apply_cli_overrides_applies_target_size(
    config_cases: dict[str, dict[str, object]],
) -> None:
    """CFG-OVERRIDE-001 should preserve mode size override behavior."""
    case = config_cases["CFG-OVERRIDE-001"]
    args = argparse.Namespace(
        jf_url=None,
        jf_api_key=None,
        libraries=None,
        item_types=None,
        dry_run=False,
        backup=False,
        logo_target_size=(321, 123),
        thumb_target_size=None,
        backdrop_target_size=None,
        profile_target_size=None,
        no_upscale=False,
        no_downscale=False,
        logo_padding=None,
        thumb_jpeg_quality=None,
        backdrop_jpeg_quality=None,
        profile_webp_quality=None,
        jf_delay_ms=None,
        force_upload_noscale=False,
    )
    merged = apply_cli_overrides(args, {"jf_url": "u", "jf_api_key": "k"})
    _assert_config_case(
        case,
        observed_effective={
            "logo_width": merged["logo"]["width"],
            "logo_height": merged["logo"]["height"],
        },
    )
