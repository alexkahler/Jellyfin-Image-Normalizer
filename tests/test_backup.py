from jfin_core.backup import normalize_backup_mode, should_backup_for_plan


def test_should_backup_for_plan_modes():
    assert should_backup_for_plan("SCALE_UP", "partial") is True
    assert should_backup_for_plan("SCALE_DOWN", "partial") is True
    assert should_backup_for_plan("NO_SCALE", "partial") is False
    assert should_backup_for_plan("NO_SCALE", "full") is True


def test_normalize_backup_mode_defaults_to_partial():
    assert normalize_backup_mode("full") == "full"
    assert normalize_backup_mode(None) == "partial"
    assert normalize_backup_mode("unsupported") == "partial"
