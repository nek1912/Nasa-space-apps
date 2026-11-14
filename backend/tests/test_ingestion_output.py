"""Offline validation that ingestion produces a valid RegionSummary-shaped payload."""

from app.schemas import RegionSummary


def _make_cdl_result() -> dict:
    return {
        "source_id": "cdl",
        "provider": "USDA NASS",
        "product": "Cropland Data Layer (CDL) county statistics",
        "status": "ok",
        "geographic_scope": "Story County, Iowa (FIPS 19169) — county-wide crop statistics",
        "period_start": "2021-01-01",
        "period_end": "2025-12-31",
        "units": ["acres", "percent of classified acreage"],
        "retrieved_at": "2026-01-01T00:00:00+00:00",
        "detail": None,
        "crops": [
            {
                "year": 2021,
                "classified_acres": 150.0,
                "crops": [
                    {"crop_name": "Corn", "crop_code": 1, "acres": 100.0, "share_pct": 66.67},
                    {"crop_name": "Soybeans", "crop_code": 5, "acres": 50.0, "share_pct": 33.33},
                ],
            }
        ],
    }


def _make_ssurgo_result() -> dict:
    return {
        "source_id": "ssurgo",
        "provider": "USDA NRCS",
        "product": "SSURGO mapped soil survey data",
        "status": "ok",
        "geographic_scope": "Story County, Iowa (survey area IA169) — map-unit level",
        "period_start": None,
        "period_end": None,
        "units": ["percent", "centimeters"],
        "retrieved_at": "2026-01-01T00:00:00+00:00",
        "detail": None,
        "soils": [
            {
                "mukey": "1001",
                "musym": "100",
                "map_unit_name": "Mukey A loam",
                "available_water_storage_cm": 12.5,
                "components": [
                    {
                        "component_name": "Loam component",
                        "component_pct": 85,
                        "horizons": [
                            {
                                "depth_top_cm": 0,
                                "depth_bottom_cm": 15,
                                "sand_pct": 40,
                                "silt_pct": 40,
                                "clay_pct": 20,
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _make_power_result() -> dict:
    return {
        "source_id": "nasa_power",
        "provider": "NASA POWER",
        "product": "Daily gridded meteorological data at a reference point",
        "status": "ok",
        "geographic_scope": "NASA POWER 0.5° grid cell containing 42.03° N, -93.631° W — regional weather context",
        "period_start": "2021-01-01",
        "period_end": "2025-12-31",
        "units": ["°C", "mm/day", "%", "MJ/m²/day"],
        "retrieved_at": "2026-01-01T00:00:00+00:00",
        "detail": None,
        "parameters": [
            {
                "parameter": "T2M_MAX",
                "units": "C",
                "long_name": "Temperature at 2 Meters Maximum",
                "daily": [
                    {"date": "20210101", "value": -3.64},
                    {"date": "20210102", "value": None},
                    {"date": "20210103", "value": 0.8},
                ],
            }
        ],
        "monthly": [
            {
                "year": 2021,
                "month": 1,
                "days_reported": 2,
                "tmax_c_mean": -1.42,
                "tmin_c_mean": None,
                "precip_mm_total": None,
                "rh2m_pct_mean": None,
                "solar_dwn_mj_m2_mean": None,
            }
        ],
    }


def test_ingestion_output_validates_against_region_summary() -> None:
    """The ingestion script's output must conform to the locked RegionSummary schema."""
    summary = {
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
            "geographic_scope": "Story County, Iowa — county/regional scale only; not parcel- or field-level",
        },
        "data_status": "ok",
        "sources": [_make_cdl_result(), _make_ssurgo_result(), _make_power_result()],
        "crops": _make_cdl_result()["crops"],
        "soils": _make_ssurgo_result()["soils"],
        "weather_parameters": _make_power_result()["parameters"],
        "weather_monthly": _make_power_result()["monthly"],
    }
    validated = RegionSummary.model_validate(summary)
    assert validated.region.county_fips == "19169"
    assert validated.data_status == "ok"
    assert len(validated.sources) == 3
    assert validated.sources[0].source_id == "cdl"
    assert validated.sources[1].source_id == "ssurgo"
    assert validated.sources[2].source_id == "nasa_power"
    assert len(validated.crops) == 1
    assert validated.crops[0].year == 2021
    assert len(validated.weather_parameters) == 1
    assert validated.weather_parameters[0].parameter == "T2M_MAX"
    assert len(validated.weather_monthly) == 1
    assert validated.weather_monthly[0].year == 2021
    assert validated.weather_monthly[0].month == 1