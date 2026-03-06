"""Pipeline safety characterization tests for WI-005."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

import pytest
import requests

from jfin import state
from jfin.client import JellyfinClient
from tests.characterization.safety_contract._harness import (
    FakeResponse,
    assert_observation_subset,
    load_baseline_cases,
    png_bytes,
)

try:
    import tomllib  # noqa: F401

    HAS_TOMLLIB = True
except ModuleNotFoundError:  # pragma: no cover - local py3.10 fallback
    HAS_TOMLLIB = False

if HAS_TOMLLIB:
    from jfin.config import ModeRuntimeSettings
    from jfin.discovery import DiscoveredItem
    from jfin.imaging import ScalePlan
    from jfin.pipeline import normalize_item_backdrops_api, normalize_item_image_api
    import jfin.pipeline as pipeline_mod
else:  # pragma: no cover - runtime guard for local py3.10 collection
    ModeRuntimeSettings = object  # type: ignore[assignment]
    DiscoveredItem = object  # type: ignore[assignment]
    ScalePlan = object  # type: ignore[assignment]
    normalize_item_backdrops_api = None  # type: ignore[assignment]
    normalize_item_image_api = None  # type: ignore[assignment]
    pipeline_mod = None  # type: ignore[assignment]


BASELINE_PATH = (
    Path(__file__).resolve().parents[1] / "baselines" / "safety_contract_baseline.json"
)
SAFETY_CASES = load_baseline_cases(BASELINE_PATH)


@pytest.mark.skipif(
    not HAS_TOMLLIB,
    reason="Pipeline safety characterization requires Python 3.11+ (tomllib).",
)
def test_pipe_dryrun_001_characterization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """PIPE-DRYRUN-001 should preserve app and adapter dry-run write gates."""
    case = SAFETY_CASES["PIPE-DRYRUN-001"]

    state.reset_state()
    app_upload_calls = {"count": 0}

    class AppDryRunClient:
        def get_item_image(self, _item_id: str, _image_type: str):
            return png_bytes(size=(200, 100), color=(200, 10, 10)), "image/png"

        def set_item_image_bytes(self, **_kwargs):
            app_upload_calls["count"] += 1
            return True

    item = DiscoveredItem(
        id="item1",
        name="Demo",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        backdrop_count=None,
        image_types={"Thumb"},
    )
    settings = ModeRuntimeSettings(
        target_width=100,
        target_height=50,
        allow_upscale=False,
        allow_downscale=True,
        jpeg_quality=85,
        webp_quality=80,
    )
    app_result = normalize_item_image_api(
        item=item,
        image_type="Thumb",
        settings_by_mode={"thumb": settings},
        jf_client=cast(JellyfinClient, AppDryRunClient()),
        dry_run=True,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )
    app_successes = state.stats.successes

    state.reset_state()
    adapter_post_calls = {"count": 0}

    def fake_post(*_args, **_kwargs):
        adapter_post_calls["count"] += 1
        return FakeResponse(200)

    monkeypatch.setattr(requests, "post", fake_post)
    adapter_client = JellyfinClient(
        base_url="http://example",
        api_key="token",
        dry_run=True,
        retry_count=1,
    )
    monkeypatch.setattr(
        adapter_client,
        "get_item_image",
        lambda *_args, **_kwargs: (
            png_bytes(size=(200, 100), color=(10, 120, 220)),
            "image/png",
        ),
    )
    adapter_result = normalize_item_image_api(
        item=item,
        image_type="Thumb",
        settings_by_mode={"thumb": settings},
        jf_client=adapter_client,
        dry_run=False,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    observed = {
        "result": {"return_value": app_result and adapter_result, "raises": None},
        "calls": {
            "app_upload_calls": app_upload_calls["count"],
            "adapter_post_calls": adapter_post_calls["count"],
        },
        "stats": {
            "app_successes": app_successes,
            "adapter_successes": state.stats.successes,
        },
    }
    assert_observation_subset(case["expected_observations"], observed)


@pytest.mark.skipif(
    not HAS_TOMLLIB,
    reason="Pipeline safety characterization requires Python 3.11+ (tomllib).",
)
def test_pipe_backdrop_001_characterization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """PIPE-BACKDROP-001 should preserve ordering and staging retention semantics."""
    case = SAFETY_CASES["PIPE-BACKDROP-001"]
    state.reset_state()

    monkeypatch.setattr(
        pipeline_mod,
        "IMAGE_TYPE_TO_MODE",
        {"Backdrop": "backdrop"},
        raising=False,
    )

    jf_client = Mock(spec=JellyfinClient)
    jf_client.delete_image.return_value = True
    jf_client.get_item_image_head.return_value = None
    jf_client.get_item_image.side_effect = lambda *_args, **kwargs: (
        f"payload-{kwargs['index']}".encode("utf-8"),
        "image/jpeg",
    )
    normalized_backdrop_indices: list[int] = []

    def fake_normalize_image_bytes(**kwargs):
        plan = ScalePlan(
            decision="SCALE_DOWN",
            scale=1.0,
            new_width=100,
            new_height=50,
            orig_width=100,
            orig_height=50,
        )
        idx = kwargs.get("backdrop_index") or 0
        normalized_backdrop_indices.append(idx)
        return plan, f"normalized-{idx}".encode("utf-8"), "image/jpeg"

    monkeypatch.setattr(
        pipeline_mod,
        "_normalize_image_bytes",
        fake_normalize_image_bytes,
        raising=False,
    )

    jf_client.set_item_image_bytes.side_effect = lambda *_args, **kwargs: (
        kwargs.get("backdrop_index") != 1
    )

    item = DiscoveredItem(
        id="item-backdrop",
        name="Backdrop",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        backdrop_count=2,
        image_types={"Backdrop"},
    )
    result = normalize_item_backdrops_api(
        item=item,
        settings_by_mode={"backdrop": cast(ModeRuntimeSettings, object())},
        jf_client=jf_client,
        dry_run=False,
        force_upload_noscale=False,
        make_backup=False,
        backup_root=tmp_path,
        backup_mode="partial",
    )

    all_calls = jf_client.mock_calls
    first_delete_idx = next(
        i for i, c in enumerate(all_calls) if c[0] == "delete_image"
    )
    first_upload_idx = next(
        i for i, c in enumerate(all_calls) if c[0] == "set_item_image_bytes"
    )
    backdrop_count = item.backdrop_count or 0
    fetch_calls = jf_client.get_item_image.call_args_list[:backdrop_count]
    fetch_indices = [call.kwargs.get("index") for call in fetch_calls]

    def _delete_index(call: Any) -> int | None:
        if "index" in call.kwargs:
            return cast(int | None, call.kwargs["index"])
        if "image_index" in call.kwargs:
            return cast(int | None, call.kwargs["image_index"])
        if len(call.args) >= 3:
            return cast(int | None, call.args[2])
        return None

    delete_indices = [
        _delete_index(call) for call in jf_client.delete_image.call_args_list
    ]
    upload_indices = [
        call.kwargs.get("backdrop_index")
        for call in jf_client.set_item_image_bytes.call_args_list
    ]
    verify_call = jf_client.get_item_image_head.call_args
    post_delete_404_verified = bool(
        verify_call
        and verify_call.kwargs.get("index") == 0
        and jf_client.get_item_image_head.return_value is None
    )
    staging_dir = tmp_path / "staging" / item.id
    observed = {
        "result": {"return_value": result, "raises": None},
        "calls": {
            "delete_calls": jf_client.delete_image.call_count,
            "upload_calls": jf_client.set_item_image_bytes.call_count,
            "sequence.fetch_indices_dense_ordered": fetch_indices
            == list(range(backdrop_count)),
            "sequence.normalize_source_index_mapping": normalized_backdrop_indices
            == list(range(backdrop_count)),
            "sequence.post_delete_404_verified": post_delete_404_verified,
            "sequence.upload_indices_dense_ordered": upload_indices
            == list(range(backdrop_count)),
            "sequence.delete_index_zero_repeated": delete_indices
            == ([0] * backdrop_count),
            "sequence.staging_retained_partial_failure": staging_dir.exists(),
        },
        "stats": {
            "successes": state.stats.successes,
            "errors": state.stats.errors,
        },
        "filesystem": {"staging_retained": staging_dir.exists()},
        "ordering": (
            ["delete_before_upload"]
            if first_delete_idx < first_upload_idx
            else ["upload_before_delete"]
        ),
    }
    assert_observation_subset(case["expected_observations"], observed)
