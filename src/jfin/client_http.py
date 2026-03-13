"""Provide client http helpers."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any, Callable

import requests

from .http_error import http_error

if TYPE_CHECKING:
    from .client import JellyfinClient

SleepFn = Callable[[float], Any]
RequestFn = Callable[..., requests.Response]


def _request_with_retry(
    client: JellyfinClient,
    *,
    request_fn: RequestFn,
    url: str,
    params: dict[str, Any] | None,
    stream: bool,
    label: str,
    sleep_fn: SleepFn,
    allow_retry: bool,
) -> requests.Response | None:
    """Run  request with retry."""
    attempts = 1 if not allow_retry else max(1, int(client.retry_count))
    backoff = 0.0 if not allow_retry else max(0.0, float(client.backoff_base))
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            resp = request_fn(
                url,
                headers=client._headers(),
                params=params,
                timeout=client.timeout,
                verify=client.verify_tls,
                stream=stream,
            )
        except Exception as exc:
            last_error = str(exc)
        else:
            if resp.ok:
                return resp
            last_error = http_error(resp)
        client.logger.error(
            "[API-ERROR] Attempt %s/%s failed for %s: %s",
            attempt,
            attempts,
            label,
            last_error,
        )
        if allow_retry and attempt < attempts and backoff > 0:
            sleep_fn(backoff)
            backoff *= 2
    return None


def get_response(
    client: JellyfinClient,
    *,
    request_fn: RequestFn,
    url: str,
    params: dict[str, Any] | None,
    stream: bool,
    label: str,
    sleep_fn: SleepFn,
) -> requests.Response | None:
    """Get response."""
    return _request_with_retry(
        client,
        request_fn=request_fn,
        url=url,
        params=params,
        stream=stream,
        label=label,
        sleep_fn=sleep_fn,
        allow_retry=True,
    )


def head_response(
    client: JellyfinClient,
    *,
    request_fn: RequestFn,
    url: str,
    params: dict[str, Any] | None,
    stream: bool,
    label: str,
    sleep_fn: SleepFn,
    allow_retry: bool,
) -> requests.Response | None:
    """Run head response."""
    return _request_with_retry(
        client,
        request_fn=request_fn,
        url=url,
        params=params,
        stream=stream,
        label=label,
        sleep_fn=sleep_fn,
        allow_retry=allow_retry,
    )


def test_connection(
    client: JellyfinClient, *, request_fn: RequestFn, sleep_fn: SleepFn
) -> bool:
    """Run test connection."""
    url = f"{client.base_url}/System/Info"
    attempts = max(1, int(client.retry_count))
    backoff = max(0.0, float(client.backoff_base))
    last_error = "Unknown error"
    for attempt in range(1, attempts + 1):
        try:
            client.logger.debug("Knock, knock.")
            resp = request_fn(
                url,
                headers=client._headers(),
                timeout=client.timeout,
                verify=client.verify_tls,
            )
        except Exception as exc:
            last_error = f"Exception: {exc}"
        else:
            status = resp.status_code
            if status == 401:
                client.logger.critical(
                    "[API-ERROR] Unauthorized (401) when calling /System/Info. Check API key."
                )
                return False
            if status == 403:
                client.logger.critical(
                    "[API-ERROR] Forbidden (403) when calling /System/Info. Check Jellyfin permissions."
                )
                return False
            if status == 503:
                last_error = "HTTP 503 Service Unavailable (server starting or temporarily unavailable). Try again later."
            elif not resp.ok:
                last_error = http_error(resp)
            else:
                try:
                    payload = resp.json()
                except Exception as exc:
                    client.logger.error(
                        "[API-ERROR] Failed to decode JSON from /System/Info: %s (%s)",
                        exc,
                        (resp.text or "")[:200].replace("\n", " "),
                    )
                    return False
                if isinstance(payload, dict) and payload.get("IsShuttingDown"):
                    client.logger.error(
                        "[API-ERROR] Jellyfin reported that it is shutting down; aborting to avoid data loss."
                    )
                    return False
                client.logger.debug("Who's there?")
                client.logger.info("[API-TEST] Jellyfin connection OK.")
                return True
        client.logger.error(
            "[API-ERROR] Attempt %s/%s failed for system info: %s.",
            attempt,
            attempts,
            last_error,
        )
        if attempt < attempts and backoff > 0:
            client.logger.debug("*Waiting for a response...*")
            sleep_fn(backoff)
            backoff *= 2
    return False


def post_image(
    client: JellyfinClient,
    *,
    request_fn: RequestFn,
    sleep_fn: SleepFn,
    url: str,
    headers: dict[str, str],
    data: bytes,
    encode_base64: bool,
    success_message: str,
    error_label: str,
    action_label: str,
    failures: list[dict[str, Any]] | None,
    failure_entry: dict[str, Any],
    fail_fast_prefix: str,
) -> bool:
    """Run post image."""
    if not client._writes_allowed(action_label):
        client.logger.debug(
            "DRY RUN - Would upload normalized image for %s.", action_label
        )
        return True
    attempts = max(1, int(client.retry_count))
    backoff = max(0.0, float(client.backoff_base))
    last_error_msg = "Unknown error"
    payload = base64.b64encode(data) if encode_base64 else data
    for attempt in range(1, attempts + 1):
        try:
            resp = request_fn(
                url,
                headers=headers,
                data=payload,
                timeout=client.timeout,
                verify=client.verify_tls,
            )
        except Exception as exc:
            last_error_msg = f"Exception: {exc}"
        else:
            if resp.ok:
                if success_message.startswith("[API]"):
                    client.logger.debug(success_message)
                else:
                    client.logger.info(success_message)
                if client.delay > 0:
                    sleep_fn(client.delay)
                return True
            last_error_msg = http_error(resp)
        client.logger.error(
            "[API-ERROR] Attempt %s/%s failed for %s: %s",
            attempt,
            attempts,
            error_label,
            last_error_msg,
        )
        if attempt < attempts:
            sleep_fn(backoff)
            backoff *= 2.0
    failure_entry["error"] = last_error_msg
    if failures is not None:
        failures.append(failure_entry)
    if client.fail_fast:
        raise RuntimeError(f"{fail_fast_prefix}: {last_error_msg}")
    return False


def delete_image(
    client: JellyfinClient,
    *,
    request_fn: RequestFn,
    sleep_fn: SleepFn,
    uuid: str,
    image_type: str,
    image_index: int | None,
) -> bool:
    """Run delete image."""
    if image_type == "Primary":
        url = f"{client.base_url}/UserImage?userId={uuid}"
    elif image_type == "Backdrop":
        url = f"{client.base_url}/Items/{uuid}/Images/{image_type}/{image_index}"
    else:
        raise ValueError(f"Unsupported image type for deletion: {image_type}")
    if not client._writes_allowed(f"delete profile image for user {uuid}"):
        client.logger.debug("DRY RUN - Would delete existing image for uuid %s.", uuid)
        return True
    attempts = max(1, int(client.retry_count))
    backoff = max(0.0, float(client.backoff_base))
    last_error_msg = "Unknown error"
    headers = client._headers()
    for attempt in range(1, attempts + 1):
        try:
            resp = request_fn(
                url, headers=headers, timeout=client.timeout, verify=client.verify_tls
            )
        except Exception as exc:
            client.logger.error(
                "[API-ERROR] Failed to get image for uuid %s: %s", uuid, exc
            )
            return False
        else:
            if resp.ok:
                client.logger.debug(
                    f"[API] Deleted image for uuid {uuid} type {image_type}"
                )
                if client.delay > 0:
                    sleep_fn(client.delay)
                return True
            last_error_msg = http_error(resp)
        client.logger.debug(
            "  -> Attempt %s/%s failed at deleting image for uuid %s: %s",
            attempt,
            attempts,
            uuid,
            last_error_msg,
        )
        if attempt < attempts:
            sleep_fn(backoff)
            backoff *= 2.0
    if client.fail_fast:
        raise RuntimeError(
            "[API-ERROR] Deletion failed for item "
            f"{uuid} type {image_type}: "
            f"{last_error_msg}"
        )
    return False
