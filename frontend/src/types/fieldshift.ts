/* Exact TS mirror of backend/app/schemas.py (Schema Lock Law — RULES.md) */

export interface RegionIdentity {
    region_id: string;
    country: string;
    state: string;
    county: string;
    county_fips: string;
    soil_survey_area: string | null;
    latitude: number;
    longitude: number;
    start_date: string;
    end_date: string;
    geographic_scope: string;
}

export interface SourceStatus {
    source_id: string;
    provider: string;
    product: string;
    status: "ok" | "stale" | "unavailable";
    geographic_scope: string;
    retrieved_at: string | null;
    period_start: string | null;
    period_end: string | null;
    units: string[];
    detail: string | null;
}

export interface CropClass {
    crop_name: string;
    crop_code: number | null;
    acres: number;
    share_pct: number;
}

export interface CropYear {
    year: number;
    classified_acres: number | null;
    crops: CropClass[];
}

export interface SoilHorizon {
    depth_top_cm: number | null;
    depth_bottom_cm: number | null;
    sand_pct: number | null;
    silt_pct: number | null;
    clay_pct: number | null;
}

export interface SoilComponent {
    component_name: string;
    component_pct: number | null;
    horizons: SoilHorizon[];
}

export interface SoilMapUnit {
    mukey: string;
    musym: string | null;
    map_unit_name: string;
    available_water_storage_cm: number | null;
    components: SoilComponent[];
}

export interface WeatherValue {
    date: string;
    value: number | null;
}

export interface WeatherParameter {
    parameter: string;
    units: string | null;
    long_name: string | null;
    daily: WeatherValue[];
}

export interface WeatherMonth {
    year: number;
    month: number;
    days_reported: number;
    tmax_c_mean: number | null;
    tmin_c_mean: number | null;
    precip_mm_total: number | null;
    rh2m_pct_mean: number | null;
    solar_dwn_mj_m2_mean: number | null;
}

/* Phase 2 — WMS map layer metadata (mirrors backend LayerInfoResponse) */
export interface WmsLayerInfo {
    name: string;
    title: string;
    srs: string[];
    bounds: number[];
    format: string;
}

export interface CdLYearInfo {
    year: number;
    layer_name: string;
    wms_url: string;
    available: boolean;
}

export interface SsurgoLayerInfo {
    layer_name: string;
    wms_url: string;
    available: boolean;
}

export interface LayerInfoResponse {
    cdl_years: CdLYearInfo[];
    ssurgo_layer: SsurgoLayerInfo | null;
    cdl_wms_base_url: string;
    ssurgo_wms_base_url: string;
    story_county_bbox: number[];
    aoi_statistics_blocker: string | null;
}

export interface RegionSummary {
    region: RegionIdentity;
    data_status: string;
    sources: SourceStatus[];
    crops: CropYear[];
    soils: SoilMapUnit[];
    weather_parameters: WeatherParameter[];
    weather_monthly: WeatherMonth[];
}