"""Shared helper builders for characterization governance tests."""

from __future__ import annotations

import copy
from typing import Any


def _default_case_payload() -> dict[str, object]:
    """Build a valid minimal CLI/config baseline case payload."""
    return {
        "expected_exit_code": 0,
        "expected_messages": [],
        "expected_preflight": "not_reached",
        "notes": "seed",
    }


def _default_imaging_case_payload() -> dict[str, object]:
    """Build a valid minimal imaging baseline case payload."""
    return {
        "expected_properties": {
            "decision": "SCALE_UP",
            "size": [10, 10],
            "mode": "RGB",
            "format": "JPEG",
            "content_type": "image/jpeg",
        },
        "golden_key": "golden-seed",
        "notes": "seed",
    }


def _default_safety_case_payload() -> dict[str, object]:
    """Build a valid minimal WI-005 safety baseline case payload."""
    return {
        "expected_observations": {
            "result": {"return_value": True, "raises": None},
            "calls": {
                "seed_calls": 0,
                "sequence.fetch_indices_dense_ordered": True,
                "sequence.normalize_source_index_mapping": True,
                "sequence.post_delete_404_verified": True,
                "sequence.upload_indices_dense_ordered": True,
                "sequence.delete_index_zero_repeated": True,
                "sequence.staging_retained_partial_failure": True,
            },
            "ordering": ["delete_before_upload"],
        },
        "expected_messages": [],
        "notes": "seed",
    }


def build_backdrop_trace_events() -> list[dict[str, object]]:
    """Build canonical PIPE-BACKDROP-001 trace events for COV-04 tests."""
    return [
        {
            "phase": "fetch",
            "index": 0,
            "action": "get_item_image",
            "result": "ok",
            "details": {"source_index": 0},
        },
        {
            "phase": "fetch",
            "index": 1,
            "action": "get_item_image",
            "result": "ok",
            "details": {"source_index": 1},
        },
        {
            "phase": "normalize",
            "index": 0,
            "action": "normalize_image",
            "result": "ok",
            "details": {"source_index": 0, "target_index": 0},
        },
        {
            "phase": "normalize",
            "index": 1,
            "action": "normalize_image",
            "result": "ok",
            "details": {"source_index": 1, "target_index": 1},
        },
        {
            "phase": "delete",
            "index": 0,
            "action": "delete_image",
            "result": "ok",
            "details": {"target_index": 0},
        },
        {
            "phase": "delete",
            "index": 0,
            "action": "delete_image",
            "result": "ok",
            "details": {"target_index": 0},
        },
        {
            "phase": "verify",
            "index": 0,
            "action": "get_item_image_head",
            "result": "not_found",
            "details": {"target_index": 0, "status_code": 404},
        },
        {
            "phase": "upload",
            "index": 0,
            "action": "set_item_image_bytes",
            "result": "ok",
            "details": {"source_index": 0, "target_index": 0},
        },
        {
            "phase": "upload",
            "index": 1,
            "action": "set_item_image_bytes",
            "result": "failed",
            "details": {"source_index": 1, "target_index": 1},
        },
        {
            "phase": "finalize",
            "index": None,
            "action": "staging_retention",
            "result": "retained",
            "details": {
                "retained": True,
                "failure_kind": "partial_upload_failure",
            },
        },
    ]


def build_valid_baseline_payload(
    required_ids: list[str],
    *,
    imaging: bool = False,
    safety: bool = False,
    include_backdrop_trace: bool = False,
) -> dict[str, Any]:
    """Build a valid baseline JSON payload for required behavior IDs."""
    if imaging and safety:
        raise ValueError("imaging and safety payload flags are mutually exclusive.")
    if imaging:
        case_payload = _default_imaging_case_payload()
    elif safety:
        case_payload = _default_safety_case_payload()
    else:
        case_payload = _default_case_payload()
    cases = {behavior_id: copy.deepcopy(case_payload) for behavior_id in required_ids}
    if safety and include_backdrop_trace and "PIPE-BACKDROP-001" in cases:
        expected_observations = cases["PIPE-BACKDROP-001"]["expected_observations"]
        if isinstance(expected_observations, dict):
            expected_observations["trace"] = {"events": build_backdrop_trace_events()}
    return {
        "version": 1,
        "cases": cases,
    }


def build_valid_imaging_manifest(imaging_ids: list[str]) -> dict[str, Any]:
    """Build a valid imaging manifest payload for required IMG behavior IDs."""
    cases: dict[str, dict[str, object]] = {}
    for behavior_id in imaging_ids:
        key = f"golden-{behavior_id.lower()}"
        cases[key] = {
            "expected_path": (
                f"tests/golden/imaging/expected/{behavior_id.lower()}_expected.png"
            ),
            "compare_mode": "exact",
        }
    return {
        "version": 1,
        "metadata": {
            "python_version": "3.13.0",
            "pillow_version": "12.1.1",
            "generated_at": "2026-03-04T00:00:00Z",
        },
        "cases": cases,
    }
