# Verified CropScape CDL Service Requests (Phase 2)

All requests below were tested against live services before being hardcoded into
the codebase. No values are guessed.

## WMS GetCapabilities

**URL:** `https://crop.csiss.gmu.edu/cgi-bin/wms_cdl_ia?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities`

**Result:** Valid WMS 1.1.1 capabilities XML (25,750 bytes).

**Key findings:**
- Service title: "Cropland Data Layer WMS Service for Iowa"
- OnlineResource: `https://crop.csiss.gmu.edu/cgi-bin/wms_cdl_ia?`
- MapServer 7.7.0-dev
- Layers follow pattern `cdl_YYYY_ia` (verified: cdl_2021_ia, cdl_2022_ia)
- Supported SRS: `epsg:5070`, `epsg:102004`, `epsg:4326` (WGS84)
- Iowa LatLonBoundingBox: [-96.6479, 40.3274, -90.0159, 43.5874]
- GetMap formats include `image/png`

## WMS GetMap — CDL 2021 (VERIFIED)

**URL:** `https://crop.csiss.gmu.edu/cgi-bin/wms_cdl_ia?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=cdl_2021_ia&STYLES=&SRS=EPSG:4326&BBOX=-93.8,41.8,-93.3,42.3&WIDTH=600&HEIGHT=400&FORMAT=image/png`

**Result:** `Content-Type: image/png`, 57,707 bytes — valid map image.

## WMS GetMap — CDL 2022 (VERIFIED)

**URL:** `https://crop.csiss.gmu.edu/cgi-bin/wms_cdl_ia?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=cdl_2022_ia&STYLES=&SRS=EPSG:4326&BBOX=-93.8,41.8,-93.3,42.3&WIDTH=600&HEIGHT=400&FORMAT=image/png`

**Result:** `Content-Type: image/png`, 57,837 bytes — valid map image.

## GetCDLStat — County Statistics (VERIFIED)

**URL:** `https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLStat?year=2021&fips=19169&format=json`

**Result:** XML with `<returnURL>` pointing to JSON cache at
`https://nassgeodata.gmu.edu/webservice/nass_data_cache/byfips/CDL_2021_19169.json`

**JSON cache shape:** `{success, totalCount, fileName, rows[{value, count, category, color, acreage}]}`
- 34 crop classes for Story County 2021
- Top classes: Corn (143,005.8 acres), Soybeans (129,325.6 acres), Grass/Pasture (37,156.4 acres)

## GetCDLStat — AOI/BBox Statistics (BLOCKED)

The following parameter combinations were tested, all returning **HTTP 500**:

1. `?year=2021&aoi=-93.8,41.8,-93.3,42.3&type=b&format=json`
2. `?year=2021&box=-93.8,41.8,-93.3,42.3&format=json`
3. `?year=2021&bbox=-93.8,41.8,-93.3,42.3&format=json`

**Conclusion:** The GetCDLStat axis2 endpoint does not accept bbox/aoi/box
parameters for area-of-interest statistics. County-scope statistics via FIPS
code are available. The AOI proof-of-concept is **blocked** on this endpoint.

**Decision per roadmap §16:** Keep the API at Story County scope and record the
blocker. Do not simulate field-level data.
