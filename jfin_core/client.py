from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from . import state


@dataclass
class JellyfinClient:
    """Wrapper for Jellyfin API calls with retry/backoff and dry-run safety."""

    base_url: str
    api_key: str
    client_name: str = "Jellyfin Image Normalizer"
    client_version: str = "unknown"
    timeout: float = 15.0
    verify_tls: bool = True
    delay: float = 0.1
    retry_count: int = 3
    backoff_base: float = 0.5
    fail_fast: bool = False
    dry_run: bool = True
    logger: Any = field(default_factory=lambda: state.log)


    def __post_init__(self) -> None:
        # Normalize base_url once to avoid repeated rstrip calls.
        self.base_url = self.base_url.rstrip("/")


    def _headers(self) -> dict[str, str]:
        """Return MediaBrowser auth headers for Jellyfin requests."""
        auth_value = (
            f'MediaBrowser Token="{self.api_key}", '
            f'Client="{self.client_name}", '
            f'Version="{self.client_version}"'
        )
        return {"Authorization": auth_value}


    def _get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        stream: bool = False,
        label: str = "request",
    ) -> requests.Response | None:
        """Wrap requests.get with logging, retry, and status validation."""
        attempts = max(1, int(self.retry_count))
        backoff = max(0.0, float(self.backoff_base))
        last_error = None

        for attempt in range(1, attempts + 1):
            try:
                resp = requests.get(
                    url,
                    headers=self._headers(),
                    params=params,
                    timeout=self.timeout,
                    verify=self.verify_tls,
                    stream=stream,
                )
            except Exception as e:
                last_error = str(e)
                resp = None
            else:
                if resp.ok:
                    return resp
                snippet = (resp.text or "")[:200].replace("\n", " ")
                last_error = f"HTTP {resp.status_code} {snippet}"
                resp = None

            self.logger.error(
                "[API-ERROR] Attempt %s/%s failed for %s: %s",
                attempt,
                attempts,
                label,
                last_error,
            )
            if attempt < attempts and backoff > 0:
                time.sleep(backoff)
                backoff *= 2

        return None


    def _get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        label: str,
    ) -> Any | None:
        """GET and decode JSON, logging errors on decode/HTTP failures."""
        resp = self._get(url, params=params, stream=False, label=label)
        if resp is None:
            return None
        try:
            return resp.json()
        except Exception as e:
            snippet = (resp.text or "")[:200].replace("\n", " ")
            self.logger.error(
                "[API-ERROR] Failed to decode JSON from %s: %s (%s)",
                url,
                e,
                snippet,
            )
            return None


    def _head(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        stream: bool = False,
        label: str = "request",
        allow_retry: bool = True,
    ) -> requests.Response | None:
        """Wrap requests.head with logging, retry, and status validation."""

        attempts = 1 if not allow_retry else max(1, int(self.retry_count))
        backoff = 0.0 if not allow_retry else max(0.0, float(self.backoff_base))

        for attempt in range(1, attempts + 1):
            try:
                resp = requests.head(
                    url,
                    headers=self._headers(),
                    params=params,
                    timeout=self.timeout,
                    verify=self.verify_tls,
                    stream=stream,
                )
            except Exception as e:
                resp = None
            else:
                if resp.ok:
                    return resp
                
            if allow_retry and attempt < attempts and backoff > 0:
                time.sleep(backoff)
                backoff *= 2

        return None


    def _writes_allowed(self, action: str) -> bool:
        if self.dry_run:
            return False
        return True


    def _guess_content_type(self, image_path: Path) -> str | None:
        """Infer a basic content-type from a file suffix."""
        suffix = image_path.suffix.lower()
        if suffix == ".png":
            return "image/png"
        if suffix in (".jpg", ".jpeg"):
            return "image/jpeg"
        return "application/octet-stream"


    def test_connection(self) -> bool:
        """Verify /System/Info connectivity and server readiness.

        Returns True when reachable and not shutting down. Logs specific
        failures for auth errors (401/403), temporary unavailability (503),
        shutdown state, JSON decode issues, or other HTTP/connection problems.
        """
        url = f"{self.base_url}/System/Info"

        attempts = max(1, int(self.retry_count))
        backoff = max(0.0, float(self.backoff_base))
        last_error = "Unknown error"

        for attempt in range(1, attempts + 1):
            try:
                self.logger.debug("Knock, knock.")
                resp = requests.get(
                    url,
                    headers=self._headers(),
                    timeout=self.timeout,
                    verify=self.verify_tls,
                )
            except Exception as exc:
                last_error = f"Exception: {exc}"
                resp = None
            else:
                status = resp.status_code
                if status == 401:
                    self.logger.critical(
                        (
                            "[API-ERROR] Unauthorized (401) when "
                            "calling /System/Info. "
                            "Check API key."
                        )
                    )
                    return False
                if status == 403:
                    self.logger.critical(
                        (
                            "[API-ERROR] Forbidden (403) when calling "
                            "/System/Info. "
                            "Check Jellyfin permissions."
                        )
                    )
                    return False
                if status == 503:
                    last_error = (
                        "HTTP 503 Service Unavailable (server starting or "
                        "temporarily unavailable). Try again later."
                    )
                    resp = None
                elif not resp.ok:
                    snippet = (resp.text or "")[:200].replace("\n", " ")
                    last_error = f"HTTP {status} {snippet}"
                    resp = None
                else:
                    try:
                        payload = resp.json()
                    except Exception as exc:
                        snippet = (resp.text or "")[:200].replace("\n", " ")
                        self.logger.error(
                            (
                                "[API-ERROR] Failed to decode JSON from "
                                "/System/Info: "
                                "%s (%s)"
                            ),
                            exc,
                            snippet,
                        )
                        return False

                    if isinstance(payload, dict) and payload.get(
                        "IsShuttingDown"
                    ):
                        self.logger.error(
                            (
                                "[API-ERROR] Jellyfin reported that it is "
                                "shutting down; "
                                "aborting to avoid data loss."
                            )
                        )
                        return False
                    self.logger.debug("Who's there?")
                    self.logger.info("[API-TEST] Jellyfin connection OK.")
                    return True

            self.logger.error(
                "[API-ERROR] Attempt %s/%s failed for system info: %s.",
                attempt,
                attempts,
                last_error,
            )
            if attempt < attempts and backoff > 0:
                self.logger.debug("*Waiting for a response...*")
                time.sleep(backoff)
                backoff *= 2

        return False


    def list_users(
        self,
        is_disabled: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Return all users (optionally filtered by disabled flag)."""
        url = f"{self.base_url}/Users"
        params: dict[str, str] | None = None
        if is_disabled is not None:
            params = {"isDisabled": str(is_disabled).lower()}

        data = self._get_json(url, params=params, label="list users")
        if data is None:
            return []

        if not isinstance(data, list):
            self.logger.error("[API-ERROR] /Users response is not a list")
            return []

        return data


    def list_media_folders(self) -> dict[str, Any] | None:
        """Fetch all media folders via /Library/MediaFolders."""
        url = f"{self.base_url}/Library/MediaFolders"
        data = self._get_json(url, label="list media folders")
        if data is None:
            return None
        if not isinstance(data, dict):
            self.logger.error(
                "[API-ERROR] /Library/MediaFolders response is not an object"
            )
            return None
        return data


    def query_items(
        self,
        *,
        parent_id: str | None,
        include_item_types: list[str],
        enable_image_types: str | list[str],
        recursive: bool,
        start_index: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any] | None:
        """Query items within a parent folder for specific item/image types."""
        enable_types = (
            ",".join(enable_image_types)
            if isinstance(enable_image_types, list)
            else enable_image_types
        )
        params: dict[str, str] = {
            "Recursive": str(recursive).lower(),
            "EnableImageTypes": enable_types,
        }
        if parent_id:
            params["ParentId"] = parent_id
        if include_item_types:
            params["IncludeItemTypes"] = ",".join(include_item_types)
        if start_index is not None:
            params["StartIndex"] = str(start_index)
        if limit is not None:
            params["Limit"] = str(limit)

        request_label = (
            f"/Items (parent={parent_id or 'ALL'}, "
            f"image_types={enable_types}, "
            f"types={params.get('IncludeItemTypes')}, "
            f"start={start_index}, "
            f"limit={limit})"
        )
        url = f"{self.base_url}/Items"
        return self._get_json(url, params=params, label=request_label)

    def get_item(self, item_id: str) -> dict[str, Any] | None:
        """Fetch the metadata for a given item by its Jellyfin ID.

        Jellyfin returns a query-style envelope for `/Items?Ids=<id>` so this
        helper unwraps the first entry from the `Items` list.
        """
        url = f"{self.base_url}/Items"
        data = self._get_json(
            url,
            params={"Ids": item_id},
            label=f"/Items?Ids={item_id}",
        )
        if data is None:
            return None
        if isinstance(data, dict) and "Items" in data:
            items = data.get("Items")
            if isinstance(items, list) and items and isinstance(items[0], dict):
                return items[0]
            return None
        if isinstance(data, dict):
            return data
        return None


    def get_item_image(
        self,
        item_id: str,
        image_type: str,
        index: int | None = None,
    ) -> tuple[bytes, str] | None:
        """Fetch raw image bytes and content type for an item image."""
        suffix = f"/{index}" if index is not None else ""
        url = f"{self.base_url}/Items/{item_id}/Images/{image_type}{suffix}"
        resp = self._get(
            url,
            stream=True,
            label=f"item image {item_id}:{image_type}{suffix}",
        )
        if resp is None:
            return None
        content_type = resp.headers.get(
            "Content-Type", "application/octet-stream"
        )
        return resp.content, content_type


    def get_item_image_head(
        self,
        item_id: str,
        image_type: str,
        index: int | None = None,
        retry: bool = True,
    ) -> tuple[bytes, str] | None:
        """HEAD an item image and return (bytes, content-type) when present.

        Returns None when the image is missing (e.g., 404) or the request fails.
        """
        suffix = f"/{index}" if index is not None else ""
        url = f"{self.base_url}/Items/{item_id}/Images/{image_type}{suffix}"
        resp = self._head(
            url,
            stream=True,
            label=f"item image HEAD {item_id}:{image_type}{suffix}",
            allow_retry=retry,
        )
        if resp is None:
            return None
        content_type = resp.headers.get(
            "Content-Type", "application/octet-stream"
        )
        return resp.content, content_type


    def get_user_image(self, user_id: str) -> tuple[bytes, str] | None:
        """Fetch a user's profile image bytes and content type."""
        url = f"{self.base_url}/UserImage"
        resp = self._get(
            url,
            params={"userId": user_id},
            stream=True,
            label=f"profile image for {user_id}",
        )
        if resp is None:
            return None

        content_type = resp.headers.get(
            "Content-Type", "application/octet-stream"
        )
        return resp.content, content_type


    def _post_image(
        self,
        *,
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
        """Centralized POST helper used by item and user uploads."""
        if not self._writes_allowed(action_label):
            self.logger.debug(
                "DRY RUN - Would upload normalized image for %s.",
                action_label,
            )
            return True

        attempts = max(1, int(self.retry_count))
        backoff = max(0.0, float(self.backoff_base))

        last_error_msg = "Unknown error"
        payload = base64.b64encode(data) if encode_base64 else data

        for attempt in range(1, attempts + 1):
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    data=payload,
                    timeout=self.timeout,
                    verify=self.verify_tls,
                )
            except Exception as e:
                last_error_msg = f"Exception: {e}"
                resp = None
            else:
                if resp.ok:
                    if success_message.startswith("[API]"):
                        self.logger.debug(success_message)
                    else:
                        self.logger.info(success_message)
                    if self.delay > 0:
                        time.sleep(self.delay)
                    return True
                snippet = (resp.text or "")[:200].replace("\n", " ")
                last_error_msg = f"HTTP {resp.status_code} {snippet}"

            self.logger.error(
                "[API-ERROR] Attempt %s/%s failed for %s: %s",
                attempt,
                attempts,
                error_label,
                last_error_msg,
            )

            if attempt < attempts:
                time.sleep(backoff)
                backoff *= 2.0

        failure_entry["error"] = last_error_msg
        if failures is not None:
            failures.append(failure_entry)

        if self.fail_fast:
            raise RuntimeError(f"{fail_fast_prefix}: {last_error_msg}")

        return False


    def set_item_image_bytes(
        self,
        item_id: str,
        image_type: str,
        data: bytes,
        content_type: str,
        backdrop_index: int | None,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Upload an image for an item using in-memory bytes."""
        if image_type == "Backdrop" and backdrop_index is not None:
            url = (
                f"{self.base_url}/Items/{item_id}/Images/{image_type}/"
                f"{backdrop_index}"
            )
        elif image_type in ("Primary", "Thumb", "Logo"):
            url = f"{self.base_url}/Items/{item_id}/Images/{image_type}"
        else:
            raise ValueError(
                f"Unsupported image type for upload: {image_type}"
            )

        headers = {**self._headers(), "Content-Type": content_type}

        return self._post_image(
            url=url,
            headers=headers,
            data=data,
            encode_base64=True,
            success_message=(
                f"[API] Updated {image_type} image for item {item_id}"
            ),
            error_label=f"item {item_id}, type {image_type}",
            action_label=f"item {item_id} (type {image_type})",
            failures=failures,
            failure_entry={
                "item_id": item_id,
                "image_type": image_type,
                "path": None,
            },
            fail_fast_prefix=(
                f"[API] Upload failed for item {item_id} type {image_type}"
            ),
        )


    def set_item_image(
        self,
        item_id: str,
        image_type: str,
        image_path: Path,
        backdrop_index: int | None, 
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Upload an image for an item from a filesystem path."""
        try:
            with image_path.open("rb") as f:
                data = f.read()
        except Exception as e:
            msg = f"Exception reading image file {image_path}: {e}"
            self.logger.error("[API-ERROR] %s", msg)
            if failures is not None:
                failures.append(
                    {
                        "item_id": item_id,
                        "image_type": image_type,
                        "path": str(image_path),
                        "error": msg,
                    }
                )
            if self.fail_fast:
                raise
            return False

        content_type = (
            self._guess_content_type(image_path)
            or "application/octet-stream"
        )
        return self.set_item_image_bytes(
            item_id=item_id,
            image_type=image_type,
            data=data,
            content_type=content_type,
            backdrop_index=backdrop_index,
            failures=failures,
        )


    def set_user_image_bytes(
        self,
        user_id: str,
        image_type: str,
        data: bytes,
        content_type: str,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Upload an image for a user from in-memory bytes."""
        url = f"{self.base_url}/UserImage?userId={user_id}"

        headers = {**self._headers(), "Content-Type": content_type}

        return self._post_image(
            url=url,
            headers=headers,
            data=data,
            encode_base64=True,
            success_message=(
                f"[API] Updated {image_type} image for user {user_id}"
            ),
            error_label=f"user {user_id}, type {image_type}",
            action_label=f"user {user_id} (type {image_type})",
            failures=failures,
            failure_entry={
                "user_id": user_id,
                "image_type": image_type,
                "path": None,
            },
            fail_fast_prefix=(
                f"[API] Upload failed for user {user_id} type {image_type}"
            ),
        )


    def delete_image(
        self,
        uuid: str,
        image_type: str,
        image_index: int | None,
    ) -> bool:
        """Delete an image and return True only on successful HTTP response."""
        if image_type == "Primary":
            url = f"{self.base_url}/UserImage?userId={uuid}"
        elif image_type == "Backdrop":
            url = (
                f"{self.base_url}/Items/{uuid}/Images/{image_type}/"
                f"{image_index}"
            )
        else:
            raise ValueError(
                f"Unsupported image type for deletion: {image_type}"
            )
        
        headers = self._headers()

        if not self._writes_allowed(f"delete profile image for user {uuid}"):
            self.logger.debug(
                "DRY RUN - Would delete existing image for uuid %s.",
                uuid,
            )
            return True

        attempts = max(1, int(self.retry_count))
        backoff = max(0.0, float(self.backoff_base))
        last_error_msg = "Unknown error"
        for attempt in range(1, attempts + 1):
            try:
                resp = requests.delete(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_tls,
                )
            except Exception as e:
                self.logger.error(
                    "[API-ERROR] Failed to get image for uuid %s: %s",
                    uuid,
                    e,
                )
                return False
            else:
                if resp.ok:
                    self.logger.debug(
                        (
                            f"[API] Deleted image for uuid {uuid} type "
                            f"{image_type}"
                        )
                    )
                    if self.delay > 0:
                        time.sleep(self.delay)
                    return True
                snippet = (resp.text or "")[:200].replace("\n", " ")
                last_error_msg = f"HTTP {resp.status_code} {snippet}"
            
            self.logger.debug(
                "  -> Attempt %s/%s failed at deleting image for uuid %s: %s",
                attempt,
                attempts,
                uuid,
                last_error_msg,
            )
            
            if attempt < attempts:
                time.sleep(backoff)
                backoff *= 2.0
                
        if self.fail_fast:
            raise RuntimeError(
                (
                    "[API-ERROR] Deletion failed for item "
                    f"{uuid} type {image_type}: "
                    f"{last_error_msg}"
                )
            )
            
        return False


    def set_user_profile_image(
        self,
        user_id: str,
        data: bytes,
        content_type: str,
        failures: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Replace a user's profile image (delete existing then upload)."""
        url = f"{self.base_url}/UserImage?userId={user_id}"
        headers = {**self._headers(), "Content-Type": content_type}

        if not self.delete_image(user_id, "Primary", None):
            failure_entry = {
                "user_id": user_id,
                "image_type": "Primary",
                "path": None,
                "error": (
                    "Failed to delete existing profile image before upload"
                ),
            }
            if failures is not None:
                failures.append(failure_entry)
            if self.fail_fast:
                raise RuntimeError(
                    (
                        f"API delete failed for user {user_id} profile image; "
                        "aborting upload"
                    )
                )
            return False

        return self._post_image(
            url=url,
            headers=headers,
            data=data,
            encode_base64=True,
            success_message=f"[API] Updated profile image for user {user_id}",
            error_label=f"user {user_id} profile",
            action_label=f"user {user_id} (profile image)",
            failures=failures,
            failure_entry={
                "user_id": user_id,
                "image_type": "Primary",
                "path": None,
            },
            fail_fast_prefix=(
                f"[API] Upload failed for user {user_id} profile image"
            ),
        )
