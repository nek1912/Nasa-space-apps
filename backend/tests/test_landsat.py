"""Offline tests for the USGS M2M API client (no network)."""

from typing import Any

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.landsat import M2M_BASE, M2MClient, M2MError


class _FakeResponse:
    def __init__(self, status_code: int, json_data: dict, text: str = "{}"):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error", request=MagicMock(), response=MagicMock()
            )

    def json(self) -> dict:
        return self._json


def _make_client(monkeypatch: pytest.MonkeyPatch) -> M2MClient:
    client = M2MClient("test_user", "test_token_64chars....................")
    # Patch httpx.Client.post to avoid real network calls.
    orig_post = client._client.post

    def fake_post(url: str, **kwargs: Any) -> _FakeResponse:
        path = url.replace(M2M_BASE, "")
        if path == "login-token":
            return _FakeResponse(200, {"apiKey": "test_api_key_1234567890abcdef"})
        if path == "scene-search":
            return _FakeResponse(
                200,
                {
                    "data": [
                        {
                            "entityId": "LC09_L2SP_027031_20250615_20250626_02_T2",
                            "displayId": "LC09_L2SP_027031_20250615_20250626_02_T2",
                            "cloudCover": 5.2,
                            "acquisitionDate": "2025-06-15",
                        }
                    ],
                    "recordsReturned": 1,
                    "totalRecords": 1,
                },
            )
        if path == "download-options":
            return _FakeResponse(
                200,
                {
                    "data": [
                        {
                            "entityId": "LC09_L2SP_027031_20250615_20250626_02_T2",
                            "downloadOptions": [
                                {
                                    "id": "...-SR_B4",
                                    "name": "SR_B4",
                                    "size": 45000000,
                                    "available": True,
                                }
                            ],
                        }
                    ]
                },
            )
        if path == "download-request":
            return _FakeResponse(200, {"downloadRequestId": "req_12345"})
        if path == "download-retrieve":
            return _FakeResponse(
                200,
                {
                    "data": [
                        {
                            "entityId": "LC09_L2SP_027031_20250615_20250626_02_T2",
                            "url": "https://example.com/download/scene.tar.gz",
                            "filename": "LC09_L2SP_027031_20250615_20250626_02_T2.tar.gz",
                            "available": True,
                        }
                    ]
                },
            )
        if path == "logout":
            return _FakeResponse(200, {})
        return _FakeResponse(404, {}, "not found")

    client._client.post = fake_post  # type: ignore[method-assign]
    return client


def test_login_stores_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(monkeypatch)
    key = client.login()
    assert key == "test_api_key_1234567890abcdef"
    assert client.api_key == "test_api_key_1234567890abcdef"


def test_search_scenes_returns_scene_list(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(monkeypatch)
    client.login()
    scenes = client.search_scenes(
        dataset_name="landsat_ot_c2_l2",
        start_date="2025-04-01",
        end_date="2025-10-31",
        bbox=[-93.8, 41.8, -93.3, 42.3],
        max_cloud=20,
    )
    assert len(scenes) == 1
    assert scenes[0]["entityId"] == "LC09_L2SP_027031_20250615_20250626_02_T2"
    assert scenes[0]["cloudCover"] == 5.2


def test_search_scenes_requires_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    client = M2MClient("test_user", "test_token_64chars....................")
    with pytest.raises(M2MError, match="Not authenticated"):
        client.search_scenes(
            dataset_name="landsat_ot_c2_l2",
            start_date="2025-04-01",
            end_date="2025-10-31",
            bbox=[-93.8, 41.8, -93.3, 42.3],
        )


def test_login_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    client = M2MClient("bad_user", "bad_token")

    def bad_post(url: str, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(401, {}, "unauthorized")

    client._client.post = bad_post  # type: ignore[method-assign]
    with pytest.raises(M2MError, match="M2M login failed"):
        client.login()


def test_download_options(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(monkeypatch)
    client.login()
    result = client.download_options(
        ["LC09_L2SP_027031_20250615_20250626_02_T2"]
    )
    assert "data" in result


def test_download_request_and_retrieve(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(monkeypatch)
    client.login()
    req = client.download_request(
        [
            {
                "entityId": "LC09_L2SP_027031_20250615_20250626_02_T2",
                "productId": "...-SR_B4",
            }
        ]
    )
    assert req["downloadRequestId"] == "req_12345"
    retrieved = client.download_retrieve("req_12345")
    assert retrieved["data"][0]["available"] is True