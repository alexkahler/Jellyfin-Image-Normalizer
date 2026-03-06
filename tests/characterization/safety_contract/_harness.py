"""Shared helpers for WI-005 safety characterization tests."""

from __future__ import annotations

import io
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import pytest
from PIL import Image
from tests.characterization._harness import (
    capture_logger_messages,
    merge_observed_messages,
)


def load_baseline_cases(path: Path) -> dict[str, dict[str, Any]]:
    """Load and validate the safety baseline payload."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1:
        raise AssertionError(
            f"Unsupported safety baseline version in {path}: {payload}"
        )
    cases = payload.get("cases")
    if not isinstance(cases, dict):
        raise AssertionError(f"Safety baseline is missing object 'cases': {path}")
    return cases


def assert_expected_messages(
    expected_tokens: list[str] | None,
    observed_messages: list[str],
) -> None:
    """Assert all expected message tokens exist in observed logs/messages."""
    if not expected_tokens:
        return
    haystack = "\n".join(observed_messages)
    for token in expected_tokens:
        assert token in haystack, f"Missing expected message token: {token!r}"


@contextmanager
def capture_safety_messages() -> Iterator[list[str]]:
    """Capture safety-test logger messages with strict lifecycle isolation."""
    with capture_logger_messages("jfin") as captured:
        yield captured


def observed_messages(
    caplog: pytest.LogCaptureFixture,
    logger_messages: list[str],
) -> list[str]:
    """Merge caplog + direct logger captures with deterministic normalization."""
    return merge_observed_messages(
        [record.getMessage() for record in caplog.records],
        logger_messages,
    )


def assert_observation_subset(
    expected: dict[str, Any],
    observed: dict[str, Any],
    *,
    path: str = "expected_observations",
) -> None:
    """Recursively assert expected observation keys are present and equal."""
    for key, expected_value in expected.items():
        assert key in observed, f"Missing observation key: {path}.{key}"
        observed_value = observed[key]
        if isinstance(expected_value, dict):
            assert isinstance(observed_value, dict), (
                f"Observation key {path}.{key} must be an object."
            )
            assert_observation_subset(
                expected_value,
                observed_value,
                path=f"{path}.{key}",
            )
            continue
        if isinstance(expected_value, list):
            assert observed_value == expected_value, (
                f"Observation list mismatch for {path}.{key}: "
                f"expected {expected_value!r}, got {observed_value!r}"
            )
            continue
        assert observed_value == expected_value, (
            f"Observation mismatch for {path}.{key}: expected {expected_value!r}, "
            f"got {observed_value!r}"
        )


def build_backdrop_observed_trace_events(
    *,
    fetch_indices: list[int],
    normalized_backdrop_indices: list[int],
    delete_indices: list[int],
    verify_index: int | None,
    verify_status_code: int,
    upload_indices: list[int],
    staging_retained: bool,
) -> list[dict[str, Any]]:
    """Build deterministic observed trace events for backdrop characterization."""
    trace_events: list[dict[str, Any]] = []
    for source_index in fetch_indices:
        trace_events.append(
            {
                "phase": "fetch",
                "index": source_index,
                "action": "get_item_image",
                "result": "ok",
                "details": {"source_index": source_index},
            }
        )
    for source_index, target_index in enumerate(normalized_backdrop_indices):
        trace_events.append(
            {
                "phase": "normalize",
                "index": target_index,
                "action": "normalize_image",
                "result": "ok",
                "details": {
                    "source_index": source_index,
                    "target_index": target_index,
                },
            }
        )
    for target_index in delete_indices:
        trace_events.append(
            {
                "phase": "delete",
                "index": target_index,
                "action": "delete_image",
                "result": "ok",
                "details": {"target_index": target_index},
            }
        )
    if verify_index is not None:
        trace_events.append(
            {
                "phase": "verify",
                "index": verify_index,
                "action": "get_item_image_head",
                "result": "not_found" if verify_status_code == 404 else "ok",
                "details": {
                    "target_index": verify_index,
                    "status_code": verify_status_code,
                },
            }
        )
    for target_index in upload_indices:
        trace_events.append(
            {
                "phase": "upload",
                "index": target_index,
                "action": "set_item_image_bytes",
                "result": "ok" if target_index != 1 else "failed",
                "details": {
                    "source_index": target_index,
                    "target_index": target_index,
                },
            }
        )
    trace_events.append(
        {
            "phase": "finalize",
            "index": None,
            "action": "staging_retention",
            "result": "retained" if staging_retained else "discarded",
            "details": {
                "retained": staging_retained,
                "failure_kind": "partial_upload_failure"
                if staging_retained
                else "none",
            },
        }
    )
    return trace_events


def project_backdrop_trace_events(trace_events: list[dict[str, Any]]) -> dict[str, Any]:
    """Project backdrop trace events into invariant-relevant fields."""
    fetch_source_indices: list[int] = []
    normalize_pairs: list[tuple[int, int]] = []
    delete_target_indices: list[int] = []
    verify_status_pairs: list[tuple[int, int]] = []
    upload_target_indices: list[int] = []
    first_delete_position: int | None = None
    first_upload_position: int | None = None
    staging_retained_partial_failure = False

    for event_position, event in enumerate(trace_events):
        phase = event["phase"]
        details = event["details"]
        if phase == "fetch":
            fetch_source_indices.append(int(details["source_index"]))
        elif phase == "normalize":
            normalize_pairs.append(
                (int(details["source_index"]), int(details["target_index"]))
            )
        elif phase == "delete":
            if first_delete_position is None:
                first_delete_position = event_position
            delete_target_indices.append(int(details["target_index"]))
        elif phase == "verify":
            verify_status_pairs.append(
                (int(details["target_index"]), int(details["status_code"]))
            )
        elif phase == "upload":
            if first_upload_position is None:
                first_upload_position = event_position
            upload_target_indices.append(int(details["target_index"]))
        elif phase == "finalize":
            staging_retained_partial_failure = (
                bool(details["retained"])
                and details["failure_kind"] == "partial_upload_failure"
            )

    expected_dense_indices = list(range(len(fetch_source_indices)))
    return {
        "fetch_source_indices": fetch_source_indices,
        "normalize_pairs": normalize_pairs,
        "delete_target_indices": delete_target_indices,
        "verify_status_pairs": verify_status_pairs,
        "upload_target_indices": upload_target_indices,
        "fetch_dense_ordered": fetch_source_indices == expected_dense_indices,
        "normalize_source_index_mapping": normalize_pairs
        == [(index, index) for index in expected_dense_indices],
        "post_delete_404_verified": bool(verify_status_pairs)
        and all(pair == (0, 404) for pair in verify_status_pairs),
        "upload_dense_ordered": upload_target_indices == expected_dense_indices,
        "delete_index_zero_repeated": delete_target_indices
        == ([0] * len(fetch_source_indices)),
        "delete_before_upload": first_delete_position is not None
        and first_upload_position is not None
        and first_delete_position < first_upload_position,
        "staging_retained_partial_failure": staging_retained_partial_failure,
    }


def extract_delete_index(call: Any) -> int | None:
    """Extract backdrop delete index from call args/kwargs."""
    if "index" in call.kwargs:
        return int(call.kwargs["index"])
    if "image_index" in call.kwargs:
        return int(call.kwargs["image_index"])
    if len(call.args) >= 3:
        return int(call.args[2])
    return None


class FakeResponse:
    """Minimal requests response test double."""

    def __init__(self, status_code: int, *, text: str = "") -> None:
        self.status_code = status_code
        self.text = text
        self.content = b""

    @property
    def ok(self) -> bool:
        return self.status_code < 400


def png_bytes(*, size: tuple[int, int], color: tuple[int, int, int]) -> bytes:
    """Build deterministic PNG bytes for pipeline/api scenarios."""
    img = Image.new("RGB", size, color)
    buff = io.BytesIO()
    img.save(buff, format="PNG")
    return buff.getvalue()


def write_backup_files(
    *,
    backup_root: Path,
    item_id: str,
    filenames: list[str],
    payload: bytes,
) -> None:
    """Create backup files under the expected <prefix>/<item_id>/ layout."""
    item_dir = backup_root / item_id[:2] / item_id
    item_dir.mkdir(parents=True, exist_ok=True)
    for name in filenames:
        (item_dir / name).write_bytes(payload)
