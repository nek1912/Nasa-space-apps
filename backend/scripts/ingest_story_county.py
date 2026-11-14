#!/usr/bin/env python3
"""Ingest the three Phase 1 sources for the configured region (Story County, IA).

Reads ``backend/config/region.json``, downloads USDA NASS CDL, USDA NRCS SSURGO
and NASA POWER responses, saves each raw response under ``backend/data/raw/``,
and writes the normalized summary to ``backend/data/processed/story_county.json``.

Run:  cd backend && python scripts/ingest_story_county.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from statistics import mean
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data_store import (
    PROCESSED_DIR,
    RAW_DIR,
    REGION_CONFIG_PATH,
    save_processed_summary,
    save_raw_response,
)
from app.schemas import RegionSummary
from app.services.cdl import CdlError, fetch_cdl_stat, parse_cdl_stat
from app.services.nasa_power import PowerError, fetch_power_daily, parse_power_daily
from app.services.usda_soil import SdaError, confirm_survey_area, fetch_soil_data, parse_soil_data

SOURCES = ("cdl", "ssurgo", "nasa_power")
YEARS = list(range(2021, 2026))
POWER_PARAMETERS = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _month_key(date_str: str) -> tuple[int, int]:
    return int(date_str[:4]), int(date_str[4:6])


def ingest_cdl(region: dict) -> dict:
    county_fips = region["county_fips"]
    crops_by_year: list[dict] = []
    details: list[str] = []
    ok = True
    for year in YEARS:
        try:
            raw = fetch_cdl_stat(year, county_fips)
            save_raw_response("cdl", f"story_county_{year}.json", raw)
            crops_by_year.append(parse_cdl_stat(raw, year))
        except CdlError as exc:
            ok = False
            details.append(str(exc))
    return {
        "source_id": "cdl",
        "provider": "USDA NASS",
        "product": "Cropland Data Layer (CDL) county statistics",
        "status": "ok" if ok and crops_by_year else ("partial" if crops_by_year else "unavailable"),
        "geographic_scope": f"Story County, Iowa (FIPS {county_fips}) — county-wide crop statistics",
        "period_start": f"{YEARS[0]}-01-01",
        "period_end": f"{YEARS[-1]}-12-31",
        "units": ["acres", "percent of classified acreage"],
        "retrieved_at": _now_iso(),
        "detail": "; ".join(details) if details else None,
        "crops": crops_by_year,
    }


def ingest_ssurgo(region: dict) -> dict:
    areasymbol = region.get("soil_survey_area")
    details: list[str] = []
    soils: list[dict] = []
    ok = True
    try:
        if not areasymbol:
            confirmed = confirm_survey_area(region["state"], region["county"])
            if not confirmed:
                raise SdaError(f"Could not confirm SSURGO survey area for {region['state']} {region['county']}")
            areasymbol = confirmed
        raw = fetch_soil_data(areasymbol)
        save_raw_response("ssurgo", "story_county.json", raw)
        soils = parse_soil_data(raw)
    except SdaError as exc:
        ok = False
        details.append(str(exc))
    return {
        "source_id": "ssurgo",
        "provider": "USDA NRCS",
        "product": "SSURGO mapped soil survey data",
        "status": "ok" if ok and soils else ("partial" if soils else "unavailable"),
        "geographic_scope": f"{region['county']} County, {region['state']} (survey area {areasymbol or 'unconfirmed'}) — map-unit level",
        "period_start": None,
        "period_end": None,
        "units": ["percent", "centimeters"],
        "retrieved_at": _now_iso() if soils else None,
        "detail": "; ".join(details) if details else None,
        "soils": soils,
    }


def aggregate_monthly(parsed: dict) -> list[dict]:
    """Aggregate parsed POWER daily series into monthly summaries."""
    series_by_param: dict[str, dict[str, float | None]] = {}
    for block in parsed.get("parameters", []):
        by_date: dict[str, float | None] = {}
        for item in block.get("daily", []):
            by_date[item["date"]] = item["value"]
        series_by_param[block["parameter"]] = by_date

    all_dates = sorted({d for by_date in series_by_param.values() for d in by_date})
    months: dict[tuple[int, int], dict] = {}
    for date_str in all_dates:
        y, m = _month_key(date_str)
        bucket = months.setdefault(
            (y, m),
            {"year": y, "month": m, "days_reported": 0, "tmax": [], "tmin": [], "precip": [], "rh": [], "sw": []},
        )
        tmax = series_by_param["T2M_MAX"].get(date_str)
        if tmax is not None:
            bucket["days_reported"] += 1
            bucket["tmax"].append(tmax)
        tmin = series_by_param["T2M_MIN"].get(date_str)
        if tmin is not None:
            bucket["tmin"].append(tmin)
        precip = series_by_param["PRECTOTCORR"].get(date_str)
        if precip is not None:
            bucket["precip"].append(precip)
        rh = series_by_param["RH2M"].get(date_str)
        if rh is not None:
            bucket["rh"].append(rh)
        sw = series_by_param["ALLSKY_SFC_SW_DWN"].get(date_str)
        if sw is not None:
            bucket["sw"].append(sw)

    result: list[dict] = []
    for bucket in sorted(months.values(), key=lambda b: (b["year"], b["month"])):
        result.append(
            {
                "year": bucket["year"],
                "month": bucket["month"],
                "days_reported": bucket["days_reported"],
                "tmax_c_mean": round(mean(bucket["tmax"]), 2) if bucket["tmax"] else None,
                "tmin_c_mean": round(mean(bucket["tmin"]), 2) if bucket["tmin"] else None,
                "precip_mm_total": round(sum(bucket["precip"]), 2) if bucket["precip"] else None,
                "rh2m_pct_mean": round(mean(bucket["rh"]), 2) if bucket["rh"] else None,
                "solar_dwn_mj_m2_mean": round(mean(bucket["sw"]), 2) if bucket["sw"] else None,
            }
        )
    return result


def ingest_nasa_power(region: dict) -> dict:
    lat = region["latitude"]
    lon = region["longitude"]
    details: list[str] = []
    parameters_out: list[dict] = []
    monthly: list[dict] = []
    ok = True
    try:
        raw = fetch_power_daily(lat, lon, POWER_PARAMETERS, region["start_date"], region["end_date"])
        save_raw_response("nasa_power", "story_county_daily_2021_2025.json", raw)
        parsed = parse_power_daily(raw)
        parameters_out = parsed["parameters"]
        monthly = aggregate_monthly(parsed)
    except PowerError as exc:
        ok = False
        details.append(str(exc))
    return {
        "source_id": "nasa_power",
        "provider": "NASA POWER",
        "product": "Daily gridded meteorological data at a reference point",
        "status": "ok" if ok and parameters_out else ("partial" if parameters_out else "unavailable"),
        "geographic_scope": f"NASA POWER 0.5° grid cell containing {lat}° N, {lon}° W — regional weather context",
        "period_start": region["start_date"],
        "period_end": region["end_date"],
        "units": ["°C", "mm/day", "%", "MJ/m²/day"],
        "retrieved_at": _now_iso() if parameters_out else None,
        "detail": "; ".join(details) if details else None,
        "parameters": parameters_out,
        "monthly": monthly,
    }


def main() -> None:
    with open(REGION_CONFIG_PATH, encoding="utf-8") as f:
        region = json.load(f)

    cdl_result = ingest_cdl(region)
    ssurgo_result = ingest_ssurgo(region)
    power_result = ingest_nasa_power(region)

    statuses = [cdl_result["status"], ssurgo_result["status"], power_result["status"]]
    data_status = (
        "ok"
        if all(s == "ok" for s in statuses)
        else ("partial" if any(s != "unavailable" for s in statuses) else "unavailable")
    )

    ssurgo_scope = ssurgo_result["geographic_scope"]
    confirmed_area = None
    if "survey area " in ssurgo_scope:
        confirmed_area = ssurgo_scope.split("survey area ")[1].split(")")[0]

    summary = {
        "region": {
            "region_id": region["region_id"],
            "country": region["country"],
            "state": region["state"],
            "county": region["county"],
            "county_fips": region["county_fips"],
            "soil_survey_area": confirmed_area or region.get("soil_survey_area"),
            "latitude": region["latitude"],
            "longitude": region["longitude"],
            "start_date": region["start_date"],
            "end_date": region["end_date"],
            "geographic_scope": "Story County, Iowa — county/regional scale only; not parcel- or field-level",
        },
        "data_status": data_status,
        "sources": [
            {
                "source_id": r["source_id"],
                "provider": r["provider"],
                "product": r["product"],
                "status": r["status"],
                "geographic_scope": r["geographic_scope"],
                "retrieved_at": r["retrieved_at"],
                "period_start": r["period_start"],
                "period_end": r["period_end"],
                "units": r["units"],
                "detail": r["detail"],
            }
            for r in (cdl_result, ssurgo_result, power_result)
        ],
        "crops": cdl_result["crops"],
        "soils": ssurgo_result["soils"],
        "weather_parameters": power_result["parameters"],
        "weather_monthly": power_result["monthly"],
    }

    RegionSummary.model_validate(summary)
    save_processed_summary(summary)

    print("Ingestion complete")
    for r in (cdl_result, ssurgo_result, power_result):
        print(f"  {r['source_id']}: {r['status']}  detail={r['detail'] or '-'}")
    print(f"  data_status: {data_status}")
    print(f"  processed -> backend/data/processed/story_county.json")


if __name__ == "__main__":
    main()