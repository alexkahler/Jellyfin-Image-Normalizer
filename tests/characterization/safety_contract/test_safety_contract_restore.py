"""Restore safety characterization tests for WI-005."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import Mock

import pytest

from jfin import state
from jfin.backup import restore_from_backups, restore_single_item_from_backup
from jfin.client import JellyfinClient
from tests.characterization.safety_contract._harness import (
    assert_expected_messages,
    assert_observation_subset,
    capture_safety_messages,
    load_baseline_cases,
    observed_messages,
    write_backup_files,
)


BASELINE_PATH = (
    Path(__file__).resolve().parents[1] / "baselines" / "safety_contract_baseline.json"
)
SAFETY_CASES = load_baseline_cases(BASELINE_PATH)


def test_rst_bulk_001_characterization(tmp_path: Path) -> None:
    """RST-BULK-001 should preserve contiguous backdrop restore semantics."""
    case = SAFETY_CASES["RST-BULK-001"]
    state.reset_state()
    backup_root = tmp_path / "bulk"
    write_backup_files(
        backup_root=backup_root,
        item_id="abc123",
        filenames=["backdrop.jpg", "backdrop1.jpg"],
        payload=b"data",
    )

    jf_client = Mock(spec=JellyfinClient)
    jf_client.set_item_image_bytes.return_value = True
    jf_client.set_user_profile_image.return_value = True

    restore_from_backups(
        backup_root=backup_root,
        jf_client=jf_client,
        operations=["backdrop"],
        dry_run=False,
    )
    observed = {
        "result": {"return_value": None, "raises": None},
        "calls": {
            "item_upload_calls": jf_client.set_item_image_bytes.call_count,
            "profile_upload_calls": jf_client.set_user_profile_image.call_count,
        },
        "stats": {
            "successes": state.stats.successes,
            "errors": state.stats.errors,
        },
    }
    assert_observation_subset(case["expected_observations"], observed)


def test_rst_single_001_characterization(tmp_path: Path) -> None:
    """RST-SINGLE-001 should preserve single-item contiguous backdrop semantics."""
    case = SAFETY_CASES["RST-SINGLE-001"]
    state.reset_state()
    backup_root = tmp_path / "single"
    target_id = "abc123"
    write_backup_files(
        backup_root=backup_root,
        item_id=target_id,
        filenames=["backdrop.jpg", "backdrop1.jpg"],
        payload=b"data",
    )

    jf_client = Mock(spec=JellyfinClient)
    jf_client.set_item_image_bytes.return_value = True
    jf_client.set_user_profile_image.return_value = True

    result = restore_single_item_from_backup(
        backup_root=backup_root,
        jf_client=jf_client,
        mode="backdrop",
        target_id=target_id,
        dry_run=False,
    )
    observed = {
        "result": {"return_value": result, "raises": None},
        "calls": {
            "item_upload_calls": jf_client.set_item_image_bytes.call_count,
            "profile_upload_calls": jf_client.set_user_profile_image.call_count,
        },
        "stats": {
            "successes": state.stats.successes,
            "errors": state.stats.errors,
        },
    }
    assert_observation_subset(case["expected_observations"], observed)


def test_rst_refuse_001_characterization(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """RST-REFUSE-001 should preserve missing-backup-root refusal semantics."""
    case = SAFETY_CASES["RST-REFUSE-001"]
    state.reset_state()
    missing_root = tmp_path / "missing"
    jf_client = Mock(spec=JellyfinClient)
    with capture_safety_messages() as captured_messages:
        with caplog.at_level(logging.DEBUG):
            with pytest.raises(SystemExit) as excinfo:
                restore_from_backups(
                    backup_root=missing_root,
                    jf_client=jf_client,
                    operations=["logo"],
                    dry_run=False,
                )

    observed = {
        "result": {
            "return_value": None,
            "raises": "SystemExit",
            "exit_code": excinfo.value.code,
        },
        "stats": {"errors": state.stats.errors},
    }
    assert_observation_subset(case["expected_observations"], observed)
    assert_expected_messages(
        case.get("expected_messages"),
        observed_messages(caplog, captured_messages),
    )


def test_rst_path_001_characterization(tmp_path: Path) -> None:
    """RST-PATH-001 should preserve profile-vs-item restore API path semantics."""
    case = SAFETY_CASES["RST-PATH-001"]
    state.reset_state()
    backup_root = tmp_path / "paths"
    write_backup_files(
        backup_root=backup_root,
        item_id="user123",
        filenames=["profile.png"],
        payload=b"profile",
    )
    write_backup_files(
        backup_root=backup_root,
        item_id="item123",
        filenames=["logo.png"],
        payload=b"item",
    )

    jf_client = Mock(spec=JellyfinClient)
    jf_client.set_item_image_bytes.return_value = True
    jf_client.set_user_profile_image.return_value = True

    profile_ok = restore_single_item_from_backup(
        backup_root=backup_root,
        jf_client=jf_client,
        mode="profile",
        target_id="user123",
        dry_run=False,
    )
    item_ok = restore_single_item_from_backup(
        backup_root=backup_root,
        jf_client=jf_client,
        mode="logo",
        target_id="item123",
        dry_run=False,
    )

    observed = {
        "result": {"return_value": profile_ok and item_ok, "raises": None},
        "calls": {
            "profile_upload_calls": jf_client.set_user_profile_image.call_count,
            "item_upload_calls": jf_client.set_item_image_bytes.call_count,
        },
        "stats": {
            "successes": state.stats.successes,
            "errors": state.stats.errors,
        },
    }
    assert_observation_subset(case["expected_observations"], observed)
