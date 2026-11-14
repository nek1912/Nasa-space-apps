"""Contract tests for the region summary API and schema."""

from fastapi.testclient import TestClient

from app.data_store import SourceDataUnavailable
from app.main import app
from app.schemas import RegionSummary

client = TestClient(app)


def test_region_summary_schema_round_trip() -> None:
    payload = {
        "region": {
            "region_id": "us-ia-story",
            "country": "USA",
            "state": "Iowa",
            "county": "Story",
            "county_fips": "19169",
            "soil_survey_area": "IA169",
            "latitude": 42.03,
            "longitude": -93.631,
            "start_date": "2021-01-01",
            "end_date": "2025-12-31",
            "geographic_scope": "Story County, Iowa — county/regional scale only",
        },
        "data_status": "ok",
        "sources": [],
        "crops": [],
        "soils": [],
        "weather_parameters": [],
        "weather_monthly": [],
    }
    summary = RegionSummary.model_validate(payload)
    assert summary.region.county_fips == "19169"
    assert summary.data_status == "ok"
    assert summary.model_dump()["region"]["region_id"] == "us-ia-story"


def test_region_summary_returns_503_when_not_ingested(monkeypatch) -> None:
    """Missing processed data must surface as an explicit 503, never placeholder data."""
    import app.api.routes_field as routes

    def boom() -> dict:
        raise SourceDataUnavailable("missing")

    monkeypatch.setattr(routes, "load_processed_summary", boom)
    resp = client.get("/api/region-summary")
    assert resp.status_code == 503
    assert "error" in resp.json()