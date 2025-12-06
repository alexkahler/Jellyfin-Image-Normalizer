import io

from PIL import Image

from jfin_core import state
from jfin_core.imaging import (
    ScalePlan,
    build_logo_image,
    build_normalized_image,
    build_thumb_image,
    encode_image_to_bytes,
    handle_no_scale,
    make_scale_plan,
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
    logo = build_logo_image(
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


def test_build_thumb_image_crops_to_canvas(rgb_image_bytes):
    img = Image.open(io.BytesIO(rgb_image_bytes(size=(200, 200))))
    thumb = build_thumb_image(img, target_width=100, target_height=50, new_width=200, new_height=200)
    assert thumb.size == (100, 50)


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
    assert state.stats.successes == 1
