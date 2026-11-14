from fastapi import APIRouter, HTTPException

from app.data_store import SourceDataUnavailable, load_processed_summary
from app.schemas import CdLYearInfo, LayerInfoResponse, RegionSummary, SsurgoLayerInfo
from app.services.wms import CDL_LAYERS, CDL_WMS_BASE, SSURGO_WMS_BASE, SSURGO_LAYERS, STORY_COUNTY_BBOX, build_wms_getmap_url

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