"""API safety characterization tests for WI-005."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
import requests

from jfin.client import JellyfinClient
from tests.characterization.safety_contract._harness import (
    FakeResponse,
    assert_expected_messages,
    assert_observation_subset,
    load_baseline_cases,
)


BASELINE_PATH = (
    Path(__file__).resolve().parents[1] / "baselines" / "safety_contract_baseline.json"
)
SAFETY_CASES = load_baseline_cases(BASELINE_PATH)


def test_api_dryrun_001_characterization(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """API-DRYRUN-001 should block item-image POST writes in dry-run mode."""
    case = SAFETY_CASES["API-DRYRUN-001"]
    post_calls = {"count": 0}

    def fake_post(*_args, **_kwargs):
        post_calls["count"] += 1
        return FakeResponse(200)

    monkeypatch.setattr(requests, "post", fake_post)

    client = JellyfinClient(base_url="http://example", api_key="token", dry_run=True)
    with caplog.at_level(logging.DEBUG):
        result = client.set_item_image_bytes(
            item_id="item1",
            image_type="Logo",
            data=b"abc",
            content_type="image/png",
            backdrop_index=None,
        )

    observed = {
        "result": {"return_value": result, "raises": None},
        "calls": {"requests_post": post_calls["count"]},
    }
    assert_observation_subset(case["expected_observations"], observed)
    assert_expected_messages(
        case.get("expected_messages"),
        [record.getMessage() for record in caplog.records],
    )


def test_api_dryrun_002_characterization(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """API-DRYRUN-002 should block profile DELETE+POST writes in dry-run mode."""
    case = SAFETY_CASES["API-DRYRUN-002"]
    delete_calls = {"count": 0}
    post_calls = {"count": 0}

    def fake_delete(*_args, **_kwargs):
        delete_calls["count"] += 1
        return FakeResponse(204)

    def fake_post(*_args, **_kwargs):
        post_calls["count"] += 1
        return FakeResponse(200)

    monkeypatch.setattr(requests, "delete", fake_delete)
    monkeypatch.setattr(requests, "post", fake_post)

    client = JellyfinClient(base_url="http://example", api_key="token", dry_run=True)
    with caplog.at_level(logging.DEBUG):
        result = client.set_user_profile_image(
            user_id="user1",
            data=b"abc",
            content_type="image/png",
        )

    observed = {
        "result": {"return_value": result, "raises": None},
        "calls": {
            "requests_delete": delete_calls["count"],
            "requests_post": post_calls["count"],
        },
    }
    assert_observation_subset(case["expected_observations"], observed)
    assert_expected_messages(
        case.get("expected_messages"),
        [record.getMessage() for record in caplog.records],
    )


def test_api_delete_001_characterization(monkeypatch: pytest.MonkeyPatch) -> None:
    """API-DELETE-001 should preserve non-dry-run retry semantics."""
    case = SAFETY_CASES["API-DELETE-001"]
    delete_calls = {"count": 0}

    def fake_delete(*_args, **_kwargs):
        delete_calls["count"] += 1
        return FakeResponse(500, text="boom")

    monkeypatch.setattr(requests, "delete", fake_delete)

    client = JellyfinClient(
        base_url="http://example",
        api_key="token",
        dry_run=False,
        retry_count=3,
    )
    result = client.delete_image("item1", "Backdrop", 0)
    observed = {
        "result": {"return_value": result, "raises": None},
        "calls": {"requests_delete": delete_calls["count"]},
    }
    assert_observation_subset(case["expected_observations"], observed)
