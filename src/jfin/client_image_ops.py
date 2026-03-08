from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import JellyfinClient


def _item_image_upload_url(
    client: JellyfinClient, item_id: str, image_type: str, backdrop_index: int | None
) -> str:
    if image_type == "Backdrop" and backdrop_index is not None:
        return f"{client.base_url}/Items/{item_id}/Images/{image_type}/{backdrop_index}"
    if image_type in ("Primary", "Thumb", "Logo"):
        return f"{client.base_url}/Items/{item_id}/Images/{image_type}"
    raise ValueError(f"Unsupported image type for upload: {image_type}")


def get_item_image(
    client: JellyfinClient,
    item_id: str,
    image_type: str,
    index: int | None = None,
) -> tuple[bytes, str] | None:
    suffix = f"/{index}" if index is not None else ""
    resp = client._get(
        f"{client.base_url}/Items/{item_id}/Images/{image_type}{suffix}",
        stream=True,
        label=f"item image {item_id}:{image_type}{suffix}",
    )
    if resp is None:
        return None
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


def get_item_image_head(
    client: JellyfinClient,
    item_id: str,
    image_type: str,
    index: int | None = None,
    retry: bool = True,
) -> tuple[bytes, str] | None:
    suffix = f"/{index}" if index is not None else ""
    resp = client._head(
        f"{client.base_url}/Items/{item_id}/Images/{image_type}{suffix}",
        stream=True,
        label=f"item image HEAD {item_id}:{image_type}{suffix}",
        allow_retry=retry,
    )
    if resp is None:
        return None
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


def get_user_image(client: JellyfinClient, user_id: str) -> tuple[bytes, str] | None:
    resp = client._get(
        f"{client.base_url}/UserImage",
        params={"userId": user_id},
        stream=True,
        label=f"profile image for {user_id}",
    )
    if resp is None:
        return None
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


def query_items(
    client: JellyfinClient,
    *,
    parent_id: str | None,
    include_item_types: list[str],
    enable_image_types: str | list[str],
    recursive: bool,
    start_index: int | None = None,
    limit: int | None = None,
) -> dict[str, Any] | None:
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
        f"/Items (parent={parent_id or 'ALL'}, image_types={enable_types}, "
        f"types={params.get('IncludeItemTypes')}, start={start_index}, limit={limit})"
    )
    return client._get_json(
        f"{client.base_url}/Items", params=params, label=request_label
    )


def get_item(client: JellyfinClient, item_id: str) -> dict[str, Any] | None:
    data = client._get_json(
        f"{client.base_url}/Items",
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


def set_item_image_bytes(
    client: JellyfinClient,
    item_id: str,
    image_type: str,
    data: bytes,
    content_type: str,
    backdrop_index: int | None,
    failures: list[dict[str, Any]] | None = None,
) -> bool:
    url = _item_image_upload_url(client, item_id, image_type, backdrop_index)
    return client._post_image(
        url=url,
        headers={**client._headers(), "Content-Type": content_type},
        data=data,
        encode_base64=True,
        success_message=f"[API] Updated {image_type} image for item {item_id}",
        error_label=f"item {item_id}, type {image_type}",
        action_label=f"item {item_id} (type {image_type})",
        failures=failures,
        failure_entry={"item_id": item_id, "image_type": image_type, "path": None},
        fail_fast_prefix=f"[API] Upload failed for item {item_id} type {image_type}",
    )


def set_item_image(
    client: JellyfinClient,
    item_id: str,
    image_type: str,
    image_path: Path,
    backdrop_index: int | None,
    failures: list[dict[str, Any]] | None = None,
) -> bool:
    try:
        with image_path.open("rb") as f:
            data = f.read()
    except Exception as exc:
        msg = f"Exception reading image file {image_path}: {exc}"
        client.logger.error("[API-ERROR] %s", msg)
        if failures is not None:
            failures.append(
                {
                    "item_id": item_id,
                    "image_type": image_type,
                    "path": str(image_path),
                    "error": msg,
                }
            )
        if client.fail_fast:
            raise
        return False
    content_type = client._guess_content_type(image_path) or "application/octet-stream"
    return set_item_image_bytes(
        client,
        item_id=item_id,
        image_type=image_type,
        data=data,
        content_type=content_type,
        backdrop_index=backdrop_index,
        failures=failures,
    )


def set_user_image_bytes(
    client: JellyfinClient,
    user_id: str,
    image_type: str,
    data: bytes,
    content_type: str,
    failures: list[dict[str, Any]] | None = None,
) -> bool:
    return client._post_image(
        url=f"{client.base_url}/UserImage?userId={user_id}",
        headers={**client._headers(), "Content-Type": content_type},
        data=data,
        encode_base64=True,
        success_message=f"[API] Updated {image_type} image for user {user_id}",
        error_label=f"user {user_id}, type {image_type}",
        action_label=f"user {user_id} (type {image_type})",
        failures=failures,
        failure_entry={"user_id": user_id, "image_type": image_type, "path": None},
        fail_fast_prefix=f"[API] Upload failed for user {user_id} type {image_type}",
    )


def set_user_profile_image(
    client: JellyfinClient,
    user_id: str,
    data: bytes,
    content_type: str,
    failures: list[dict[str, Any]] | None = None,
) -> bool:
    if not client.delete_image(user_id, "Primary", None):
        failure_entry = {
            "user_id": user_id,
            "image_type": "Primary",
            "path": None,
            "error": "Failed to delete existing profile image before upload",
        }
        if failures is not None:
            failures.append(failure_entry)
        if client.fail_fast:
            raise RuntimeError(
                f"API delete failed for user {user_id} profile image; aborting upload"
            )
        return False
    return client._post_image(
        url=f"{client.base_url}/UserImage?userId={user_id}",
        headers={**client._headers(), "Content-Type": content_type},
        data=data,
        encode_base64=True,
        success_message=f"[API] Updated profile image for user {user_id}",
        error_label=f"user {user_id} profile",
        action_label=f"user {user_id} (profile image)",
        failures=failures,
        failure_entry={"user_id": user_id, "image_type": "Primary", "path": None},
        fail_fast_prefix=f"[API] Upload failed for user {user_id} profile image",
    )
