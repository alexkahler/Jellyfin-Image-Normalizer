"""Characterization tests for imaging behavior contract rows in parity matrix."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from jfin.imaging import (
    build_normalized_image,
    cover_and_crop_image,
    encode_image_to_bytes,
    handle_no_scale,
    make_scale_plan,
    remove_padding_from_logo,
)
from jfin.state import RunStats
from tests.characterization.imaging_contract._harness import (
    assert_case_properties,
    assert_golden_match,
    load_baseline_cases,
    load_golden_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_PATH = (
    REPO_ROOT
    / "tests"
    / "characterization"
    / "baselines"
    / "imaging_contract_baseline.json"
)
MANIFEST_PATH = REPO_ROOT / "tests" / "golden" / "imaging" / "manifest.json"
REALISH_LOGO_FIXTURE = (
    REPO_ROOT
    / "tests"
    / "golden"
    / "imaging"
    / "fixtures"
    / "realish"
    / "logo_halo_soft.png"
)

IMAGING_CASES = load_baseline_cases(BASELINE_PATH)
GOLDEN_MANIFEST = load_golden_manifest(MANIFEST_PATH)


def test_img_scale_001_characterization() -> None:
    """IMG-SCALE-001 should preserve upscale decision and thumb output shape."""
    case = IMAGING_CASES["IMG-SCALE-001"]
    img = Image.new("RGB", (100, 50), (220, 30, 30))
    plan = make_scale_plan(
        img,
        target_w=200,
        target_h=100,
        fit_mode="fit",
        allow_upscale=True,
        allow_downscale=True,
    )
    normalized_img, content_type, fmt = build_normalized_image(
        img,
        mode="thumb",
        target_width=200,
        target_height=100,
        new_width=plan.new_width,
        new_height=plan.new_height,
        orig_mode=img.mode,
        orig_color_count=None,
    )
    payload = encode_image_to_bytes(
        normalized_img,
        fmt=fmt,
        jpeg_quality=80,
        webp_quality=80,
    )
    assert_case_properties(
        case,
        decision=plan.decision,
        normalized_img=normalized_img,
        content_type=content_type,
        fmt=fmt,
    )
    assert_golden_match(
        case_payload=case,
        observed_payload=payload,
        manifest=GOLDEN_MANIFEST,
        repo_root=REPO_ROOT,
    )


def test_img_noscale_001_characterization() -> None:
    """IMG-NOSCALE-001 should preserve imaging helper no-scale seam behavior."""
    case = IMAGING_CASES["IMG-NOSCALE-001"]
    img = Image.new("RGB", (100, 50), (30, 180, 90))
    plan = make_scale_plan(
        img,
        target_w=100,
        target_h=50,
        fit_mode="fit",
        allow_upscale=True,
        allow_downscale=True,
    )

    stats = RunStats()
    upload_calls: list[bool] = []

    def uploader() -> tuple[bool, str | None]:
        upload_calls.append(True)
        return True, None

    result = handle_no_scale(
        plan=plan,
        dry_run=True,
        force_upload=True,
        upload_fn=uploader,
        record_label="img-noscale-001",
        default_error="err",
        stats=stats,
    )
    assert result is True
    assert not upload_calls
    assert stats.successes == 1

    normalized_img, content_type, fmt = build_normalized_image(
        img,
        mode="logo",
        target_width=100,
        target_height=50,
        new_width=plan.new_width,
        new_height=plan.new_height,
        orig_mode=img.mode,
        orig_color_count=None,
    )
    payload = encode_image_to_bytes(
        normalized_img,
        fmt=fmt,
        jpeg_quality=80,
        webp_quality=80,
    )
    assert_case_properties(
        case,
        decision=plan.decision,
        normalized_img=normalized_img,
        content_type=content_type,
        fmt=fmt,
    )
    assert_golden_match(
        case_payload=case,
        observed_payload=payload,
        manifest=GOLDEN_MANIFEST,
        repo_root=REPO_ROOT,
    )


def test_img_logo_001_characterization() -> None:
    """IMG-LOGO-001 should preserve transparent-border removal behavior."""
    case = IMAGING_CASES["IMG-LOGO-001"]
    fixture = Image.open(REALISH_LOGO_FIXTURE)
    cropped, changed = remove_padding_from_logo(fixture, sensitivity=20)
    assert changed is True

    normalized_img, content_type, fmt = build_normalized_image(
        cropped,
        mode="logo",
        target_width=6,
        target_height=6,
        new_width=6,
        new_height=6,
        orig_mode=cropped.mode,
        orig_color_count=None,
    )
    payload = encode_image_to_bytes(
        normalized_img,
        fmt=fmt,
        jpeg_quality=80,
        webp_quality=80,
    )
    assert_case_properties(
        case,
        decision="PADDING_REMOVED",
        normalized_img=normalized_img,
        content_type=content_type,
        fmt=fmt,
    )
    assert_golden_match(
        case_payload=case,
        observed_payload=payload,
        manifest=GOLDEN_MANIFEST,
        repo_root=REPO_ROOT,
    )


def test_img_crop_001_characterization() -> None:
    """IMG-CROP-001 should preserve cover+crop centered geometry."""
    case = IMAGING_CASES["IMG-CROP-001"]
    img = Image.new("RGB", (4, 2))
    pixels = [
        (0, 0, 0),
        (10, 0, 0),
        (20, 0, 0),
        (30, 0, 0),
        (0, 10, 0),
        (10, 10, 0),
        (20, 10, 0),
        (30, 10, 0),
    ]
    index = 0
    for y in range(2):
        for x in range(4):
            img.putpixel((x, y), pixels[index])
            index += 1

    normalized_img = cover_and_crop_image(
        img,
        target_width=2,
        target_height=2,
        new_width=4,
        new_height=2,
        mode="RGB",
    )
    payload = encode_image_to_bytes(
        normalized_img,
        fmt="JPEG",
        jpeg_quality=80,
        webp_quality=80,
    )
    assert_case_properties(
        case,
        decision="COVER_CROP",
        normalized_img=normalized_img,
        content_type="image/jpeg",
        fmt="JPEG",
    )
    assert_golden_match(
        case_payload=case,
        observed_payload=payload,
        manifest=GOLDEN_MANIFEST,
        repo_root=REPO_ROOT,
    )


def test_img_encode_001_characterization() -> None:
    """IMG-ENCODE-001 should preserve profile WebP encoding behavior."""
    case = IMAGING_CASES["IMG-ENCODE-001"]
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for y in range(64):
        for x in range(64):
            r = (x * 4) % 256
            g = (y * 4) % 256
            b = ((x + y) * 2) % 256
            alpha = 255 if (x - 32) ** 2 + (y - 32) ** 2 < 24**2 else 80
            img.putpixel((x, y), (r, g, b, alpha))

    normalized_img, content_type, fmt = build_normalized_image(
        img,
        mode="profile",
        target_width=64,
        target_height=64,
        new_width=64,
        new_height=64,
        orig_mode=img.mode,
        orig_color_count=None,
    )
    payload = encode_image_to_bytes(
        normalized_img,
        fmt=fmt,
        jpeg_quality=80,
        webp_quality=80,
    )
    assert_case_properties(
        case,
        decision="ENCODE_PROFILE",
        normalized_img=normalized_img,
        content_type=content_type,
        fmt=fmt,
    )
    assert_golden_match(
        case_payload=case,
        observed_payload=payload,
        manifest=GOLDEN_MANIFEST,
        repo_root=REPO_ROOT,
    )
