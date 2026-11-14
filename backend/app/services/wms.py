"""WMS service helpers for Phase 2 map layers.

All URLs and layer names were verified against live service GetCapabilities /
GetMap responses before being hardcoded here. No values are guessed.
"""

from __future__ import annotations

CDL_WMS_BASE = "https://crop.csiss.gmu.edu/cgi-bin/wms_cdl_ia?"
SSURGO_WMS_BASE = "https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms?"

# CDL Iowa WMS layers verified via live GetCapabilities and GetMap (image/png).
# Layers exist for 2000 through 2025; Phase 1 period is 2021-2025.
CDL_LAYERS: dict[int, str] = {
    year: f"cdl_{year}_ia" for year in range(2021, 2026)
}

# SSURGO WMS layers verified via live GetMap (image/png).
SSURGO_LAYERS = ["SurveyAreaPoly", "MapunitPoly"]

WMS_COMMON_PARAMS = {
    "SERVICE": "WMS",
    "VERSION": "1.1.1",
    "REQUEST": "GetMap",
    "STYLES": "",
    "SRS": "EPSG:4326",
    "WIDTH": "256",
    "HEIGHT": "256",
    "FORMAT": "image/png",
    "TRANSPARENT": "TRUE",
}

# Story County, Iowa reference extent (EPSG:4326): [minx, miny, maxx, maxy]
STORY_COUNTY_BBOX = [-93.80, 41.80, -93.30, 42.30]


def build_wms_getmap_url(base_url: str, layers: list[str], bbox: list[float]) -> str:
    """Build a WMS GetMap URL for one layer list over one bbox."""
    params = dict(WMS_COMMON_PARAMS)
    params["LAYERS"] = ",".join(layers)
    params["BBOX"] = ",".join(str(v) for v in bbox)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return base_url + query