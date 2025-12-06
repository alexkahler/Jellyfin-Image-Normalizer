import pytest

from jfin_core.config import DiscoverySettings, OperatorSpec
from jfin_core.discovery import discover_libraries, discover_library_items, LibraryRef


class FakeClient:
    def __init__(self, items):
        self.items = items

    def get_user_items(self, user_id):
        return {"Items": self.items}


def test_discover_libraries_filters_names():
    client = FakeClient(
        [
            {"Id": "1", "Name": "🍿 | Movies", "CollectionType": "movies"},
            {"Id": "2", "Name": "🍞 | Crispyroll", "CollectionType": "tvshows"},
            {"Id": "3", "Name": "🎥|crispyROLL", "CollectionType": "tvshows"},
        ]
    )
    discovery = DiscoverySettings(
        operator=OperatorSpec(username=None),
        library_names=["Crispyroll"],
        include_item_types=[],
        enable_image_types=[],
        recursive=True,
        image_type_limit=1,
    )

    libs = discover_libraries(client, "user", discovery)
    assert len(libs) == 2
    assert {lib.id for lib in libs} == {"2", "3"}
    assert all("crispyroll" in lib.name.casefold() for lib in libs)


def test_discover_libraries_raises_if_filters_match_none():
    client = FakeClient([{"Id": "1", "Name": "Movies", "CollectionType": "movies"}])
    discovery = DiscoverySettings(
        operator=OperatorSpec(username=None),
        library_names=["Crispyroll"],
        include_item_types=[],
        enable_image_types=[],
        recursive=True,
        image_type_limit=1,
    )
    with pytest.raises(SystemExit):
        discover_libraries(client, "user", discovery)


def test_discover_libraries_skips_unsupported_collection_types():
    client = FakeClient(
        [
            {"Id": "1", "Name": "Movies", "CollectionType": "movies"},
            {"Id": "2", "Name": "Photos", "CollectionType": "photos"},
        ]
    )
    discovery = DiscoverySettings(
        operator=OperatorSpec(username=None),
        library_names=[],
        include_item_types=[],
        enable_image_types=[],
        recursive=True,
        image_type_limit=1,
    )
    libs = discover_libraries(client, "user", discovery)
    assert [lib.id for lib in libs] == ["1"]


def test_discover_library_items_paginates():
    pages = [
        {
            "Items": [
                {"Id": "1", "Name": "One", "Type": "Movie", "ParentId": "lib", "ImageTags": {"Thumb": "a"}}
            ],
            "TotalRecordCount": 2,
        },
        {
            "Items": [
                {"Id": "2", "Name": "Two", "Type": "Movie", "ParentId": "lib", "ImageTags": {"Thumb": "b"}}
            ],
            "TotalRecordCount": 2,
        },
    ]

    class PagingClient:
        def __init__(self, pages):
            self.pages = pages
            self.calls = 0

        def query_library_items(
            self,
            user_id,
            parent_id,
            include_item_types,
            enable_image_types,
            recursive,
            image_type_limit,
            start_index=None,
            limit=None,
        ):
            idx = self.calls
            self.calls += 1
            if idx < len(self.pages):
                return self.pages[idx]
            return {"Items": [], "TotalRecordCount": 2}

    discovery = DiscoverySettings(
        operator=OperatorSpec(username=None),
        library_names=[],
        include_item_types=["Movie"],
        enable_image_types=["Thumb"],
        recursive=True,
        image_type_limit=1,
    )
    library = LibraryRef(id="lib", name="Lib", collection_type="tvshows")
    client = PagingClient(pages)

    items = discover_library_items(client, "user", library, discovery)
    assert {item.id for item in items} == {"1", "2"}
    assert client.calls == 2
