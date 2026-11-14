# Verified USGS M2M API — Landsat Collection 2 Level-2 (Phase 3 research)

All request/response shapes below were verified from official USGS documentation
(`code.usgs.gov/eros-user-services/machine_to_machine` and the NegativeBounce API
library reference). No values are guessed.

## Authentication

EROS Registration Service (ERS) account with MACHINE role access is required.
Access must be requested via https://ers.cr.usgs.gov/ and approved by USGS
(typically a few days).

**Base URL:** `https://m2m.cr.usgs.gov/api/api/json/stable/`

**Endpoint:** `POST /login-token`

```json
// Request
{"username": "<ERS_USERNAME>", "token": "<64-char-application-token>"}

// Response
{"apiKey": "<session-api-key>", ...}
```

The returned `apiKey` is sent as `X-Auth-Token` on all subsequent calls.

## Scene Search — Landsat 8-9 Collection 2 Level-2

**Endpoint:** `POST /scene-search`

Dataset name for Landsat 8-9 OLI/TIRS Collection 2 Level-2 Surface Reflectance:
`landsat_ot_c2_l2`

### Request body

```json
{
  "datasetName": "landsat_ot_c2_l2",
  "startDate": "2025-04-01",
  "endDate": "2025-10-31",
  "sceneFilter": {
    "spatialFilter": {
      "filterType": "mbr",
      "lowerLeft": {"x": -93.8, "y": 41.8},
      "upperRight": {"x": -93.3, "y": 42.3}
    },
    "acquisitionFilter": {
      "start": "2025-04-01",
      "end": "2025-10-31"
    },
    "cloudCoverFilter": {
      "min": 0,
      "max": 20,
      "includeUnknown": false
    }
  },
  "maxResults": 50
}
```

### Spatial filter types
- `"mbr"` — bounding box: `lowerLeft {x, y}`, `upperRight {x, y}`
- `"geoJson"` — GeoJSON geometry object

### Response format

```json
{
  "data": [
    {
      "entityId": "LE07_L1GT_016034_20210415_20210427_02_T2",
      "displayId": "LC09_L2SP_027031_20250615_20250626_02_T2",
      "spatialCoverage": "...",
      "cloudCover": 5.2,
      "acquisitionDate": "2025-06-15",
      ...
    }
  ],
  ...
}
```

The `entityId` is used in the download flow.

## Download flow (after scene-search)

1. `POST /download-options` — get available products for scene entityIds
2. `POST /download-request` — request download (returns request ID)
3. `POST /download-retrieve` — poll until download URL is ready
4. `POST /logout` — end session

## Landsat Collection 2 Level-2 Surface Reflectance technical specs

| Property | Value |
|----------|-------|
| Product | Landsat 8-9 OLI/TIRS Collection 2 Level-2 |
| Dataset name | `landsat_ot_c2_l2` |
| Bands | SR_B1 (coastal), SR_B2 (blue), SR_B3 (green), SR_B4 (red), SR_B5 (NIR), SR_B6 (SWIR1), SR_B7 (SWIR2), QA_PIXEL |
| Pixel size | 30 m |
| Scale factor | SR = DN × 0.0000275 − 0.2 |
| QA_PIXEL | Bitmask for cloud, cloud shadow, snow, water, fill |

NDVI = (SR_B5 − SR_B4) / (SR_B5 + SR_B4) using scaled surface reflectance.

## Constraints (roadmap §17)

- RULES.md bans `rasterio`, `gdal`, `netCDF4`, `h5py` on the backend.
- Do **not** hand-write a GeoTIFF parser.
- Before computing NDVI, perform a technical spike: either propose a narrowly-scoped
  `rasterio` exception for preprocessing only (update RULES.md/DECISIONS.md), or use a
  verified external processing service.
- Until NDVI is implemented, the app may display a verified Landsat image layer for
  context but must not show computed NDVI values.
