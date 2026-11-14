"""USGS EROS Machine-to-Machine (M2M) API client for Landsat Collection 2 Level-2.

Implements the search/download flow without any raster dependency:
  POST /login-token    -> authenticate (ERS username + app token)
  POST /scene-search   -> find scenes for an AOI/date range/cloud cover
  POST /download-options  -> list available products per scene
  POST /download-request  -> request a download (returns request id)
  POST /download-retrieve -> poll for the signed download URL
  POST /logout         -> end the session

No GeoTIFF parsing, no rasterio, no NDVI computation here. Those are gated on
the rasterio exception (RULES.md §5) and Landsat data download (Phase 3 gate).

All raw responses are saved under backend/data/raw/landsat/ for provenance.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.paths import RAW_DIR

M2M_BASE = "https://m2m.cr.usgs.gov/api/api/json/stable/"
TIMEOUT = 30.0
LANDSAT_C2L2_DATASET = "landsat_ot_c2_l2"


class M2MError(RuntimeError):
    """Raised when the M2M API cannot be reached or returns an error."""


class M2MClient:
    """Thin client for the USGS M2M API.

    Usage:
        client = M2MClient(username, app_token)
        client.login()
        scenes = client.search_scenes(
            dataset_name="landsat_ot_c2_l2",
            start_date="2025-04-01",
            end_date="2025-10-31",
            bbox=[-93.8, 41.8, -93.3, 42.3],
            max_cloud=20,
        )
        client.logout()
    """

    def __init__(self, username: str, app_token: str) -> None:
        self.username = username
        self.app_token = app_token
        self.api_key: str | None = None
        self._client = httpx.Client(timeout=TIMEOUT)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Auth-Token"] = self.api_key
        return headers

    def login(self) -> str:
        """Authenticate and store the session API key."""
        resp = self._client.post(
            M2M_BASE + "login-token",
            headers=self._headers(),
            json={"username": self.username, "token": self.app_token},
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise M2MError(f"M2M login failed: {resp.status_code} {resp.text[:200]}") from exc
        payload = resp.json()
        self.api_key = payload.get("apiKey")
        if not self.api_key:
            raise M2MError(f"M2M login returned no apiKey: {resp.text[:200]}")
        self._save_raw("login", payload)
        return self.api_key
    def search_scenes(
        self,
        dataset_name: str,
        start_date: str,
        end_date: str,
        bbox: list[float],
        max_cloud: int = 20,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Search for Landsat scenes and return the raw scene list."""
        if self.api_key is None:
            raise M2MError("Not authenticated. Call login() first.")
        minx, miny, maxx, maxy = bbox
        body = {
            "datasetName": dataset_name,
            "startDate": start_date,
            "endDate": end_date,
            "sceneFilter": {
                "spatialFilter": {
                    "filterType": "mbr",
                    "lowerLeft": {"x": minx, "y": miny},
                    "upperRight": {"x": maxx, "y": maxy},
                },
                "acquisitionFilter": {"start": start_date, "end": end_date},
                "cloudCoverFilter": {
                    "min": 0,
                    "max": max_cloud,
                    "includeUnknown": False,
                },
            },
            "maxResults": max_results,
        }
        resp = self._client.post(
            M2M_BASE + "scene-search",
            headers=self._headers(),
            json=body,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise M2MError(
                f"M2M scene-search failed: {resp.status_code} {resp.text[:200]}"
            ) from exc
        payload = resp.json()
        self._save_raw("scene_search", payload)
        return payload.get("data", [])

    def download_options(self, entity_ids: list[str]) -> dict[str, Any]:
        """Get available download products for one or more scenes."""
        if self.api_key is None:
            raise M2MError("Not authenticated. Call login() first.")
        body = {"entityIds": entity_ids}
        resp = self._client.post(
            M2M_BASE + "download-options",
            headers=self._headers(),
            json=body,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise M2MError(
                f"M2M download-options failed: {resp.status_code} {resp.text[:200]}"
            ) from exc
        payload = resp.json()
        self._save_raw("download_options", payload)
        return payload

    def download_request(self, downloads: list[dict[str, Any]]) -> dict[str, Any]:
        """Request a download for prepared products (returns a request id)."""
        if self.api_key is None:
            raise M2MError("Not authenticated. Call login() first.")
        body = {"downloads": downloads}
        resp = self._client.post(
            M2M_BASE + "download-request",
            headers=self._headers(),
            json=body,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise M2MError(
                f"M2M download-request failed: {resp.status_code} {resp.text[:200]}"
            ) from exc
        payload = resp.json()
        self._save_raw("download_request", payload)
        return payload

    def download_retrieve(self, request_id: str) -> dict[str, Any]:
        """Retrieve a signed download URL for a completed request."""
        if self.api_key is None:
            raise M2MError("Not authenticated. Call login() first.")
        body = {"downloadRequestId": request_id}
        resp = self._client.post(
            M2M_BASE + "download-retrieve",
            headers=self._headers(),
            json=body,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise M2MError(
                f"M2M download-retrieve failed: {resp.status_code} {resp.text[:200]}"
            ) from exc
        payload = resp.json()
        self._save_raw("download_retrieve", payload)
        return payload

    def logout(self) -> None:
        """End the M2M session."""
        if self.api_key is None:
            return
        try:
            self._client.post(M2M_BASE + "logout", headers=self._headers())
        except httpx.HTTPError:
            pass  # logout failures should not mask earlier success
        finally:
            self._client.close()
            self.api_key = None

    def _save_raw(self, step: str, payload: Any) -> Path:
        """Persist an unmodified M2M response for provenance."""
        target_dir = RAW_DIR / "landsat"
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = target_dir / f"{step}_{timestamp}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return path