"""Pipeline backdrop split safety characterization tests for Slice-34."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

import pytest

from jfin import state
from tests.characterization.safety_contract._harness import (
    assert_observation_subset,
    build_backdrop_observed_trace_events,
    extract_delete_index,
    load_baseline_cases,
    project_backdrop_trace_events,
)

try:
    import tomllib  # noqa: F401

    HAS_TOMLLIB = True
except ModuleNotFoundError:  # pragma: no cover - local py3.10 fallback
    HAS_TOMLLIB = False

if HAS_TOMLLIB:
    from jfin.client import JellyfinClient
    from jfin.config import ModeRuntimeSettings
    from jfin.discovery import DiscoveredItem
    from jfin.imaging import ScalePlan
    from jfin.pipeline import normalize_item_backdrops_api
    import jfin.pipeline as pipeline_mod
else:  # pragma: no cover - runtime guard for local py3.10 collection
    JellyfinClient = object  # type: ignore[assignment]
    ModeRuntimeSettings = object  # type: ignore[assignment]
    DiscoveredItem = object  # type: ignore[assignment]
    ScalePlan = object  # type: ignore[assignment]
    normalize_item_backdrops_api = None  # type: ignore[assignment]
    pipeline_mod = None  # type: ignore[assignment]


BASELINE_PATH = (
    Path(__file__).resolve().parents[1] / "baselines" / "safety_contract_baseline.json"
)
SAFETY_CASES = load_baseline_cases(BASELINE_PATH)


@pytest.mark.skipif(
    not HAS_TOMLLIB,
    reason="Pipeline safety characterization requires Python 3.11+ (tomllib).",
)
def test_pipe_backdrop_002_characterization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """PIPE-BACKDROP-002 should preserve one-index partial-failure retention semantics."""
    case = SAFETY_CASES["PIPE-BACKDROP-002"]
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
    jf_client.set_item_image_bytes.return_value = False

    item = DiscoveredItem(
        id="item-backdrop-split",
        name="BackdropSplit",
        type="Movie",
        parent_id=None,
        library_id=None,
        library_name=None,
        backdrop_count=1,
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
        i for i, call in enumerate(all_calls) if call[0] == "delete_image"
    )
    first_upload_idx = next(
        i for i, call in enumerate(all_calls) if call[0] == "set_item_image_bytes"
    )
    backdrop_count = item.backdrop_count or 0
    fetch_calls = jf_client.get_item_image.call_args_list[:backdrop_count]
    fetch_indices = [call.kwargs.get("index") for call in fetch_calls]
    delete_indices = [
        extract_delete_index(call) for call in jf_client.delete_image.call_args_list
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
    verify_index = (
        cast(int | None, verify_call.kwargs.get("index")) if verify_call else None
    )
    verify_status_code = 404 if post_delete_404_verified else 200
    trace_events = build_backdrop_observed_trace_events(
        fetch_indices=cast(list[int], fetch_indices),
        normalized_backdrop_indices=normalized_backdrop_indices,
        delete_indices=cast(list[int], delete_indices),
        verify_index=verify_index,
        verify_status_code=verify_status_code,
        upload_indices=cast(list[int], upload_indices),
        staging_retained=staging_dir.exists(),
    )
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
        "trace": {"events": trace_events},
    }
    expected_trace_events = cast(
        list[dict[str, Any]],
        case["expected_observations"]["trace"]["events"],
    )
    assert project_backdrop_trace_events(trace_events) == project_backdrop_trace_events(
        expected_trace_events
    )
    assert_observation_subset(case["expected_observations"], observed)
