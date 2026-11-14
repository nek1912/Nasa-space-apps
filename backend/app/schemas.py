"""Locked Pydantic v2 response contracts for the Phase 1 real-data API.

Frontend mirror: `frontend/src/types/fieldshift.ts`. The Schema Lock Law in
RULES.md applies: never rename or remove a field here without updating the TS
mirror in the same change.

Phase 1 serves exactly one endpoint, `GET /api/region-summary`, built from
real provider responses (USDA NASS CDL, USDA NRCS SSURGO, NASA POWER) for a
single configured region. Nothing here is inferred, interpolated, or defaulted
to a synthetic value: absent measurements are `null`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RegionIdentity(BaseModel):
    """Identity of the single active region and the scope of its data."""

    region_id: str
    country: str
    state: str
    county: str
    county_fips: str = Field(description="USDA/FIPS county code, e.g. '19169'")
    soil_survey_area: str | None = Field(
        default=None,
        description="SSURGO survey area symbol (e.g. 'IA169'), null until confirmed by SDA",
    )
    latitude: float
    longitude: float
    start_date: str = Field(description="ISO date, first day of the requested period")
    end_date: str = Field(description="ISO date, last day of the requested period")
    geographic_scope: str = Field(
        description="Human-readable statement of what area the data actually represents"
    )


class SourceStatus(BaseModel):
    """Provenance and availability of one provider's contribution."""

    source_id: str = Field(description="Stable key, e.g. 'cdl', 'ssurgo', 'nasa_power'")
    provider: str = Field(description="e.g. 'USDA NASS', 'USDA NRCS', 'NASA POWER'")
    product: str = Field(description="e.g. 'CDL county statistics'")
    status: str = Field(description="'ok', 'stale' or 'unavailable'")
    geographic_scope: str = Field(description="Area this source actually represents")
    retrieved_at: str | None = Field(
        default=None, description="ISO 8601 retrieval timestamp of the saved raw response"
    )
    period_start: str | None = None
    period_end: str | None = None
    units: list[str] = Field(
        default_factory=list, description="Units of the values reported by this source"
    )
    detail: str | None = Field(
        default=None, description="Why a source is unavailable or stale, when applicable"
    )


class CropClass(BaseModel):
    """One CDL crop class as reported for the county in one year."""

    crop_name: str
    crop_code: int | None = None
    acres: float
    share_pct: float = Field(
        description="Share of the county's classified acreage, as reported"
    )


class CropYear(BaseModel):
    """CDL county statistics for a single crop year."""

    year: int
    classified_acres: float | None = Field(
        default=None,
        description="Total classified acreage the provider reported for the county",
    )
    crops: list[CropClass]


class SoilHorizon(BaseModel):
    """One reported soil horizon of a map-unit component."""

    depth_top_cm: float | None = None
    depth_bottom_cm: float | None = None
    sand_pct: float | None = None
    silt_pct: float | None = None
    clay_pct: float | None = None


class SoilComponent(BaseModel):
    """A named component of a map unit, with the attributes the source returned."""

    component_name: str
    component_pct: float | None = None
    horizons: list[SoilHorizon] = Field(default_factory=list)


class SoilMapUnit(BaseModel):
    """A SSURGO map unit with its major components."""

    mukey: str
    musym: str | None = None
    map_unit_name: str
    available_water_storage_cm: float | None = Field(
        default=None,
        description="aws025wta exactly as returned by SSURGO; null when absent",
    )
    components: list[SoilComponent]


class WeatherValue(BaseModel):
    """A single NASA POWER daily value; null when the source flagged it missing."""

    date: str
    value: float | None = None


class WeatherParameter(BaseModel):
    """One NASA POWER parameter series with its source-reported units."""

    parameter: str
    units: str | None = None
    long_name: str | None = None
    daily: list[WeatherValue]


class WeatherMonth(BaseModel):
    """Monthly aggregate derived only from the returned daily POWER values."""

    year: int
    month: int
    days_reported: int = Field(
        description="Count of days with a non-missing value, so gaps stay visible"
    )
    tmax_c_mean: float | None = None
    tmin_c_mean: float | None = None
    precip_mm_total: float | None = None
    rh2m_pct_mean: float | None = None
    solar_dwn_mj_m2_mean: float | None = None


class RegionSummary(BaseModel):
    """Complete response of `GET /api/region-summary`."""

    region: RegionIdentity
    data_status: str = Field(
        description="'ok' when every source loaded, otherwise 'partial' or 'unavailable'"
    )
    sources: list[SourceStatus]
    crops: list[CropYear] = Field(default_factory=list)
    soils: list[SoilMapUnit] = Field(default_factory=list)
    weather_parameters: list[WeatherParameter] = Field(default_factory=list)
    weather_monthly: list[WeatherMonth] = Field(default_factory=list)


class WmsLayerInfo(BaseModel):
    """Metadata for one verified WMS map layer."""

    name: str = Field(description="WMS layer name, e.g. 'cdl_2021_ia'")
    title: str = Field(description="Human-readable layer title")
    srs: list[str] = Field(description="Supported coordinate reference systems")
    bounds: list[float] = Field(
        description="Layer extent [minx, miny, maxx, maxy] in EPSG:4326"
    )
    format: str = Field(default="image/png", description="WMS output format")


class CdLYearInfo(BaseModel):
    """One available CDL crop-year layer."""

    year: int
    layer_name: str = Field(description="WMS layer name, e.g. 'cdl_2021_ia'")
    wms_url: str = Field(description="Base WMS service URL")
    available: bool = Field(
        default=True, description="Whether a live GetMap request succeeded"
    )


class SsurgoLayerInfo(BaseModel):
    """SSURGO WMS layer availability."""

    layer_name: str = Field(description="WMS layer name, e.g. 'MapunitPoly'")
    wms_url: str = Field(description="Base WMS service URL")
    available: bool = Field(
        default=True, description="Whether a live GetMap request succeeded"
    )


class LayerInfoResponse(BaseModel):
    """Complete response of `GET /api/layer-info`."""

    cdl_years: list[CdLYearInfo]
    ssurgo_layer: SsurgoLayerInfo | None = None
    cdl_wms_base_url: str
    ssurgo_wms_base_url: str
    story_county_bbox: list[float] = Field(
        description="Story County extent [minx, miny, maxx, maxy] in EPSG:4326"
    )
    aoi_statistics_blocker: str | None = Field(
        default=None,
        description="If CDL AOI/bbox statistics cannot be queried, the reason; "
        "null when available",
    )