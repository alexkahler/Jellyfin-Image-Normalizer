"""Provide cli runtime args helpers."""

from __future__ import annotations

import argparse
from typing import Callable


def parse_args(
    *,
    default_config_name: str,
    parse_size_pair_fn: Callable[[str], tuple[int, int]],
) -> argparse.Namespace:
    """Parse args."""
    parser = argparse.ArgumentParser(
        description=(
            "Normalize Jellyfin images (logos, thumbs, profiles) via the Jellyfin API.\n\n"
            "- Logos: scale to fit inside canvas (defaults from config), preserve aspect ratio and pad with transparency.\n"
            "- Thumbs: scale to cover canvas (defaults from config), preserve aspect ratio and center crop.\n"
            "- Profile: cover-scale, center crop, and encode to WebP (defaults from config).\n\n"
            "Configuration (Jellyfin URL, API key, discovery filters, sizes, etc.) "
            "is loaded from a TOML config file. Use --generate-config to create one."
        )
    )
    add = parser.add_argument
    add(
        "--config",
        help=f"Path to TOML config file (default: {default_config_name} in repo root).",
    )
    add(
        "--generate-config",
        action="store_true",
        help="Generate a default config file and exit. Does not process images.",
    )
    add(
        "--test-jf",
        action="store_true",
        help="Test Jellyfin connection (using config/CLI settings) and exit.",
    )
    add(
        "--mode",
        help="Image types to handle, e.g. 'logo', 'thumb', 'profile', 'backdrop', or a pipe-separated list like 'logo|thumb'. Overrides the config 'operations' value if provided.",
    )
    add(
        "--logo-target-size",
        metavar="WIDTHxHEIGHT",
        type=parse_size_pair_fn,
        help="Override logo canvas size with WIDTHxHEIGHT (e.g., 800x310).",
    )
    add(
        "--thumb-target-size",
        metavar="WIDTHxHEIGHT",
        type=parse_size_pair_fn,
        help="Override thumb canvas size with WIDTHxHEIGHT (e.g., 1000x562).",
    )
    add(
        "--backdrop-target-size",
        metavar="WIDTHxHEIGHT",
        type=parse_size_pair_fn,
        help="Override backdrop canvas size with WIDTHxHEIGHT (e.g., 1920x1080).",
    )
    add(
        "--profile-target-size",
        metavar="WIDTHxHEIGHT",
        type=parse_size_pair_fn,
        help="Override profile canvas size with WIDTHxHEIGHT (e.g., 256x256).",
    )
    add(
        "--thumb-jpeg-quality",
        type=int,
        default=None,
        help="JPEG quality for thumb output (1-95). Overrides config thumb.jpeg_quality.",
    )
    add(
        "--backdrop-jpeg-quality",
        type=int,
        default=None,
        help="JPEG quality for backdrop output (1-95). Overrides config backdrop.jpeg_quality.",
    )
    add(
        "--profile-webp-quality",
        type=int,
        default=None,
        help="WebP quality for profile output (1-100). Overrides config profile.webp_quality.",
    )
    add(
        "--dry-run",
        action="store_true",
        help="Only report actions, do not modify files or call the API.",
    )
    add(
        "--backup",
        action="store_true",
        help="Save originals to the configured backup folder before uploading replacements.",
    )
    add(
        "--single",
        help="Process a single Jellyfin item by id (logo/thumb/backdrop). Use --mode to filter which image types run.",
    )
    add(
        "--restore",
        action="store_true",
        help="Restore images from the backup folder via the API. Use with --mode to pick which image types.",
    )
    add(
        "--restore-all",
        action="store_true",
        help="Restore all backup images (logo, thumb, profile) from the backup folder. Must be used alone (aside from optional --config/logging flags).",
    )
    add(
        "--no-upscale",
        action="store_true",
        help="Do not upscale images; only allow downscaling.",
    )
    add(
        "--no-downscale",
        action="store_true",
        help="Do not downscale images; only allow upscaling.",
    )
    add(
        "--logo-padding",
        choices=("add", "remove", "none"),
        default=None,
        help="Logo padding policy: add (pad to canvas), remove (crop transparent border before scaling; never pad), or none (no add/remove; only scale). Overrides config logo.padding.",
    )
    add(
        "--jf-url",
        help="Override Jellyfin base URL from config (e.g. https://jellyfin.example.com).",
    )
    add("--jf-api-key", help="Override Jellyfin API key from config.")
    add(
        "--libraries",
        help="Comma- or pipe-separated library names to include. Overrides config.",
    )
    add(
        "--item-types",
        help="Item types to include for discovery (movies|series, pipe/comma-separated). Overrides config.",
    )
    add(
        "--jf-delay-ms",
        type=int,
        help="Delay in milliseconds between API calls (overrides config jf_delay_ms).",
    )
    add(
        "--force-upload-noscale",
        action="store_true",
        help="For NO_SCALE images (already at target size), force an upload to Jellyfin anyway. Useful for re-registering pre-normalized artwork.",
    )
    add(
        "--silent",
        "-s",
        action="store_true",
        help="Suppress CLI output (file logging continues).",
    )
    add(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging to CLI (overrides logging.cli_level).",
    )
    return parser.parse_args()
