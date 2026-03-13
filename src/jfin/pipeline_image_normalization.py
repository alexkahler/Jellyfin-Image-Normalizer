"""Provide pipeline image normalization helpers."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from PIL import Image

from .backup import save_backup, should_backup_for_plan
from .config import ModeRuntimeSettings
from .imaging import (
    ScalePlan,
    apply_exif_orientation,
    build_normalized_image,
    encode_image_to_bytes,
    get_palette_color_count,
    log_processing_summary,
    make_scale_plan,
    remove_padding_from_logo,
    record_scale_decision,
)


def plan_and_backup_image(
    *,
    img: Image.Image,
    label: str,
    fit_mode: str,
    settings: ModeRuntimeSettings,
    item_id: str,
    image_type: str,
    raw_bytes: bytes,
    content_type: str | None,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
    dry_run: bool,
    backdrop_index: int | None = None,
) -> ScalePlan:
    """Run plan and backup image."""
    plan = make_scale_plan(
        img=img,
        target_w=settings.target_width,
        target_h=settings.target_height,
        fit_mode=fit_mode,
        allow_upscale=settings.allow_upscale,
        allow_downscale=settings.allow_downscale,
        pad_to_canvas=bool(fit_mode == "fit" and settings.logo_padding == "add"),
    )

    if (
        make_backup
        and not dry_run
        and should_backup_for_plan(plan.decision, backup_mode)
    ):
        save_backup(
            backup_root=backup_root,
            item_id=item_id,
            image_type=image_type,
            data=raw_bytes,
            content_type=content_type,
            overwrite_existing=True,
            backdrop_index=backdrop_index,
        )

    record_scale_decision(label, plan)
    output_w = settings.target_width
    output_h = settings.target_height
    if plan.is_no_scale:
        output_w, output_h = img.size
    elif fit_mode == "fit" and settings.logo_padding != "add":
        output_w = plan.new_width
        output_h = plan.new_height

    log_processing_summary(
        label,
        plan,
        settings.target_width,
        settings.target_height,
        output_w,
        output_h,
        img.mode,
        img.format,
    )
    return plan


def normalize_image_bytes(
    *,
    item_id: str,
    label: str,
    image_type: str,
    data: bytes,
    content_type: str | None,
    mode: str,
    settings: ModeRuntimeSettings,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
    dry_run: bool,
    state_module: Any,
    backdrop_index: int | None = None,
) -> tuple[ScalePlan, bytes, str]:
    """Normalize image bytes."""

    def has_pixels_above_alpha_threshold(src: Image.Image, sensitivity: float) -> bool:
        """Return whether pixels above alpha threshold."""
        rgba = src if src.mode == "RGBA" else src.convert("RGBA")
        alpha = rgba.getchannel("A")
        mask = alpha.point([255 if a > sensitivity else 0 for a in range(256)])
        return mask.getbbox() is not None

    with Image.open(io.BytesIO(data)) as opened_img:
        img: Image.Image = apply_exif_orientation(opened_img)
        orig_mode = img.mode
        fit_mode = "fit" if mode == "logo" else "cover"

        orig_color_count = (
            get_palette_color_count(img)
            if (mode == "logo" and orig_mode == "P")
            else None
        )

        cropped = False
        if mode == "logo" and settings.logo_padding == "remove":
            sensitivity = settings.logo_padding_remove_sensitivity
            fully_transparent = not has_pixels_above_alpha_threshold(img, sensitivity)
            before_size = img.size
            cropped_img, cropped = remove_padding_from_logo(img, sensitivity)
            img = cropped_img

            if fully_transparent:
                state_module.log.warning(
                    "[WARN] Logo padding removal skipped: image is fully "
                    "transparent at sensitivity=%s.",
                    sensitivity,
                )
                state_module.stats.record_warning()
            elif (
                (not cropped)
                and img.size == before_size
                and img.size == (settings.target_width, settings.target_height)
            ):
                state_module.log.warning(
                    "[WARN] Logo padding removal may have failed: image "
                    "remained at target size after crop; borders may contain "
                    "non-obvious pixels."
                )
                state_module.stats.record_warning()

        plan = plan_and_backup_image(
            img=img,
            label=label,
            fit_mode=fit_mode,
            settings=settings,
            item_id=item_id,
            image_type=image_type,
            raw_bytes=data,
            content_type=content_type,
            make_backup=make_backup,
            backup_root=backup_root,
            backup_mode=backup_mode,
            dry_run=dry_run,
            backdrop_index=backdrop_index,
        )

        if plan.is_no_scale and not cropped:
            return plan, data, content_type or "application/octet-stream"

        normalized_img, normalized_content_type, fmt = build_normalized_image(
            img=img,
            mode=mode,
            target_width=settings.target_width,
            target_height=settings.target_height,
            new_width=plan.new_width,
            new_height=plan.new_height,
            orig_mode=orig_mode,
            orig_color_count=orig_color_count,
            logo_padding=settings.logo_padding,
        )
        payload = encode_image_to_bytes(
            normalized_img=normalized_img,
            fmt=fmt,
            jpeg_quality=settings.jpeg_quality,
            webp_quality=settings.webp_quality,
        )

    return plan, payload, normalized_content_type
