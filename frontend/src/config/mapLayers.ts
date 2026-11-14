/* Verified WMS/WMTS tile templates for Phase 2 map layers.

All URLs, layer names, and CRS values were confirmed against live service
GetCapabilities/GetMap responses. No values are guessed.
*/

export const OSM_BASE_LAYER = {
    name: "OpenStreetMap",
    type: "raster",
    url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: "\u00A9 OpenStreetMap contributors",
};

/* USDA NASS Cropland Data Layer — Iowa WMS.
   Verified: GetCapabilities lists cdl_2021_ia … cdl_2025_ia; GetMap returns
   image/png for Story County bbox with SRS=EPSG:4326. */
export const CDL_WMS = {
    baseUrl: "https://crop.csiss.gmu.edu/cgi-bin/wms_cdl_ia?",
    srs: "EPSG:4326",
    format: "image/png",
    width: 256,
    height: 256,
    transparent: true,
    layerForYear: (year: number): string => `cdl_${year}_ia`,
    availableYears: [2021, 2022, 2023, 2024, 2025],
    title: "USDA NASS Cropland Data Layer — Iowa",
};

/* USDA NRCS SSURGO — Soil map units WMS.
   Verified: GetMap returns image/png for MapunitPoly with SRS=EPSG:4326. */
export const SSURGO_WMS = {
    baseUrl: "https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms?",
    srs: "EPSG:4326",
    format: "image/png",
    width: 256,
    height: 256,
    transparent: true,
    layerName: "MapunitPoly",
    title: "USDA NRCS SSURGO — Map Unit Polygons",
};

/* Story County, Iowa reference extent (EPSG:4326): [minx, miny, maxx, maxy] */
export const STORY_COUNTY_BBOX = [-93.80, 41.80, -93.30, 42.30];

/* Map center [lon, lat] and zoom for Story County */
export const STORY_COUNTY_CENTER = [-93.631, 42.03];
export const STORY_COUNTY_ZOOM = 9;