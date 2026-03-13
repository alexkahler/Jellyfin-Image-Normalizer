"""Provide imaging ops helpers."""

from __future__ import annotations

import io
from typing import Literal, Optional

from PIL import Image, ImageOps

from . import state

LogoPadding = Literal["add", "remove", "none"]


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


def remove_padding_from_logo(
    img: Image.Image, sensitivity: int | float = 0
) -> tuple[Image.Image, bool]:
    """Crop transparent border padding from a logo image based on alpha values.

    Pixels with alpha <= sensitivity are treated as padding. The returned image
    is cropped to the bounding box of pixels whose alpha > sensitivity.

    Args:
        img: Source image (any Pillow mode). Converted to RGBA for alpha checks.
        sensitivity: Alpha threshold (>= 0). Higher values treat faint/near-
            transparent pixels as padding.

    Returns:
        (img_out, changed) where changed is True if the crop reduced width or
        height.
    """
    if sensitivity < 0:
        raise ValueError("sensitivity must be >= 0")

    rgba = img if img.mode == "RGBA" else img.convert("RGBA")
    alpha = rgba.getchannel("A")
    # Build a LUT so Pillow's type hints match (avoids lambda param type ambiguity for Pylance)
    mask = alpha.point([255 if a > sensitivity else 0 for a in range(256)])
    bbox = mask.getbbox()
    if bbox is None:
        return img, False

    full_bbox = (0, 0, rgba.width, rgba.height)
    if bbox == full_bbox:
        return img, False

    return rgba.crop(bbox), True


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
    """Generic cover + center crop with optional final mode.

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
    logo_padding: LogoPadding = "add",
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
            no_padding=logo_padding != "add",
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
            img, target_width, target_height, new_width, new_height, mode="RGBA"
        )
        state.log.debug("  -> Built normalized %s image in memory", "Profile")
        return normalized_img, "image/webp", "WEBP"

    if mode == "backdrop":
        # For v1: reuse thumb's cover+crop behaviour, but with backdrop-specific size.
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
