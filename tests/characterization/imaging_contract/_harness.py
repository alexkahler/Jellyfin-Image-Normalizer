"""Shared helpers for WI-003 imaging characterization tests."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops


def load_baseline_cases(path: Path) -> dict[str, dict[str, Any]]:
    """Load and validate the imaging baseline payload."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1:
        raise AssertionError(f"Unsupported baseline version in {path}: {payload}")
    cases = payload.get("cases")
    if not isinstance(cases, dict):
        raise AssertionError(f"Baseline is missing object 'cases': {path}")
    return cases


def load_golden_manifest(path: Path) -> dict[str, Any]:
    """Load and validate the imaging golden manifest payload."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1:
        raise AssertionError(
            f"Unsupported golden manifest version in {path}: {payload}"
        )
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise AssertionError(f"Golden manifest missing metadata object: {path}")
    for key in ("python_version", "pillow_version", "generated_at"):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise AssertionError(
                f"Golden manifest metadata.{key} must be a non-empty string."
            )
    cases = payload.get("cases")
    if not isinstance(cases, dict):
        raise AssertionError(f"Golden manifest missing cases object: {path}")
    return payload


def decode_image(payload: bytes) -> Image.Image:
    """Decode image bytes into a loaded Pillow image."""
    img = Image.open(io.BytesIO(payload))
    img.load()
    return img


def assert_case_properties(
    case_payload: dict[str, Any],
    *,
    decision: str,
    normalized_img: Image.Image,
    content_type: str,
    fmt: str,
) -> None:
    """Assert one imaging case's expected transform properties."""
    expected = case_payload["expected_properties"]
    assert decision == expected["decision"]
    assert list(normalized_img.size) == expected["size"]
    assert normalized_img.mode == expected["mode"]
    assert fmt == expected["format"]
    assert content_type == expected["content_type"]


def _to_common_mode(
    lhs: Image.Image, rhs: Image.Image
) -> tuple[Image.Image, Image.Image]:
    """Convert two images to a common mode for tolerant pixel comparison."""
    target_mode = "RGBA" if ("A" in lhs.getbands() or "A" in rhs.getbands()) else "RGB"
    return lhs.convert(target_mode), rhs.convert(target_mode)


def _mae_and_diff_pixels(lhs: Image.Image, rhs: Image.Image) -> tuple[float, int]:
    """Compute mean absolute error and differing pixel count between two images."""
    if lhs.size != rhs.size:
        raise AssertionError(
            f"Size mismatch for tolerant compare: {lhs.size} vs {rhs.size}."
        )

    lhs_common, rhs_common = _to_common_mode(lhs, rhs)
    diff = ImageChops.difference(lhs_common, rhs_common)
    bands = len(diff.getbands())
    total_values = lhs_common.width * lhs_common.height * bands
    histogram = diff.histogram()
    weighted_sum = 0
    for idx, count in enumerate(histogram):
        weighted_sum += (idx % 256) * count
    mae = weighted_sum / float(total_values)

    lum_diff = diff.convert("L")
    mask = lum_diff.point([0] + [255] * 255)
    diff_pixels = sum(mask.getdata()) // 255
    return mae, int(diff_pixels)


def assert_golden_match(
    *,
    case_payload: dict[str, Any],
    observed_payload: bytes,
    manifest: dict[str, Any],
    repo_root: Path,
) -> None:
    """Assert observed output matches the golden manifest contract."""
    golden_key = case_payload["golden_key"]
    manifest_case = manifest["cases"].get(golden_key)
    assert isinstance(manifest_case, dict), (
        f"Missing manifest case for golden_key={golden_key!r}."
    )

    expected_relpath = manifest_case["expected_path"]
    expected_path = repo_root / expected_relpath
    assert expected_path.exists(), f"Golden expected file not found: {expected_relpath}"

    expected_img = decode_image(expected_path.read_bytes())
    observed_img = decode_image(observed_payload)

    compare_mode = manifest_case["compare_mode"]
    meta = manifest["metadata"]
    debug_meta = (
        f"manifest metadata: python={meta['python_version']}, "
        f"pillow={meta['pillow_version']}, generated_at={meta['generated_at']}"
    )

    if compare_mode == "exact":
        assert observed_img.mode == expected_img.mode, (
            f"Exact mode mismatch for {golden_key}: {observed_img.mode} != {expected_img.mode}; "
            f"{debug_meta}"
        )
        assert observed_img.size == expected_img.size, (
            f"Exact size mismatch for {golden_key}: {observed_img.size} != {expected_img.size}; "
            f"{debug_meta}"
        )
        assert observed_img.tobytes() == expected_img.tobytes(), (
            f"Exact pixel mismatch for {golden_key}; {debug_meta}"
        )
        return

    assert compare_mode == "tolerant", (
        f"Unsupported compare_mode {compare_mode!r} for {golden_key}; {debug_meta}"
    )
    max_mae = float(manifest_case["max_mean_abs_error"])
    max_diff_pixels = manifest_case.get("max_diff_pixels")
    mae, diff_pixels = _mae_and_diff_pixels(observed_img, expected_img)
    assert mae <= max_mae, (
        f"Tolerant MAE exceeded for {golden_key}: {mae:.4f} > {max_mae:.4f}; {debug_meta}"
    )
    if max_diff_pixels is not None:
        assert diff_pixels <= int(max_diff_pixels), (
            f"Tolerant diff-pixels exceeded for {golden_key}: "
            f"{diff_pixels} > {int(max_diff_pixels)}; {debug_meta}"
        )
