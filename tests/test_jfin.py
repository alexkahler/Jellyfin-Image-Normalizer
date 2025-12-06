import argparse

import pytest

from jfin import validate_generate_config_args, validate_restore_all_args, warn_unused_cli_overrides
from jfin_core import state


def test_validate_restore_all_args_allows_config_and_logging():
    validate_restore_all_args(["--restore-all", "--config", "myconfig.toml", "-s"])
    assert state.stats.errors == 0


def test_validate_restore_all_args_blocks_other_flags():
    with pytest.raises(SystemExit):
        validate_restore_all_args(["--restore-all", "--mode", "logo"])
    assert state.stats.errors == 1


def test_validate_generate_config_args_blocks_other_flags():
    with pytest.raises(SystemExit):
        validate_generate_config_args(["--generate-config", "--mode", "logo"])
    assert state.stats.errors == 1


def test_warn_unused_cli_overrides_flags_when_not_used(caplog):
    args = argparse.Namespace(
        jpeg_quality=90,
        webp_quality=None,
        no_padding=True,
    )
    warn_unused_cli_overrides(args, ["profile"])
    assert state.stats.warnings == 2
    assert any("--jpeg-quality has no effect" in rec.message for rec in caplog.records)
