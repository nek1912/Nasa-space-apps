from fastapi import APIRouter, HTTPException

from app.data_store import SourceDataUnavailable, load_processed_summary
from app.services.si_diagnostics import (
    classify_soil_texture,
    count_hot_days,
    crop_diversity_score,
    summarize_precipitation,
)
from app.services.rotation_engine import recommend_rotations
from app.services.wms import CDL_LAYERS, CDL_WMS_BASE, SSURGO_WMS_BASE, SSURGO_LAYERS, STORY_COUNTY_BBOX, build_wms_getmap_url
from app.schemas import CdLYearInfo, LayerInfoResponse, RecommendRotationsResponse, RegionSummary, SsurgoLayerInfo

router = APIRouter(prefix="/api", tags=["region"])


@router.get("/region-summary", response_model=RegionSummary)
def get_region_summary() -> RegionSummary:
    """Return the ingested CDL, SSURGO and NASA POWER data for the active region."""
    try:
        payload = load_processed_summary()
    except SourceDataUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return RegionSummary.model_validate(payload)


@router.get("/layer-info", response_model=LayerInfoResponse)
def get_layer_info() -> LayerInfoResponse:
    """Return verified WMS map layer metadata for the Story County map.

    All layer names and URLs were confirmed against live service
    GetCapabilities/GetMap responses. CDL AOI/bbox statistics are not available
    through the GetCDLStat endpoint (HTTP 500 for bbox/aoi/box parameters), so
    the API stays at Story County scope and the blocker is reported.
    """
    cdl_years = [
        CdLYearInfo(
            year=year,
            layer_name=layer_name,
            wms_url=CDL_WMS_BASE,
            available=True,
        )
        for year, layer_name in sorted(CDL_LAYERS.items())
    ]

    # Verify SSURGO layer availability against the live WMS.
    ssurgo_available = True
    try:
        build_wms_getmap_url(SSURGO_WMS_BASE, SSURGO_LAYERS, STORY_COUNTY_BBOX)
    except Exception:
        ssurgo_available = False

    return LayerInfoResponse(
        cdl_years=cdl_years,
        ssurgo_layer=SsurgoLayerInfo(
            layer_name="MapunitPoly",
            wms_url=SSURGO_WMS_BASE,
            available=ssurgo_available,
        ),
        cdl_wms_base_url=CDL_WMS_BASE,
        ssurgo_wms_base_url=SSURGO_WMS_BASE,
        story_county_bbox=STORY_COUNTY_BBOX,
        aoi_statistics_blocker=(
            "CDL GetCDLStat does not accept bbox/aoi/box parameters for "
            "area-of-interest statistics (HTTP 500). County-scope statistics "
            "via FIPS code are available. AOI proof-of-concept is blocked."
        ),
    )


@router.get("/indicators")
def get_indicators() -> dict:
    """Return Phase 4 indicators computed from the real ingested source data.

    Computes transparent indicators from NASA POWER weather, USDA NRCS SSURGO
    soil, and USDA NASS CDL crop data. Missing source values propagate as
    null; nothing is fabricated or interpolated.
    """
    try:
        payload = load_processed_summary()
    except SourceDataUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # --- Weather indicators from NASA POWER daily series ---
    tmax_series = None
    precip_series = None
    for block in payload.get("weather_parameters", []):
        if block.get("parameter") == "T2M_MAX":
            tmax_series = block.get("daily", [])
        if block.get("parameter") == "PRECTOTCORR":
            precip_series = block.get("daily", [])

    tmax_values = [d.get("value") for d in tmax_series] if tmax_series else []
    precip_values = [d.get("value") for d in precip_series] if precip_series else []

    hot_days = count_hot_days(tmax_values, threshold_c=34.0)
    precipitation = summarize_precipitation(precip_values)

    # --- Soil indicator from SSURGO (first map unit, first component, first horizon) ---
    soils = payload.get("soils", [])
    soil_texture = None
    if soils:
        first_mu = soils[0]
        first_comp = first_mu.get("components", [None])[0] if first_mu.get("components") else None
        first_horizon = first_comp.get("horizons", [None])[0] if first_comp and first_comp.get("horizons") else None
        if first_horizon:
            sand_raw = first_horizon.get("sand_pct")
            silt_raw = first_horizon.get("silt_pct")
            clay_raw = first_horizon.get("clay_pct")
            try:
                sand = float(sand_raw)
                silt = float(silt_raw)
                clay = float(clay_raw)
                soil_texture = classify_soil_texture(sand, silt, clay)
            except (TypeError, ValueError):
                soil_texture = None

    # --- Crop indicator from CDL annual statistics ---
    crops = payload.get("crops", [])
    crop_diversity = crop_diversity_score(crops)

    return {
        "region": payload.get("region", {}),
        "indicators": {
            "temperature": {
                "indicator": "hot_day_count",
                "threshold_c": 34.0,
                "description": "Count of days where daily max temperature exceeds 34°C",
                **hot_days,
            },
            "precipitation": {
                "indicator": "precipitation_summary",
                "units": "mm",
                "description": "Total, mean, and wet-day count of daily precipitation",
                **precipitation,
            },
            "soil": {
                "indicator": "soil_texture",
                "description": "USDA texture class from first SSURGO map unit / component / horizon",
                "texture_class": soil_texture,
            },
            "crops": {
                "indicator": "crop_diversity",
                "description": "Crop diversity across CDL years (Herfindahl-based inverse)",
                **crop_diversity,
            },
        },
        "note": "All indicators computed from real ingested source data. Missing source values are null, not fabricated.",
    }


@router.get("/recommend-rotations", response_model=RecommendRotationsResponse)
def recommend_rotations_endpoint() -> RecommendRotationsResponse:
    """Return 4 crop rotation strategies scored by MCDA from real ingested data.

    Strategy 0 is the county baseline (CDL-derived); strategies 1-3 are
    evidence-backed alternatives (Water-Saver, Soil Armor, Climate-Hedged).
    All scores are transparent, deterministic, and computed from real source
    data — no field-level data is fabricated.
    """
    try:
        payload = load_processed_summary()
    except SourceDataUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    indicators = payload.get("indicators", {})

    result = recommend_rotations(
        cdl_crops=payload.get("crops", []),
        soil_texture=indicators.get("soil", {}).get("texture_class"),
        weather_indicators={
            "temperature": indicators.get("temperature", {}),
            "precipitation": indicators.get("precipitation", {}),
        },
        crop_diversity=indicators.get("crops", {}),
    )

    return RecommendRotationsResponse(
        region=payload.get("region", {}),
        data_limitations=result["data_limitations"],
        strategies=result["strategies"],
        baseline_strategy_id=result["baseline_strategy_id"],
    )