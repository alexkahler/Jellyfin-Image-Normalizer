import argparse

import pytest

from jfin_core.config import (
    build_discovery_settings,
    build_mode_runtime_settings,
    ConfigError,
    generate_default_config,
    load_config_from_path,
    parse_operations,
    validate_config_types,
)


def test_load_config_from_path_parses_toml_and_builds_mode(tmp_path):
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
        no_padding = true
        """,
        encoding="utf-8",
    )

    cfg = load_config_from_path(config_path)
    validate_config_types(cfg)
    ops = parse_operations(None, cfg["operations"])
    assert ops == ["logo"]

    args = argparse.Namespace(
        width=None,
        height=None,
        no_upscale=False,
        no_downscale=False,
        no_padding=False,
        jpeg_quality=None,
        webp_quality=None,
    )
    settings = build_mode_runtime_settings("logo", cfg["logo"], args)
    assert settings.target_width == 640
    assert settings.target_height == 360
    assert settings.allow_upscale is False
    assert settings.no_padding is True


def test_load_config_from_path_rejects_non_toml(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ConfigError, match="expected a \\.toml file"):
        load_config_from_path(cfg_path)


def test_load_config_from_path_missing_file(tmp_path):
    missing_path = tmp_path / "missing.toml"
    with pytest.raises(ConfigError, match="Config file not found"):
        load_config_from_path(missing_path)


def test_validate_config_types_rejects_invalid_types(tmp_path):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
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
    cfg = load_config_from_path(cfg_path)
    with pytest.raises(ConfigError) as excinfo:
        validate_config_types(cfg)
    assert "operations" in str(excinfo.value)
    assert "backup" in str(excinfo.value)


def test_validate_config_types_requires_core_fields():
    cfg: dict[str, object] = {}
    with pytest.raises(ConfigError) as excinfo:
        validate_config_types(cfg)
    message = str(excinfo.value)
    assert "jf_url" in message
    assert "jf_api_key" in message


def test_validate_config_types_requires_positive_dimensions():
    cfg = {
        "jf_url": "https://demo.example.com",
        "jf_api_key": "token",
        "logo": {
            "width": 0,
            "height": 200,
            "no_upscale": False,
            "no_downscale": False,
            "no_padding": False,
        },
    }
    with pytest.raises(ConfigError) as excinfo:
        validate_config_types(cfg)
    assert "width" in str(excinfo.value)


def test_generate_default_config_requires_toml(tmp_path):
    path = tmp_path / "config.json"
    with pytest.raises(SystemExit):
        generate_default_config(path)
    assert not path.exists()


def test_load_config_from_sections_lifts_keys(tmp_path):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
        [SERVER]
        jf_url = "https://demo.example.com"
        jf_api_key = "token"

        [API]
        timeout = 10
        dry_run = true

        [BACKUP]
        backup = true

        [MODES]
        operations = "logo|thumb"

        [logo]
        width = 800
        height = 400
        no_upscale = false
        no_downscale = false
        no_padding = false
        """,
        encoding="utf-8",
    )

    cfg = load_config_from_path(cfg_path)
    validate_config_types(cfg)
    ops = parse_operations(None, cfg["operations"])
    assert cfg["jf_url"] == "https://demo.example.com"
    assert cfg["timeout"] == 10
    assert ops == ["logo", "thumb"]


def test_parse_operations_dedupes_and_orders():
    ops = parse_operations("logo|thumb|logo", None)
    assert ops == ["logo", "thumb"]


def test_parse_operations_invalid_raises():
    with pytest.raises(SystemExit):
        parse_operations("poster", None)


def test_build_discovery_settings_maps_modes_and_filters():
    cfg = {
        "operator": {"username": "alex"},
        "libraries": {"names": ["Movies", "TV"]},
    }
    settings = build_discovery_settings(cfg, ["logo", "profile"])
    assert settings.include_item_types == ["Movie", "Series", "Season", "Episode"]
    assert settings.enable_image_types == ["Logo", "Primary"]
    assert settings.library_names == ["Movies", "TV"]


def test_build_mode_runtime_settings_respects_cli_overrides():
    args = argparse.Namespace(
        width=400,
        height=None,
        no_upscale=True,
        no_downscale=False,
        no_padding=True,
        jpeg_quality=None,
        webp_quality=None,
    )
    mode_cfg = {
        "width": 800,
        "height": 600,
        "no_upscale": False,
        "no_downscale": False,
        "no_padding": False,
        "jpeg_quality": 85,
        "webp_quality": 75,
    }
    settings = build_mode_runtime_settings("logo", mode_cfg, args)
    assert settings.target_width == 400
    assert settings.target_height == 300
    assert settings.allow_upscale is False
    assert settings.allow_downscale is True
    assert settings.no_padding is True


def test_build_mode_runtime_settings_infers_dimensions_without_zero():
    args = argparse.Namespace(
        width=1,
        height=None,
        no_upscale=False,
        no_downscale=False,
        no_padding=False,
        jpeg_quality=None,
        webp_quality=None,
    )
    mode_cfg = {
        "width": 3,
        "height": 2,
        "no_upscale": False,
        "no_downscale": False,
        "no_padding": False,
        "jpeg_quality": 85,
        "webp_quality": 75,
    }
    settings = build_mode_runtime_settings("logo", mode_cfg, args)
    assert settings.target_width == 1
    assert settings.target_height == 1


def test_build_mode_runtime_settings_rejects_non_positive_override():
    args = argparse.Namespace(
        width=0,
        height=None,
        no_upscale=False,
        no_downscale=False,
        no_padding=False,
        jpeg_quality=None,
        webp_quality=None,
    )
    mode_cfg = {
        "width": 100,
        "height": 50,
        "no_upscale": False,
        "no_downscale": False,
        "no_padding": False,
        "jpeg_quality": 85,
        "webp_quality": 75,
    }
    with pytest.raises(ConfigError):
        build_mode_runtime_settings("logo", mode_cfg, args)
