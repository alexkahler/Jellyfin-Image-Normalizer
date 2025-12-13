import argparse

import pytest

from jfin_core import state
from jfin_core.config import (
    apply_cli_overrides,
    build_discovery_settings,
    build_mode_runtime_settings,
    ConfigError,
    generate_default_config,
    load_config_from_path,
    parse_item_types,
    parse_operations,
    validate_config_types,
)


def test_validate_config_types_rejects_removed_logo_no_padding_key():
    cfg = {
        "jf_url": "https://demo.example.com",
        "jf_api_key": "token",
        "logo": {
            "width": 800,
            "height": 310,
            "no_upscale": False,
            "no_downscale": False,
            "no_padding": True,
        },
    }
    with pytest.raises(ConfigError, match="logo\\.no_padding has been removed"):
        validate_config_types(cfg)
    assert state.stats.warnings == 1


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
        padding = "none"
        """,
        encoding="utf-8",
    )

    cfg = load_config_from_path(config_path)
    validate_config_types(cfg)
    ops = parse_operations(None, cfg["operations"])
    assert ops == ["logo"]

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
    assert settings.target_width == 640
    assert settings.target_height == 360
    assert settings.allow_upscale is False
    assert settings.logo_padding == "none"


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


def test_validate_config_types_requires_positive_size():
    cfg = {
        "jf_url": "https://demo.example.com",
        "jf_api_key": "token",
        "logo": {
            "width": 0,
            "height": 200,
            "no_upscale": False,
            "no_downscale": False,
            "padding": "add",
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
        [server]
        jf_url = "https://demo.example.com"
        jf_api_key = "token"

        [api]
        timeout = 10
        dry_run = true

        [backup]
        backup = true

        [modes]
        operations = "logo|thumb"

        [logo]
        width = 800
        height = 400
        no_upscale = false
        no_downscale = false
        padding = "add"
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


def test_parse_operations_empty_raises():
    with pytest.raises(SystemExit):
        parse_operations("", None)
    with pytest.raises(SystemExit):
        parse_operations(None, "")


def test_build_discovery_settings_maps_modes_and_filters():
    cfg = {
        "libraries": {"names": ["Movies", "TV"]},
        "item_types": "series",
    }
    settings = build_discovery_settings(cfg, ["logo", "profile"])
    assert settings.include_item_types == ["Series"]
    assert settings.enable_image_types == ["Logo", "Primary"]
    assert settings.library_names == ["Movies", "TV"]


def test_build_mode_runtime_settings_respects_cli_overrides():
    args = argparse.Namespace(
        logo_target_size=(400, 300),
        thumb_target_size=None,
        backdrop_target_size=None,
        profile_target_size=None,
        no_upscale=True,
        no_downscale=False,
        logo_padding="none",
        thumb_jpeg_quality=None,
        backdrop_jpeg_quality=None,
        profile_webp_quality=None,
        item_types=None,
    )
    mode_cfg = {
        "width": 800,
        "height": 600,
        "no_upscale": False,
        "no_downscale": False,
        "padding": "add",
        "jpeg_quality": 85,
        "webp_quality": 75,
    }
    settings = build_mode_runtime_settings("logo", mode_cfg, args)        
    assert settings.target_width == 400
    assert settings.target_height == 300
    assert settings.allow_upscale is False
    assert settings.allow_downscale is True
    assert settings.logo_padding == "none"


def test_build_mode_runtime_settings_infers_size_without_zero():
    args = argparse.Namespace(
        logo_target_size=(1, 1),
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
    mode_cfg = {
        "width": 3,
        "height": 2,
        "no_upscale": False,
        "no_downscale": False,
        "padding": "add",
        "jpeg_quality": 85,
        "webp_quality": 75,
    }
    settings = build_mode_runtime_settings("logo", mode_cfg, args)
    assert settings.target_width == 1
    assert settings.target_height == 1


def test_build_mode_runtime_settings_rejects_non_positive_override():
    args = argparse.Namespace(
        logo_target_size=(0, 50),
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
    mode_cfg = {
        "width": 100,
        "height": 50,
        "no_upscale": False,
        "no_downscale": False,
        "padding": "add",
        "jpeg_quality": 85,
        "webp_quality": 75,
    }
    with pytest.raises(ConfigError):
        build_mode_runtime_settings("logo", mode_cfg, args)


def test_parse_item_types_supports_strings_and_arrays():
    assert parse_item_types("movies|series") == ["Movie", "Series"]
    assert parse_item_types(["Series"]) == ["Series"]
    assert parse_item_types(None) == ["Movie", "Series"]


def test_parse_item_types_rejects_invalid_values():
    with pytest.raises(ConfigError):
        parse_item_types("movies|books")
    with pytest.raises(ConfigError):
        parse_item_types(123)


@pytest.mark.parametrize(
    "mode, attr, size",
    [
        ("logo", "logo_target_size", (321, 123)),
        ("thumb", "thumb_target_size", (1000, 562)),
        ("backdrop", "backdrop_target_size", (1920, 1080)),
        ("profile", "profile_target_size", (256, 256)),
    ],
)
def test_apply_cli_overrides_applies_target_size_per_mode(mode, attr, size):
    cfg = {"jf_url": "u", "jf_api_key": "k"}
    args = argparse.Namespace(
        jf_url=None,
        jf_api_key=None,
        libraries=None,
        item_types=None,
        dry_run=False,
        backup=False,
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
        jf_delay_ms=None,
        force_upload_noscale=False,
    )
    setattr(args, attr, size)
    merged = apply_cli_overrides(args, cfg)
    assert merged[mode]["width"] == size[0]
    assert merged[mode]["height"] == size[1]


@pytest.mark.parametrize(
    "mode, attr, key, value",
    [
        ("thumb", "thumb_jpeg_quality", "jpeg_quality", 90),
        ("backdrop", "backdrop_jpeg_quality", "jpeg_quality", 75),
        ("profile", "profile_webp_quality", "webp_quality", 60),
    ],
)
def test_apply_cli_overrides_applies_quality_overrides(mode, attr, key, value):
    cfg = {"jf_url": "u", "jf_api_key": "k"}
    args = argparse.Namespace(
        jf_url=None,
        jf_api_key=None,
        libraries=None,
        item_types=None,
        dry_run=False,
        backup=False,
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
        jf_delay_ms=None,
        force_upload_noscale=False,
    )
    setattr(args, attr, value)
    merged = apply_cli_overrides(args, cfg)
    assert merged[mode][key] == value
