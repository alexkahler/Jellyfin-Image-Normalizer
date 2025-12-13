import base64
import requests
import pytest
from jfin_core.client import JellyfinClient
from unittest.mock import Mock

class FakeResponse:
    def __init__(self, status_code=200, content=b"", headers=None, text=""):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.text = text

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return {}


def test_query_items_builds_expected_params(monkeypatch):
    captured = {}

    def fake_get_json(url, params=None, label=None):
        captured["url"] = url
        captured["params"] = params
        captured["label"] = label
        return {}

    client = JellyfinClient(base_url="http://example", api_key="token")
    monkeypatch.setattr(client, "_get_json", fake_get_json)

    client.query_items(
        parent_id="parent",
        include_item_types=["Movie", "Series"],
        enable_image_types="Logo",
        recursive=True,
        start_index=5,
        limit=10,
    )

    assert captured["url"].endswith("/Items")
    assert captured["params"] == {
        "ParentId": "parent",
        "Recursive": "true",
        "IncludeItemTypes": "Movie,Series",
        "EnableImageTypes": "Logo",
        "StartIndex": "5",
        "Limit": "10",
    }


def test_query_items_accepts_list(monkeypatch):
    captured = {}

    def fake_get_json(url, params=None, label=None):
        captured["params"] = params
        return {}

    client = JellyfinClient(base_url="http://example", api_key="token")
    monkeypatch.setattr(client, "_get_json", fake_get_json)

    client.query_items(
        parent_id="parent",
        include_item_types=["Movie"],
        enable_image_types=["Logo", "Thumb", "Backdrop"],
        recursive=False,
    )

    assert captured["params"]["EnableImageTypes"] == "Logo,Thumb,Backdrop"
    assert captured["params"]["Recursive"] == "false"
    assert captured["params"]["IncludeItemTypes"] == "Movie"


def test_get_item_uses_ids_query_and_unwraps(monkeypatch):
    captured = {}

    def fake_get_json(url, params=None, label=None):
        captured["url"] = url
        captured["params"] = params
        captured["label"] = label
        return {
            "Items": [
                {"Id": "item123", "Name": "Demo", "BackdropImageTags": ["a", "b"]}
            ],
            "TotalRecordCount": 1,
            "StartIndex": 0,
        }

    client = JellyfinClient(base_url="http://example", api_key="token")
    monkeypatch.setattr(client, "_get_json", fake_get_json)

    item = client.get_item("item123")

    assert captured["url"].endswith("/Items")
    assert captured["params"] == {"Ids": "item123"}
    assert isinstance(item, dict)
    assert item["Id"] == "item123"


def test_post_image_base64_payload(monkeypatch):
    posted = {}

    def fake_post(url, headers=None, data=None, timeout=None, verify=None):
        posted["url"] = url
        posted["headers"] = headers
        posted["data"] = data
        return FakeResponse(status_code=200)

    monkeypatch.setattr(requests, "post", fake_post)

    client = JellyfinClient(
        base_url="http://example",
        api_key="token",
        dry_run=False,
        retry_count=1,
    )

    result = client.set_item_image_bytes("item1", "Logo", b"abc", "image/png", None)
    assert result is True
    assert posted["url"].endswith("/Items/item1/Images/Logo")
    assert posted["headers"]["Content-Type"] == "image/png"
    assert posted["data"] == base64.b64encode(b"abc")


def test_dry_run_blocks_post(monkeypatch):
    def fake_post(*args, **kwargs):
        raise AssertionError("post should not be called in dry-run")

    monkeypatch.setattr(requests, "post", fake_post)
    client = JellyfinClient(base_url="http://example", api_key="token", dry_run=True)
    assert client.set_item_image_bytes("item1", "Logo", b"abc", "image/png", None) is True


def test_writes_allowed_without_extra_flag(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: FakeResponse(status_code=200))
    client = JellyfinClient(base_url="http://example", api_key="token", dry_run=False)
    assert client.set_item_image_bytes("item1", "Logo", b"abc", "image/png", None) is True


@pytest.mark.parametrize(
    "image_type, backdrop_index, writes_allowed, status_code, ok, expected_url_suffix, expected_result, expect_delete_called",
    [
        # Dry-run primary: no HTTP call, but still returns True
        ("Primary", None, False, None, None, "/UserImage?userId=testuuid", True, False),

        # Primary: 204 OK => True
        ("Primary", None, True, 204, True, "/UserImage?userId=testuuid", True, True),

        # Primary: 404 treated as failed => True
        ("Primary", None, True, 404, False, "/UserImage?userId=testuuid", False, True),

        # Primary: 500, not ok => False
        ("Primary", None, True, 500, False, "/UserImage?userId=testuuid", False, True),

        # Backdrop index 0: 204 OK => True
        ("Backdrop", 0, True, 204, True, "/Items/testuuid/Images/Backdrop/0", True, True),

        # Backdrop index 3: 204 treated as success => True
        ("Backdrop", 3, True, 204, True, "/Items/testuuid/Images/Backdrop/3", True, True),
    ],
)
def test_delete_image_parametrized(
    monkeypatch,
    image_type,
    backdrop_index,
    writes_allowed,
    status_code,
    ok,
    expected_url_suffix,
    expected_result,
    expect_delete_called,
):
    # Arrange: minimal client instance
    client = JellyfinClient(base_url="http://example", api_key="token")
    client.timeout = 5
    client.verify_tls = True
    client.logger = Mock()

    # stub headers + writes_allowed
    monkeypatch.setattr(client, "_headers", lambda: {"Authorization": "Token"}, raising=False)
    monkeypatch.setattr(
        client,
        "_writes_allowed",
        lambda msg: writes_allowed,
        raising=False,
    )

    # mock requests.delete
    mock_delete = Mock()
    if expect_delete_called:
        resp = Mock()
        resp.status_code = status_code
        resp.ok = ok
        # some body text to exercise snippet logic on error
        resp.text = "some error body"
        mock_delete.return_value = resp

    monkeypatch.setattr(requests, "delete", mock_delete)

    # Act
    result = client.delete_image("testuuid", image_type, backdrop_index)

    # Assert: return value
    assert result is expected_result

    # Assert: HTTP call behavior
    assert mock_delete.called is expect_delete_called
    if expect_delete_called:
        if ok:
            assert mock_delete.call_count == 1
        else:
            assert mock_delete.call_count == client.retry_count
        
        
            
        first_call = mock_delete.call_args_list[0]
        called_url = first_call.args[0]
        called_headers = mock_delete.call_args.kwargs["headers"]
            
        assert called_url == client.base_url + expected_url_suffix
        assert called_headers == {"Authorization": "Token"}


def test_delete_image_unsupported_type_raises(monkeypatch):
    client = JellyfinClient(base_url="http://example", api_key="token")
    client.logger = Mock()

    with pytest.raises(ValueError, match="Unsupported image type"):
        client.delete_image("testuuid", "Banner", None)



def test_get_item_image_returns_content_type(monkeypatch):
    def fake_get(url, headers=None, params=None, timeout=None, verify=None, stream=None):
        return FakeResponse(
            status_code=200,
            content=b"payload",
            headers={"Content-Type": "image/png"},
        )

    monkeypatch.setattr(requests, "get", fake_get)
    client = JellyfinClient(base_url="http://example", api_key="token")
    data = client.get_item_image("abc", "Logo")
    assert data == (b"payload", "image/png")


def test_get_item_image_head_404_returns_none(monkeypatch):
    def fake_head(url, headers=None, params=None, timeout=None, verify=None, stream=None):
        return FakeResponse(
            status_code=404,
            content=b"",
            headers={"Content-Type": "image/jpeg"},
            text="not found",
        )

    monkeypatch.setattr(requests, "head", fake_head)
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)

    client = JellyfinClient(base_url="http://example", api_key="token", retry_count=1, dry_run=False)
    resp = client.get_item_image_head("abc", "Backdrop", index=0)
    assert resp is None


def test_get_retries_on_failure(monkeypatch):
    calls = {"count": 0}

    def fake_get(url, headers=None, params=None, timeout=None, verify=None, stream=None):
        calls["count"] += 1
        if calls["count"] == 1:
            raise requests.exceptions.Timeout("boom")
        return FakeResponse(status_code=200, content=b"ok")

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)

    client = JellyfinClient(base_url="http://example", api_key="token", retry_count=2, backoff_base=0.1)
    resp = client.get_item_image("abc", "Logo")
    assert resp == (b"ok", "application/octet-stream")
    assert calls["count"] == 2
