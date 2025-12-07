import pytest

from jfin_core.config import DiscoverySettings
from jfin_core.discovery import (
    LibraryRef,
    discover_all_library_items,
    discover_libraries,
    discover_library_items,
)


class FakeClient:
    def __init__(self, items):
        self.items = items

    def list_media_folders(self):
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
        library_names=["Crispyroll"],
        include_item_types=[],
        enable_image_types=[],
        recursive=True,
        image_type_limit=1,
    )

    libs = discover_libraries(client, discovery)
    assert len(libs) == 2
    assert {lib.id for lib in libs} == {"2", "3"}
    assert all("crispyroll" in lib.name.casefold() for lib in libs)


def test_discover_libraries_raises_if_filters_match_none():
    client = FakeClient([{"Id": "1", "Name": "Movies", "CollectionType": "movies"}])
    discovery = DiscoverySettings(
        library_names=["Crispyroll"],
        include_item_types=[],
        enable_image_types=[],
        recursive=True,
        image_type_limit=1,
    )
    with pytest.raises(SystemExit):
        discover_libraries(client, discovery)


def test_discover_libraries_skips_unsupported_collection_types():
    class Client:
        def __init__(self):
            self.called = False

        def list_media_folders(self):
            self.called = True
            raise AssertionError("should not call media folder listing")

    discovery = DiscoverySettings(
        library_names=[],
        include_item_types=[],
        enable_image_types=[],
        recursive=True,
        image_type_limit=1,
    )
    client = Client()

    libs = discover_libraries(client, discovery)
    assert libs == []
    assert client.called is False


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

        def query_items(
            self,
            *,
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
            self.last_call = {
                "parent_id": parent_id,
                "include_item_types": include_item_types,
                "enable_image_types": enable_image_types,
                "recursive": recursive,
            }
            if idx < len(self.pages):
                return self.pages[idx]
            return {"Items": [], "TotalRecordCount": 2}

    discovery = DiscoverySettings(
        library_names=[],
        include_item_types=["Movie"],
        enable_image_types=["Thumb"],
        recursive=True,
        image_type_limit=1,
    )
    library = LibraryRef(id="lib", name="Lib", collection_type="tvshows")
    client = PagingClient(pages)

    items = discover_library_items(client, library, discovery)
    assert {item.id for item in items} == {"1", "2"}
    assert client.calls == 2
    assert client.last_call["parent_id"] == "lib"
    assert client.last_call["include_item_types"] == ["Movie"]
    assert client.last_call["enable_image_types"] == "Thumb"
    assert client.last_call["recursive"] is True


def test_discover_library_items_maps_image_types():
    response = {
        "Items": [
            {
                "Id": "1",
                "Name": "One",
                "Type": "Movie",
                "ParentId": "lib",
                "ImageTags": {"Logo": "l1", "Thumb": "t1"},
            },
            {
                "Id": "2",
                "Name": "Two",
                "Type": "Series",
                "ParentId": "lib",
                "ImageTags": {"Thumb": "t2"},
            },
        ],
        "TotalRecordCount": 2,
    }

    class Client:
        def __init__(self, resp):
            self.resp = resp
            self.calls = 0

        def query_items(
            self,
            *,
            parent_id,
            include_item_types,
            enable_image_types,
            recursive,
            image_type_limit,
            start_index=None,
            limit=None,
        ):
            self.calls += 1
            return self.resp

    discovery = DiscoverySettings(
        library_names=[],
        include_item_types=["Movie", "Series"],
        enable_image_types=["Logo", "Thumb"],
        recursive=True,
        image_type_limit=1,
    )
    library = LibraryRef(id="lib", name="Lib", collection_type=None)
    client = Client(response)

    items = discover_library_items(client, library, discovery)
    assert len(items) == 2
    item_map = {item.id: item for item in items}
    assert item_map["1"].image_types == {"Logo", "Thumb"}
    assert item_map["2"].image_types == {"Thumb"}
    assert client.calls == 1


def test_discover_items_without_library_filters_queries_all_items():
    class Client:
        def __init__(self):
            self.calls = 0
            self.parent_ids = []

        def query_items(
            self,
            *,
            parent_id,
            include_item_types,
            enable_image_types,
            recursive,
            image_type_limit,
            start_index=None,
            limit=None,
        ):
            self.calls += 1
            self.parent_ids.append(parent_id)
            return {
                "Items": [
                    {
                        "Id": "1",
                        "Name": "Movie",
                        "Type": "Movie",
                        "ImageTags": {"Logo": "a"},
                    }
                ],
                "TotalRecordCount": 1,
            }

    discovery = DiscoverySettings(
        library_names=[],
        include_item_types=["Movie"],
        enable_image_types=["Logo"],
        recursive=True,
        image_type_limit=1,
    )
    client = Client()

    items = discover_all_library_items(client, None, discovery)
    assert {item.id for item in items} == {"1"}
    assert client.calls == 1
    assert client.parent_ids == [None]


def test_discover_libraries_and_items_apply_nested_filters():
    class Client:
        def __init__(self):
            self.media_calls = 0
            self.query_args: list[tuple] = []

        def list_media_folders(self):
            self.media_calls += 1
            return {
                "Items": [
                    {"Id": "lib1", "Name": "Movies"},
                    {"Id": "lib2", "Name": "TV"},
                ]
            }

        def query_items(
            self,
            *,
            parent_id,
            include_item_types,
            enable_image_types,
            recursive,
            image_type_limit,
            start_index=None,
            limit=None,
        ):
            self.query_args.append((parent_id, include_item_types, enable_image_types))
            return {"Items": [], "TotalRecordCount": 0}

    discovery = DiscoverySettings(
        library_names=["Movies"],
        include_item_types=["Series"],
        enable_image_types=["Thumb"],
        recursive=True,
        image_type_limit=1,
    )
    client = Client()

    libs = discover_libraries(client, discovery)
    assert [lib.id for lib in libs] == ["lib1"]

    discover_all_library_items(client, libs, discovery)
    assert client.media_calls == 1
    assert client.query_args == [("lib1", ["Series"], "Thumb")]
