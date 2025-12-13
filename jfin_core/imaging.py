from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional

from PIL import Image, ImageOps

from . import state
from .state import RunStats


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
    orig_mode: str,
    img_format: Any,
) -> None:
    """Emit a concise summary for a processed image."""
    state.log.info(
        "[PROCESS:%s] %s (%sx%s) -> %sx%s (canvas %sx%s, orig mode=%s, format=%s)",
        plan.decision,
        label,
        plan.orig_width,
        plan.orig_height,
        plan.new_width,
        plan.new_height,
        target_width,
        target_height,
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


def apply_exif_orientation(img: Image.Image) -> Image.Image:
    """Transpose the image according to EXIF orientation, if present."""
    ORIENTATION_TAG = 274
    try:
        exif = img.getexif()
    except Exception:
        exif = None

    orientation = None
    if exif:
        orientation = exif.get(ORIENTATION_TAG)

    if orientation in (5, 6, 7, 8):
        if img.height >= img.width:
            return img

    try:
        return ImageOps.exif_transpose(img)
    except Exception:
        return img


def get_palette_color_count(img: Image.Image) -> int | None:
    """Estimate number of colors used in a paletted image (up to 256)."""
    try:
        colors = img.getcolors(maxcolors=1 << 24)
        if colors is None:
            return None
        return min(len(colors), 256)
    except Exception:
        return None


def fit_contain_and_pad_image(
    img: Image.Image,
    target_width: int,
    target_height: int,
    orig_mode: str,
    orig_color_count: int | None,
    new_width: int,
    new_height: int,
    no_padding: bool,
) -> Image.Image:
    """Build a normalized logo image in memory."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    if no_padding:
        canvas = resized
    else:
        canvas = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
        offset_x = (target_width - new_width) // 2
        offset_y = (target_height - new_height) // 2
        canvas.paste(resized, (offset_x, offset_y), resized)

    if orig_mode == "P":
        colors = orig_color_count or 256
        colors = max(2, min(colors, 256))
        result = canvas.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors)
        state.log.debug("  -> Built paletted logo with ~%s colors", colors)
    elif orig_mode == "LA":
        result = canvas.convert("LA")
        state.log.debug("  -> Built logo in LA (grayscale + alpha)")
    else:
        result = canvas

    return result


def cover_and_crop_image(
    img: Image.Image,
    target_width: int,
    target_height: int,
    new_width: int,
    new_height: int,
    mode: Optional[Literal["RGB", "RGBA", "rgb", "rgba"]] = None,
) -> Image.Image:
    """
    Generic cover + center crop with optional final mode.
    - If mode="RGB": tolerate grayscale input ("L") and ensure RGB output.
    - If mode="RGBA": always convert to RGBA and preserve alpha.
    - If mode=None: keep the image's current mode (no conversions).
    """
    mode_upper = mode.upper() if mode is not None else None
        
    # Pre-conversion rules
    if mode_upper == "RGB":
        if img.mode == "L":
            # allow "L" for now; will convert after crop
            pass
        elif img.mode != "RGB":
            img = img.convert("RGB")
    elif mode_upper == "RGBA" and img.mode != "RGBA":
        img = img.convert("RGBA")

    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    left = max(0, (new_width - target_width) // 2)
    top = max(0, (new_height - target_height) // 2)
    right = left + target_width
    bottom = top + target_height

    cropped = resized.crop((left, top, right, bottom))

    # Post-conversion to guarantee output mode
    if mode_upper == "RGB" and cropped.mode != "RGB":
        cropped = cropped.convert("RGB")

    return cropped


def build_normalized_image(
    img: Image.Image,
    mode: str,
    target_width: int,
    target_height: int,
    new_width: int,
    new_height: int,
    orig_mode: str,
    orig_color_count: int | None,
    no_padding: bool = False,
) -> tuple[Image.Image, str, str]:
    """Return normalized image plus content-type/format tuple for the requested mode."""
    if mode == "logo":
        normalized_img = fit_contain_and_pad_image(
            img,
            target_width,
            target_height,
            orig_mode,
            orig_color_count,
            new_width,
            new_height,
            no_padding=no_padding,
        )
        state.log.debug("  -> Built normalized %s image in memory", "Logo")
        return normalized_img, "image/png", "PNG"
    if mode == "thumb":
        normalized_img = cover_and_crop_image(
            img,
            target_width,
            target_height,
            new_width,
            new_height,
            mode="RGB",
        )
        state.log.debug("  -> Built normalized %s image in memory", "Thumb")
        return normalized_img, "image/jpeg", "JPEG"
    if mode == "profile":
        normalized_img = cover_and_crop_image(
            img,
            target_width,
            target_height,
            new_width,
            new_height,
            mode="RGBA"
        )
        state.log.debug("  -> Built normalized %s image in memory", "Profile")
        return normalized_img, "image/webp", "WEBP"
    
    if mode == "backdrop":
        # For v1: reuse thumb’s cover+crop behaviour, but with backdrop-specific size.
        normalized_img = cover_and_crop_image(
            img,
            target_width,
            target_height,
            new_width,
            new_height,
            mode="RGB",
        )
        state.log.debug("  -> Built normalized %s image in memory", "Backdrop")
        return normalized_img, "image/jpeg", "JPEG"


    raise ValueError(f"Unsupported mode: {mode}")


def encode_image_to_bytes(
    normalized_img: Image.Image,
    fmt: str,
    jpeg_quality: int,
    webp_quality: int,
) -> bytes:
    """Encode a Pillow Image to bytes using mode-specific options."""
    buf = io.BytesIO()
    if fmt == "PNG":
        normalized_img.save(buf, format=fmt, optimize=True)
    elif fmt == "JPEG":
        normalized_img.save(
            buf,
            format=fmt,
            quality=jpeg_quality,
            optimize=True,
            progressive=True,
        )
    elif fmt == "WEBP":
        normalized_img.save(
            buf,
            format=fmt,
            quality=webp_quality,
            method=6,
        )
    else:
        raise ValueError(f"Unsupported format: {fmt!r}")

    return buf.getvalue()
