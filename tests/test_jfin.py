import argparse
import sys

import pytest

from jfin import (
    main,
    parse_args,
    validate_generate_config_args,
    validate_restore_all_args,
    validate_test_jf_args,
    warn_unused_cli_overrides,
)
from jfin_core import state


@pytest.mark.parametrize(
    "argv",
    [
        ["--restore-all", "--restore"],
        ["--restore-all", "--backup"],
        ["--restore-all", "--mode", "logo"],
        ["--restore-all", "--thumb-target-size", "100x100"],
    ],
)
def test_validate_restore_all_args_blocks_operational_flags(argv):
    with pytest.raises(SystemExit):
        validate_restore_all_args(argv)
    assert state.stats.errors == 1


def test_validate_restore_all_args_allows_config_and_logging():
    validate_restore_all_args(
        ["--restore-all", "--config", "myconfig.toml", "-s", "--verbose"]
    )
    assert state.stats.errors == 0


@pytest.mark.parametrize(
    "argv",
    [
        ["--generate-config", "--mode", "logo"],
        ["--generate-config", "--restore"],
        ["--generate-config", "--thumb-jpeg-quality", "90"],
    ],
)
def test_validate_generate_config_args_blocks_operational_flags(argv):
    with pytest.raises(SystemExit):
        validate_generate_config_args(argv)
    assert state.stats.errors == 1


@pytest.mark.parametrize(
    "argv",
    [
        ["--test-jf", "--mode", "logo"],
        ["--test-jf", "--restore"],
        ["--test-jf", "--backup"],
        ["--test-jf", "--thumb-target-size", "100x100"],
    ],
)
def test_validate_test_jf_args_blocks_operational_flags(argv):
    with pytest.raises(SystemExit):
        validate_test_jf_args(argv)
    assert state.stats.errors == 1


@pytest.mark.parametrize(
    "argv",
    [
        ["--test-jf", "--jf-url", "https://example.com", "--jf-api-key", "token"],
        ["--test-jf", "--config", "myconfig.toml", "--verbose"],
        ["--test-jf", "--jf-delay-ms", "250"],
    ],
)
def test_validate_test_jf_args_allows_connection_and_logging_flags(argv):
    validate_test_jf_args(argv)
    assert state.stats.errors == 0


def test_parse_args_requires_single_value(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jfin.py", "--single"])
    with pytest.raises(SystemExit):
        parse_args()


def test_single_requires_explicit_mode(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
        jf_url = "https://demo.example.com"
        jf_api_key = "token"
        operations = ["logo"]

        [logging]
        file_enabled = false
        silent = true
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["jfin.py", "--config", str(cfg_path), "--single", "item123"],
    )
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1

def test_warn_unused_cli_overrides_flags_when_not_used(caplog):
    args = argparse.Namespace(
        logo_target_size=None,
        thumb_target_size=None,
        backdrop_target_size=None,
        profile_target_size=None,
        thumb_jpeg_quality=90,
        backdrop_jpeg_quality=None,
        profile_webp_quality=None,
        no_padding=True,
        no_upscale=False,
        no_downscale=False,
        item_types=None,
    )
    warn_unused_cli_overrides(args, ["profile"])
    assert state.stats.warnings == 2


@pytest.mark.parametrize(
    "mode, kwargs, expected_substr",
    [
        ("logo", {"thumb_jpeg_quality": 90}, "--thumb-jpeg-quality has no effect"),
        (
            "logo",
            {"backdrop_target_size": (100, 100)},
            "--backdrop-target-size has no effect",
        ),
        ("thumb", {"profile_webp_quality": 80}, "--profile-webp-quality has no effect"),
    ],
)
def test_warn_unused_cli_overrides_incompatible_flags(mode, kwargs, expected_substr, caplog):
    base_args = dict(
        logo_target_size=None,
        thumb_target_size=None,
        backdrop_target_size=None,
        profile_target_size=None,
        thumb_jpeg_quality=None,
        backdrop_jpeg_quality=None,
        profile_webp_quality=None,
        no_padding=False,
        no_upscale=False,
        no_downscale=False,
        item_types=None,
    )
    base_args.update(kwargs)
    args = argparse.Namespace(**base_args)
    warn_unused_cli_overrides(args, [mode])
    assert state.stats.warnings == 1


def test_warns_when_no_upscale_and_no_downscale_both_set(caplog):
    args = argparse.Namespace(
        logo_target_size=None,
        thumb_target_size=None,
        backdrop_target_size=None,
        profile_target_size=None,
        thumb_jpeg_quality=None,
        backdrop_jpeg_quality=None,
        profile_webp_quality=None,
        no_padding=False,
        no_upscale=True,
        no_downscale=True,
        item_types=None,
    )
    warn_unused_cli_overrides(args, ["logo"])
    assert state.stats.warnings == 1


def test_backup_disallowed_with_restore(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
        jf_url = "https://demo.example.com"
        jf_api_key = "token"

        [logging]
        file_enabled = false
        silent = true
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["jfin.py", "--config", str(cfg_path), "--restore", "--backup"],
    )
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
