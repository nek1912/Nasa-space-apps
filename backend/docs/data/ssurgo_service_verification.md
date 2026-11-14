# Verified NRCS SSURGO Spatial Service Requests (Phase 2)

All requests below were tested against live services before being hardcoded into
the codebase. No values are guessed.

## WMS Service Discovery

**Documentation:** `https://sdmdataaccess.nrcs.usda.gov/WebServiceHelp.aspx`

**Available spatial services:**
- WMS 1.1.1: `https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms`
- WFS 1.1.0 (WGS84): `https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDMWGS84Geographic.wfs`
- WFS 1.1.0 (NAD83): `https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDMNAD83Geographic.wfs`
- WFS (Web Mercator): `https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDMWM.wfs`

**Default SRS:** `EPSG:4326` (unless AOIID/INTERPRESULTID/THEMATICMAPID used, then EPSG:3857)

## WMS GetMap — MapunitPoly (VERIFIED)

**URL:** `https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=MapunitPoly&STYLES=&SRS=EPSG:4326&BBOX=-93.8,41.8,-93.3,42.3&WIDTH=600&HEIGHT=400&FORMAT=image/png`

**Result:** `Content-Type: image/png`, 1,582 bytes — valid map image.

**Sample URL from NRCS docs:**
```
https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms
?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap
&LAYERS=SurveyAreaPoly,MapunitPoly&STYLES=&SRS=EPSG:4326
&BBOX=-102.65253,38.18368,-102.59682,38.21139&WIDTH=600&HEIGHT=400&FORMAT=image/png
```

## WFS GetFeature — MapunitPoly (NOT VERIFIED)

**URL tested:** `https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDMWGS84Geographic.wfs?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=MapunitPoly&BBOX=-93.8,41.8,-93.3,42.3`

**Result:** Request timed out after 30 seconds. Not reliable enough for Phase 2.

**Decision:** SSURGO map layer is available via WMS (verified). WFS spatial
queries for map units within an AOI are not verified and not implemented in
Phase 2.

## Tabular SSURGO (Phase 1, already implemented)

`https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest` with SQL query
against `legend`, `mapunit`, `component`, `chorizon`, `muaggatt` tables.
Verified working via `confirm_survey_area()` and `fetch_soil_data()` in
`backend/app/services/usda_soil.py`.
