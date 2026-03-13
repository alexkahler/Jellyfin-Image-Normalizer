"""Provide pipeline image payload helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .client import JellyfinClient
from .config import ModeRuntimeSettings
from .imaging import ScalePlan, handle_no_scale


def process_item_image_payload(
    *,
    item_id: str,
    label: str,
    image_type: str,
    data: bytes,
    content_type: str | None,
    mode: str,
    settings: ModeRuntimeSettings,
    jf_client: JellyfinClient,
    dry_run: bool,
    force_upload_noscale: bool,
    make_backup: bool,
    backup_root: Path,
    backup_mode: str,
    normalize_image_bytes_fn: Callable[..., tuple[ScalePlan, bytes, str]],
    state_module: Any,
    backdrop_index: int | None = None,
) -> bool:
    """Process item image payload."""
    try:
        plan, payload, normalized_content_type = normalize_image_bytes_fn(
            item_id=item_id,
            label=label,
            image_type=image_type,
            data=data,
            content_type=content_type,
            mode=mode,
            settings=settings,
            make_backup=make_backup,
            backup_root=backup_root,
            backup_mode=backup_mode,
            dry_run=dry_run,
            backdrop_index=backdrop_index,
        )

        def upload_original() -> tuple[bool, str | None]:
            """Run upload original."""
            before_failures = len(state_module.api_failures)
            upload_ok = jf_client.set_item_image_bytes(
                item_id=item_id,
                image_type=image_type,
                data=data,
                content_type=content_type or "application/octet-stream",
                backdrop_index=backdrop_index,
                failures=state_module.api_failures,
            )
            return upload_ok, state_module.latest_api_error(before_failures)

        if mode == "backdrop":
            skip_when_no_scale = False
        else:
            skip_when_no_scale = bool(
                mode in ("logo", "thumb") and not force_upload_noscale
            )

        no_scale_result = handle_no_scale(
            plan=plan,
            dry_run=dry_run,
            force_upload=force_upload_noscale,
            upload_fn=upload_original,
            record_label=label,
            default_error="API upload failed for NO_SCALE image",
            stats=state_module.stats,
            skip_when_no_scale=skip_when_no_scale,
        )
        if no_scale_result is not None:
            return no_scale_result

        if dry_run:
            state_module.stats.record_success()
            return True

        before_failures = len(state_module.api_failures)
        upload_ok = jf_client.set_item_image_bytes(
            item_id=item_id,
            image_type=image_type,
            data=payload,
            content_type=normalized_content_type,
            backdrop_index=backdrop_index,
            failures=state_module.api_failures,
        )
        if upload_ok:
            state_module.stats.record_success()
            return True

        upload_error = state_module.latest_api_error(before_failures)
        state_module.stats.record_error(label, upload_error or "API upload failed")
        return False

    except Exception as exc:
        state_module.log.exception("[ERROR] Failed to process %s", label)
        state_module.stats.record_error(label, str(exc))
        return False
