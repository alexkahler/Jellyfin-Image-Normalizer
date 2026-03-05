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
