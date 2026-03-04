"""Shared helper builders for characterization governance tests."""

from __future__ import annotations

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
            "calls": {"seed_calls": 0},
        },
        "expected_messages": [],
        "notes": "seed",
    }


def build_valid_baseline_payload(
    required_ids: list[str],
    *,
    imaging: bool = False,
    safety: bool = False,
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
    return {
        "version": 1,
        "cases": {behavior_id: dict(case_payload) for behavior_id in required_ids},
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
