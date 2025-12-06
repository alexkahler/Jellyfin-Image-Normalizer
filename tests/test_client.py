import base64

import requests

import pytest

from jfin_core.client import JellyfinClient


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


def test_query_library_items_builds_expected_params(monkeypatch):
    captured = {}

    def fake_get_user_items(user_id, params=None, label=None):
        captured["user_id"] = user_id
        captured["params"] = params
        return {}

    client = JellyfinClient(base_url="http://example", api_key="token")
    monkeypatch.setattr(client, "get_user_items", fake_get_user_items)

    client.query_library_items(
        "user123",
        parent_id="parent",
        include_item_types=["Movie", "Series"],
        enable_image_types="Logo",
        recursive=True,
        image_type_limit=1,
    )

    assert captured["user_id"] == "user123"
    assert captured["params"] == {
        "ParentId": "parent",
        "IncludeItemTypes": "Movie,Series",
        "Recursive": "true",
        "ImageTypeLimit": 1,
        "EnableImageTypes": "Logo",
    }


def test_query_library_items_accepts_list(monkeypatch):
    captured = {}

    def fake_get_user_items(user_id, params=None, label=None):
        captured["params"] = params
        return {}

    client = JellyfinClient(base_url="http://example", api_key="token")
    monkeypatch.setattr(client, "get_user_items", fake_get_user_items)

    client.query_library_items(
        "user123",
        parent_id="parent",
        include_item_types=["Movie", "Series"],
        enable_image_types=["Logo", "Thumb"],
        recursive=True,
        image_type_limit=1,
    )

    assert captured["params"]["EnableImageTypes"] == "Logo,Thumb"


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

    result = client.set_item_image_bytes("item1", "Logo", b"abc", "image/png")
    assert result is True
    assert posted["url"].endswith("/Items/item1/Images/Logo")
    assert posted["headers"]["Content-Type"] == "image/png"
    assert posted["data"] == base64.b64encode(b"abc")


def test_dry_run_blocks_post(monkeypatch):
    def fake_post(*args, **kwargs):
        raise AssertionError("post should not be called in dry-run")

    monkeypatch.setattr(requests, "post", fake_post)
    client = JellyfinClient(base_url="http://example", api_key="token", dry_run=True)
    assert client.set_item_image_bytes("item1", "Logo", b"abc", "image/png") is True


def test_writes_allowed_without_extra_flag(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: FakeResponse(status_code=200))
    client = JellyfinClient(base_url="http://example", api_key="token", dry_run=False)
    assert client.set_item_image_bytes("item1", "Logo", b"abc", "image/png") is True


def test_delete_user_profile_image_dry_run(monkeypatch):
    def fake_delete(*args, **kwargs):
        raise AssertionError("delete should not be called in dry-run")

    monkeypatch.setattr(requests, "delete", fake_delete)
    client = JellyfinClient(base_url="http://example", api_key="token", dry_run=True)
    assert client.delete_user_profile_image("user1") is True


def test_delete_user_profile_image_treats_404_as_success(monkeypatch):
    def fake_delete(*args, **kwargs):
        return FakeResponse(status_code=404)

    monkeypatch.setattr(requests, "delete", fake_delete)
    client = JellyfinClient(base_url="http://example", api_key="token", dry_run=False)
    assert client.delete_user_profile_image("user123") is True


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
