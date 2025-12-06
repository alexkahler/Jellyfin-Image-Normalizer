from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from . import state
from .config import DiscoverySettings
from .constants import ALLOWED_COLLECTION_TYPES, DEFAULT_DISCOVERY_PAGE_SIZE


@dataclass
class LibraryRef:
    """Lightweight reference to a Jellyfin library discovered for the operator."""

    id: str
    name: str
    collection_type: str | None


@dataclass
class DiscoveredItem:
    """Container for items discovered with desired image types."""

    id: str
    name: str
    type: str
    parent_id: str | None
    library_id: str | None
    library_name: str | None
    image_types: set[str] = field(default_factory=set)

    def add_image_type(self, image_type: str) -> None:
        """Mark that this item has a given image type tag."""
        self.image_types.add(image_type)


def _normalize_library_name(text: str) -> str:
    """Strip emoji/punctuation and case-fold to normalize names like 'dY?z | Crispyroll'."""
    lowered = text.casefold()
    return re.sub(r"[^a-z0-9]+", "", lowered)


def resolve_operator_user(jf_client: Any, discovery: DiscoverySettings) -> dict[str, Any]:
    """Resolve the operator user via username or default to first active."""
    users = jf_client.list_users(is_disabled=False)
    if not users:
        state.log.critical("No active users returned from Jellyfin; cannot continue.")
        state.stats.record_error("discovery", "No active users returned from Jellyfin")
        raise SystemExit(1)

    if discovery.operator.username:
        user = find_user_by_name(users, discovery.operator.username)
        if user:
            return user
        state.log.critical(
            "Configured operator username '%s' not found among active users.",
            discovery.operator.username,
        )
        state.stats.record_error("discovery", "Configured operator username not found")
        raise SystemExit(1)

    state.log.info("Operator not specified; defaulting to first active user from /Users.")
    return users[0]


def discover_libraries(
    jf_client: Any,
    user_id: str,
    discovery: DiscoverySettings,
) -> list[LibraryRef]:
    """List libraries for the operator and filter by allowed collection types/names."""
    resp = jf_client.get_user_items(user_id)
    if not resp or "Items" not in resp:
        state.log.critical("Could not list libraries for user %s.", user_id)
        state.stats.record_error("discovery", "Failed to list libraries")
        raise SystemExit(1)

    items = resp.get("Items") or []

    names_filter = {_normalize_library_name(name) for name in discovery.library_names}
    if discovery.library_names:
        state.log.info(
            "Library filter configured: raw=%s normalized=%s",
            discovery.library_names,
            sorted(names_filter),
        )

    allowed_types = set(ALLOWED_COLLECTION_TYPES)
    libraries: list[LibraryRef] = []
    for item in items:
        lib_id = item.get("Id")
        if not lib_id:
            continue
        name = item.get("Name") or "<unknown>"
        collection_type_raw = item.get("CollectionType")
        collection_type = collection_type_raw.lower() if collection_type_raw else None

        if names_filter and _normalize_library_name(name) not in names_filter:
            continue
        if collection_type and collection_type not in allowed_types:
            continue

        libraries.append(
            LibraryRef(
                id=lib_id,
                name=name,
                collection_type=collection_type,
            )
        )

    if discovery.library_names and not libraries:
        state.log.critical(
            "Library filters present (%s) but none matched active libraries.",
            ", ".join(discovery.library_names),
        )
        state.stats.record_error("discovery", "Library filters did not match any library")
        raise SystemExit(1)

    if names_filter:
        state.log.info(
            "Library filter active; selected %s/%s libraries: %s",
            len(libraries),
            len(items),
            ", ".join(lib.name for lib in libraries),
        )

    state.log.info(
        "Discovered %s libraries for user %s.",
        len(libraries),
        user_id,
    )
    return libraries


def _item_has_image_type(item: dict[str, Any], image_type: str) -> bool:
    image_tags = item.get("ImageTags") or {}
    return image_type in image_tags


def discover_library_items(
    jf_client: Any,
    user_id: str,
    library: LibraryRef,
    discovery: DiscoverySettings,
) -> list[DiscoveredItem]:
    """Discover items inside a library that have any of the requested image types."""
    items: dict[str, DiscoveredItem] = {}
    enabled_types = list(discovery.enable_image_types)
    if not enabled_types:
        state.log.info("No image types requested for library %s; skipping.", library.name)
        return []

    page_size = DEFAULT_DISCOVERY_PAGE_SIZE
    start_index = 0
    total_records: int | None = None
    state.log.info(
        "Scanning library '%s' for image types %s (page_size=%s)",
        library.name,
        ",".join(enabled_types),
        page_size,
    )

    while True:
        resp = jf_client.query_library_items(
            user_id=user_id,
            parent_id=library.id,
            include_item_types=discovery.include_item_types,
            enable_image_types=",".join(enabled_types),
            recursive=discovery.recursive,
            image_type_limit=discovery.image_type_limit,
            start_index=start_index,
            limit=page_size,
        )

        if resp is None:
            state.stats.record_error(
                library.name,
                f"Failed to query items for image types {enabled_types} (page start {start_index})",
            )
            break

        raw_items = resp.get("Items") or []
        for raw in raw_items:
            item_id = raw.get("Id")
            if not item_id:
                continue

            matching_types = [it for it in enabled_types if _item_has_image_type(raw, it)]
            if not matching_types:
                continue

            if item_id not in items:
                items[item_id] = DiscoveredItem(
                    id=item_id,
                    name=raw.get("Name") or "<unknown>",
                    type=raw.get("Type") or "Unknown",
                    parent_id=raw.get("ParentId"),
                    library_id=library.id,
                    library_name=library.name,
                )
            for image_type in matching_types:
                items[item_id].add_image_type(image_type)

        state.log.info(
            "Library '%s': fetched %s items (start=%s), unique with target images so far: %s",
            library.name,
            len(raw_items),
            start_index,
            len(items),
        )

        if not raw_items:
            break

        total_records = resp.get("TotalRecordCount", total_records)
        start_index += len(raw_items)

        if total_records is not None:
            if start_index >= total_records:
                break
        else:
            if len(raw_items) < page_size:
                break

    state.log.info(
        "Library '%s': %s items with target images.",
        library.name,
        len(items),
    )
    return list(items.values())


def discover_all_library_items(
    jf_client: Any,
    user_id: str,
    libraries: list[LibraryRef],
    discovery: DiscoverySettings,
) -> list[DiscoveredItem]:
    """Aggregate discovered items across all selected libraries."""
    all_items: list[DiscoveredItem] = []
    for library in libraries:
        library_items = discover_library_items(jf_client, user_id, library, discovery)
        all_items.extend(library_items)
    return all_items


def profile_display_name(user: dict[str, Any]) -> str:
    """Human-readable label for a user including name and id."""
    name = user.get("Name") or "<unknown>"
    user_id = user.get("Id") or "?"
    return f"{name} ({user_id})"


def find_user_by_name(users: Iterable[dict[str, Any]], username: str) -> dict[str, Any] | None:
    """Locate a user by Name (case-insensitive) from a user list."""
    username_lower = username.lower()
    for user in users:
        name = (user.get("Name") or "").lower()
        if name == username_lower:
            return user
    return None
