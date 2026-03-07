from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from PIL import Image

from . import imaging_ops as _ops
from . import state
from .state import RunStats

LogoPadding = _ops.LogoPadding
apply_exif_orientation = _ops.apply_exif_orientation
get_palette_color_count = _ops.get_palette_color_count
remove_padding_from_logo = _ops.remove_padding_from_logo
fit_contain_and_pad_image = _ops.fit_contain_and_pad_image
cover_and_crop_image = _ops.cover_and_crop_image
build_normalized_image = _ops.build_normalized_image
encode_image_to_bytes = _ops.encode_image_to_bytes


@dataclass
class ScalePlan:
    """Resize decision and resulting size for an image."""

    decision: str
    scale: float
    new_width: int
    new_height: int
    orig_width: int
    orig_height: int

    @property
    def is_no_scale(self) -> bool:
        return self.decision == "NO_SCALE"


def compute_scaled_size(
    img: Image.Image,
    target_w: int,
    target_h: int,
    fit_mode: str,
    allow_upscale: bool,
    allow_downscale: bool,
) -> tuple[float, int, int]:
    """Compute scale factor and new image size for a given fit mode."""
    orig_w, orig_h = img.size
    scale_w = target_w / orig_w
    scale_h = target_h / orig_h

    if fit_mode == "fit":
        scale = min(scale_w, scale_h)
    elif fit_mode == "cover":
        scale = max(scale_w, scale_h)
    else:
        raise ValueError(f"Invalid fit_mode: {fit_mode!r}")

    if not allow_upscale and scale > 1.0:
        scale = 1.0
    if not allow_downscale and scale < 1.0:
        scale = 1.0

    new_w = int(round(orig_w * scale))
    new_h = int(round(orig_h * scale))

    return scale, new_w, new_h


def make_scale_plan(
    img: Image.Image,
    target_w: int,
    target_h: int,
    fit_mode: str,
    allow_upscale: bool,
    allow_downscale: bool,
    pad_to_canvas: bool = False,
) -> ScalePlan:
    """Return a ScalePlan describing how an image should be resized."""
    orig_w, orig_h = img.size
    scale, new_w, new_h = compute_scaled_size(
        img=img,
        target_w=target_w,
        target_h=target_h,
        fit_mode=fit_mode,
        allow_upscale=allow_upscale,
        allow_downscale=allow_downscale,
    )

    if scale > 1.0:
        decision = "SCALE_UP"
    elif scale < 1.0:
        decision = "SCALE_DOWN"
    else:
        decision = "NO_SCALE"

    if (
        pad_to_canvas
        and fit_mode == "fit"
        and decision == "NO_SCALE"
        and orig_w <= target_w
        and orig_h <= target_h
        and (orig_w < target_w or orig_h < target_h)
    ):
        decision = "PAD_ONLY"

    return ScalePlan(
        decision=decision,
        scale=scale,
        new_width=new_w,
        new_height=new_h,
        orig_width=orig_w,
        orig_height=orig_h,
    )


def record_scale_decision(label: str, plan: ScalePlan) -> None:
    """Track whether an image was upscaled/downscaled for reporting."""
    if plan.decision == "SCALE_UP":
        state.upscaled_images.append(
            (label, plan.orig_width, plan.orig_height, plan.new_width, plan.new_height)
        )
    elif plan.decision == "SCALE_DOWN":
        state.downscaled_images.append(
            (label, plan.orig_width, plan.orig_height, plan.new_width, plan.new_height)
        )


def log_processing_summary(
    label: str,
    plan: ScalePlan,
    target_width: int,
    target_height: int,
    output_width: int,
    output_height: int,
    orig_mode: str,
    img_format: Any,
) -> None:
    """Emit a concise summary for a processed image."""
    state.log.info(
        "[PROCESS:%s] %s (%sx%s) -> %sx%s (target %sx%s, output %sx%s, orig mode=%s, format=%s)",
        plan.decision,
        label,
        plan.orig_width,
        plan.orig_height,
        plan.new_width,
        plan.new_height,
        target_width,
        target_height,
        output_width,
        output_height,
        orig_mode,
        img_format,
    )


def handle_no_scale(
    *,
    plan: ScalePlan,
    dry_run: bool,
    force_upload: bool,
    upload_fn: Callable[[], tuple[bool, str | None]] | None,
    record_label: str,
    default_error: str,
    stats: RunStats,
    skip_when_no_scale: bool = False,
) -> bool | None:
    """Common NO_SCALE handler returning True/False or None to continue processing."""
    if not plan.is_no_scale:
        return None

    if dry_run:
        if skip_when_no_scale:
            stats.record_skip(count_processed=True)
        else:
            stats.record_success()
        return True

    if not force_upload or upload_fn is None:
        if skip_when_no_scale:
            stats.record_skip(count_processed=True)
        else:
            stats.record_success()
        return True

    upload_ok, upload_error = upload_fn()
    if upload_ok:
        if skip_when_no_scale:
            stats.record_skip(count_processed=True)
        else:
            stats.record_success()
        return True

    stats.record_error(record_label, upload_error or default_error)
    return False
