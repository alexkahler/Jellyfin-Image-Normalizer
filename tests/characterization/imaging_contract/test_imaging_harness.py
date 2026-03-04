"""Unit tests for WI-003 imaging characterization harness helpers."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from tests.characterization.imaging_contract._harness import (
    assert_golden_match,
    load_baseline_cases,
    load_golden_manifest,
)


def test_load_baseline_cases_reads_cases(tmp_path: Path) -> None:
    """Harness should load versioned imaging baseline cases."""
    path = tmp_path / "baseline.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "cases": {
                    "IMG-FAKE-001": {
                        "expected_properties": {
                            "decision": "X",
                            "size": [1, 1],
                            "mode": "RGB",
                            "format": "PNG",
                            "content_type": "image/png",
                        },
                        "golden_key": "case-1",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    cases = load_baseline_cases(path)
    assert "IMG-FAKE-001" in cases


def test_load_golden_manifest_reads_metadata(tmp_path: Path) -> None:
    """Harness should load and validate required golden manifest metadata."""
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "metadata": {
                    "python_version": "3.13.0",
                    "pillow_version": "12.1.1",
                    "generated_at": "2026-03-04T00:00:00Z",
                },
                "cases": {
                    "case-1": {"expected_path": "x.png", "compare_mode": "exact"}
                },
            }
        ),
        encoding="utf-8",
    )
    manifest = load_golden_manifest(path)
    assert manifest["metadata"]["python_version"] == "3.13.0"


def test_assert_golden_match_exact_passes(tmp_path: Path) -> None:
    """Exact compare should pass when observed and expected pixels match."""
    expected_path = tmp_path / "expected.png"
    Image.new("RGB", (2, 2), (10, 20, 30)).save(expected_path, format="PNG")
    observed_payload = expected_path.read_bytes()
    case_payload = {"golden_key": "case-1"}
    manifest = {
        "metadata": {
            "python_version": "3.13.0",
            "pillow_version": "12.1.1",
            "generated_at": "2026-03-04T00:00:00Z",
        },
        "cases": {
            "case-1": {
                "expected_path": str(expected_path.relative_to(tmp_path)).replace(
                    "\\", "/"
                ),
                "compare_mode": "exact",
            }
        },
    }
    assert_golden_match(
        case_payload=case_payload,
        observed_payload=observed_payload,
        manifest=manifest,
        repo_root=tmp_path,
    )
