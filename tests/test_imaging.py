import io

from PIL import Image
from typing import Literal, Optional

from jfin_core import state
from jfin_core.imaging import (
    ScalePlan,
    fit_contain_and_pad_image,
    build_normalized_image,
    cover_and_crop_image,
    encode_image_to_bytes,
    handle_no_scale,
    make_scale_plan,
    remove_padding_from_logo,
)


def test_make_scale_plan_upscale(rgb_image_bytes):
    img = Image.open(io.BytesIO(rgb_image_bytes(size=(100, 50))))
    plan = make_scale_plan(img, target_w=200, target_h=100, fit_mode="fit", allow_upscale=True, allow_downscale=True)
    assert plan.decision == "SCALE_UP"
    assert (plan.new_width, plan.new_height) == (200, 100)


def test_handle_no_scale_dry_run_skips_upload():
    called = []

    def uploader():
        called.append(True)
        return True, None

    plan = ScalePlan("NO_SCALE", 1.0, 100, 50, 100, 50)
    result = handle_no_scale(
        plan=plan,
        dry_run=True,
        force_upload=True,
        upload_fn=uploader,
        record_label="sample",
        default_error="err",
        stats=state.stats,
    )
    assert result is True
    assert not called
    assert state.stats.successes == 1


def test_build_logo_image_respects_canvas(rgb_image_bytes):
    img = Image.open(io.BytesIO(rgb_image_bytes(size=(50, 50))))
    logo = fit_contain_and_pad_image(
        img=img,
        target_width=100,
        target_height=60,
        orig_mode=img.mode,
        orig_color_count=None,
        new_width=80,
        new_height=40,
        no_padding=False,
    )
    assert logo.size == (100, 60)


def test_remove_padding_from_logo_crops_transparent_border() -> None:
    img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    for y in range(2, 8):
        for x in range(2, 8):
            img.putpixel((x, y), (255, 255, 255, 255))

    cropped, changed = remove_padding_from_logo(img, sensitivity=0)
    assert changed is True
    assert cropped.size == (6, 6)


def test_remove_padding_from_logo_does_not_crop_when_border_is_not_transparent() -> None:
    img = Image.new("RGBA", (10, 10), (10, 20, 30, 255))
    cropped, changed = remove_padding_from_logo(img, sensitivity=0)
    assert changed is False
    assert cropped.size == img.size


def test_remove_padding_from_logo_sensitivity_threshold() -> None:
    img = Image.new("RGBA", (10, 10), (0, 0, 0, 10))
    for y in range(2, 8):
        for x in range(2, 8):
            img.putpixel((x, y), (255, 255, 255, 255))

    cropped0, changed0 = remove_padding_from_logo(img, sensitivity=0)
    assert changed0 is False
    assert cropped0.size == img.size

    cropped10, changed10 = remove_padding_from_logo(img, sensitivity=10)
    assert changed10 is True
    assert cropped10.size == (6, 6)


def test_remove_padding_from_logo_fully_transparent_returns_unchanged() -> None:
    img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    cropped, changed = remove_padding_from_logo(img, sensitivity=0)
    assert changed is False
    assert cropped.size == img.size


def test_remove_padding_roundtrip_add_then_remove_restores_pixels() -> None:
    base = Image.new("RGBA", (6, 4), (10, 20, 30, 255))
    padded = fit_contain_and_pad_image(
        img=base,
        target_width=12,
        target_height=8,
        orig_mode=base.mode,
        orig_color_count=None,
        new_width=6,
        new_height=4,
        no_padding=False,
    )
    cropped, changed = remove_padding_from_logo(padded, sensitivity=0)
    assert changed is True
    assert cropped.size == base.size
    assert cropped.convert("RGBA").tobytes() == base.tobytes()


# test_imaging.py
import pytest
from pathlib import Path
from PIL import Image

from jfin_core.imaging import cover_and_crop_image


def test_cover_and_crop_centers_correct_region() -> None:
    """
    Use a tiny 4x2 patterned image so we can verify the crop picks the centered
    region correctly when new_width > target_width.
    """
    img = Image.new("RGB", (4, 2))
    # Row 0: (0,0,0), (10,0,0), (20,0,0), (30,0,0)
    # Row 1: (0,10,0), (10,10,0), (20,10,0), (30,10,0)
    colors = [
        (0, 0, 0),
        (10, 0, 0),
        (20, 0, 0),
        (30, 0, 0),
        (0, 10, 0),
        (10, 10, 0),
        (20, 10, 0),
        (30, 10, 0),
    ]
    idx = 0
    for y in range(2):
        for x in range(4):
            img.putpixel((x, y), colors[idx])
            idx += 1

    # target = 2x2, new size = 4x2 (same as original, so resize is effectively a no-op)
    out = cover_and_crop_image(
        img=img,
        target_width=2,
        target_height=2,
        new_width=4,
        new_height=2,
        mode="RGB",
    )

    assert out.size == (2, 2)

    # Crop box in function: left = (4-2)//2 = 1, top = (2-2)//2 = 0
    # So we expect columns 1 and 2 from both rows
    expected_pixels = [
        img.getpixel((1, 0)), img.getpixel((2, 0)),
        img.getpixel((1, 1)), img.getpixel((2, 1)),
    ]
    actual_pixels = [
        out.getpixel((0, 0)), out.getpixel((1, 0)),
        out.getpixel((0, 1)), out.getpixel((1, 1)),
    ]
    assert actual_pixels == expected_pixels


@pytest.mark.parametrize(
    "orig_size, target_size, new_size",
    [
        # Scale down: original bigger than new, then crop to smaller target
        ((200, 200), (80, 80), (120, 120)),
        # Scale up: original smaller than new, then crop to target
        ((40, 40), (50, 50), (80, 80)),
        # Only width cropped
        ((100, 50), (50, 50), (100, 50)),
        # Only height cropped
        ((50, 100), (50, 50), (50, 100)),
        # No crop (new == target)
        ((80, 60), (80, 60), (80, 60)),
    ],
)
def test_cover_and_crop_respects_target_size(
    orig_size: tuple[int, int],
    target_size: tuple[int, int],
    new_size: tuple[int, int],
) -> None:
    """
    For a variety of scale-up/down and crop configurations, the output must
    always be exactly target_width x target_height, regardless of original size.
    """
    orig_w, orig_h = orig_size
    tgt_w, tgt_h = target_size
    new_w, new_h = new_size

    img = Image.new("RGB", (orig_w, orig_h), color=(123, 45, 67))

    out = cover_and_crop_image(
        img=img,
        target_width=tgt_w,
        target_height=tgt_h,
        new_width=new_w,
        new_height=new_h,
        mode=None,  # keep mode as-is
    )

    assert out.size == (tgt_w, tgt_h)
    # mode should be preserved when mode=None
    assert out.mode == img.mode


@pytest.mark.parametrize(
    "input_mode, mode_arg, expected_mode",
    [
        ("RGBA", None, "RGBA"),   # keep alpha
        ("RGBA", "RGB", "RGB"),   # drop alpha
        ("RGB", "RGBA", "RGBA"),  # add alpha channel
        ("L", "RGB", "RGB"),      # grayscale -> RGB
    ],
)
def test_cover_and_crop_mode_conversion(
    input_mode: str,
    mode_arg: Optional[Literal["RGB", "RGBA"]],
    expected_mode: str,
) -> None:
    """
    Verify that the function enforces the requested mode behavior:
    - mode=None: preserve the image mode
    - mode="RGB": ensure RGB (no alpha)
    - mode="RGBA": ensure RGBA (with alpha)
    - "L" input with mode="RGB": tolerated and converted post-crop
    """
    size = (8, 8)

    if input_mode == "RGBA":
        img = Image.new("RGBA", size, color=(10, 20, 30, 255))
    elif input_mode == "RGB":
        img = Image.new("RGB", size, color=(10, 20, 30))
    elif input_mode == "L":
        img = Image.new("L", size, color=128)
    else:
        raise ValueError(f"Unexpected test input mode {input_mode!r}")

    out = cover_and_crop_image(
        img=img,
        target_width=8,
        target_height=8,
        new_width=8,
        new_height=8,
        mode=mode_arg,
    )

    assert out.size == (8, 8)
    assert out.mode == expected_mode


def test_cover_and_crop_preserves_alpha_when_mode_none() -> None:
    """
    If mode=None and the input has alpha (RGBA), the alpha channel should be preserved.
    We craft a simple image with one fully transparent pixel and verify it survives.
    """
    size = (4, 4)
    img = Image.new("RGBA", size, color=(100, 150, 200, 255))
    # Make the center pixel fully transparent
    center = (size[0] // 2, size[1] // 2)
    img.putpixel(center, (100, 150, 200, 0))

    out = cover_and_crop_image(
        img=img,
        target_width=4,
        target_height=4,
        new_width=4,
        new_height=4,
        mode=None,
    )

    assert out.mode == "RGBA"
    assert out.size == (4, 4)
    
    pixel = out.getpixel(center)
    # Help the type checker: for RGBA we expect a 4-tuple of ints
    assert isinstance(pixel, tuple)
    assert len(pixel) == 4
    # Center pixel should still be transparent
    *_, alpha = pixel
    assert alpha == 0


def test_encode_image_to_bytes_roundtrip(rgb_image_bytes):
    img = Image.open(io.BytesIO(rgb_image_bytes(size=(64, 64))))
    normalized, content_type, fmt = build_normalized_image(
        img,
        mode="thumb",
        target_width=64,
        target_height=64,
        new_width=64,
        new_height=64,
        orig_mode=img.mode,
        orig_color_count=None,
    )
    payload = encode_image_to_bytes(normalized, fmt=fmt, jpeg_quality=80, webp_quality=80)
    assert payload
    assert content_type == "image/jpeg"


def test_handle_no_scale_forces_upload(rgb_image_bytes):
    calls = []

    def uploader():
        calls.append(True)
        return True, None

    plan = ScalePlan("NO_SCALE", 1.0, 50, 50, 50, 50)
    initial_successes = state.stats.successes
    result = handle_no_scale(
        plan=plan,
        dry_run=False,
        force_upload=True,
        upload_fn=uploader,
        record_label="noscale-sample",
        default_error="err",
        stats=state.stats,
    )
    assert result is True
    assert calls == [True]
    assert state.stats.successes == initial_successes + 1
