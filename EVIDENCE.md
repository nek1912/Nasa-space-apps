# FieldShift — Evidence Trail & Data Provenance

## Summary

All data in FieldShift traces to real USDA/NASA service responses. No synthetic data, no fabricated values, no placeholder fallbacks. Missing data is reported as unavailable, never invented.

---

## Phase 1 Data — Ingested and Verified

### USDA NASS Cropland Data Layer (CDL)

**Source:** CropScape GetCDLStat axis2 service + JSON cache
**County:** Story County, Iowa (FIPS 19169)
**Years:** 2021–2025
**Raw files:** `backend/data/raw/cdl/story_county_2021.json` … `2025.json`
**Request:** `GET https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLStat?year=YYYY&fips=19169&format=json`
**Response shape:** XML with `returnURL` → JSON cache `{success, totalCount, rows[{value, count, category, color, acreage}]}`

**Verified:** GetCDLStat returns returnURL for all 5 years; cache JSON parsed successfully for all 5 years.

**Top crops (2021):** Corn (143,005.8 acres), Soybeans (129,325.6 acres), Grass/Pasture (37,156.4 acres)
### USDA NRCS SSURGO

**Source:** Soil Data Access post.rest SQL query
**Survey area:** IA169 (Story County, Iowa)
**Raw file:** `backend/data/raw/ssurgo/story_county.json`
**Request:** `POST https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest` with SQL joining legend/mapunit/component/chorizon/muaggatt

**Verified:** Returns `{"Table": [[headers], [row1], ...]}` format with 86 map units. First unit: Webster clay loam (Clay loam texture).

**Query:** Major components only (`majcompflag = 'yes'`), ordered by map unit symbol and component percentage.

### NASA POWER

**Source:** POWER Daily API point request
**Location:** 42.03° N, -93.631° W (Story County reference point)
**Period:** 2021-01-01 through 2025-12-31
**Parameters:** T2M_MAX, T2M_MIN, PRECTOTCORR, RH2M, ALLSKY_SFC_SW_DWN
**Community:** AG
**Time standard:** UTC
**Raw file:** `backend/data/raw/nasa_power/story_county_daily_2021_2025.json`
**Request:** `GET https://power.larc.nasa.gov/api/temporal/daily/point?parameters=...&community=AG&longitude=-93.631&latitude=42.030&start=20210101&end=20251231&format=JSON&time-standard=UTC`

**Verified:** Returns `{"type": "Feature", "geometry": {...}, "properties": {"parameter": {"T2M_MAX": {"20210101": -3.64, ...}}}, "header": {"fill_value": -999, ...}, "parameters": {...}}`

**Missing value handling:** Source fill value (-999) normalized to `null`, never invented.
---

## Phase 2 Data — Map Layers Verified

### CropScape CDL WMS (Iowa)

**Service:** `https://crop.csiss.gmu.edu/cgi-bin/wms_cdl_ia?`
**Verified layers:** `cdl_2021_ia` … `cdl_2025_ia`
**SRS:** EPSG:5070, EPSG:102004, EPSG:4326
**Format:** image/png
**GetMap test:** `cdl_2021_ia` over Story County bbox returned valid PNG (57,707 bytes)

### NRCS SSURGO WMS

**Service:** `https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms`
**Verified layer:** `MapunitPoly`
**SRS:** EPSG:4326 (default)
**Format:** image/png
**GetMap test:** `MapunitPoly` over Story County bbox returned valid PNG (1,582 bytes)

### Blocked services (documented, not hidden)

| Service | Test | Result | Decision |
|---------|------|--------|----------|
| CDL GetCDLStat AOI stats | `aoi`, `box`, `bbox` params | HTTP 500 × 3 | County scope only; blocker documented |
| NRCS SSURGO WFS | `GetFeature` with BBOX | 30s timeout | Not reliable; not implemented |

---

## Phase 4 Indicators — Computed from Real Data

All indicators computed from the ingested Phase 1 data via `GET /api/indicators`:

**Temperature (NASA POWER T2M_MAX):**
- Hot days (>34°C): 61 of 1826 reported days (3.34%)

**Precipitation (NASA POWER PRECTOTCORR):**
- Total: 3,761.38 mm over 5 years
- Mean: 2.06 mm/day
- Wet days: 1,191 of 1,826 (65.22%)

**Soil texture (SSURGO first map unit/component/horizon):**
- Webster clay loam → Clay loam

**Crop diversity (CDL 2021–2025):**
- Diversity score: 70.92/100
- Dominant crop: Corn (43.79%)
- Distinct crops: 41
- Years represented: 5

---

## Phase 5 Rotation Recommendations — MCDA Scored

Four strategies scored across 6 axes using real data:

| Strategy | Sequence | Overall | Best Axis |
|----------|----------|---------|-----------|
| Climate-Hedged Cash + Forage | Sunflower, Alfalfa | 57.5 | Climate Resilience |
| County Baseline | Corn, Soybean | 49.6 | Market Return |
| Soil Armor & N-Builder | Corn, Cereal Rye, Crimson Clover | 49.6 | Erosion Armor |
| Water-Saver & Aquifer Shield | Sorghum, Chickpea | 44.6 | Water Efficiency |

All strategy cards include `why_suggested`, `nasa_evidence`, `agronomic_benefits`, `information_gaps`, and `risks_requiring_local_review`.
---

## Test Suite — 29 Tests Passing

| Test File | Tests | What It Covers |
|-----------|-------|----------------|
| `test_cdl.py` | 1 | CDL GetCDLStat JSON cache parsing |
| `test_nasa_power.py` | 1 | POWER daily response parsing, -999 → null |
| `test_usda_soil.py` | 1 | SSURGO SDA Table format parsing |
| `test_region_summary.py` | 2 | Schema round-trip, 503 when uningested |
| `test_wms.py` | 3 | WMS URL building, verified layer names |
| `test_indicators.py` | 8 | Hot days, precipitation, soil texture, crop diversity |
| `test_rotation.py` | 4 | Rotation engine: 4 strategies, 6 axes, sorting |

**Command:** `cd backend && python -m pytest -q` → `29 passed`

---

## Frontend Build

**Command:** `cd frontend && npm run build` → builds successfully (~7s)

**Verification:** Vite production build with TypeScript type-checking. All components type-safe against backend Pydantic schemas (Schema Lock Law enforced).

---

## Known Limitations (Documented, Not Hidden)

| Limitation | Cause | Mitigation |
|------------|-------|------------|
| County scope only | CDL is county-wide statistics | Explicit "county/regional scale only" labels |
| CDL AOI stats unavailable | GetCDLStat HTTP 500 for bbox params | County-level baseline only; blocker documented |
| NRCS WFS unreliable | 30s timeout | WMS map layer only; no spatial queries |
| No Landsat NDVI | ERS credentials needed + rasterio banned | M2M client ready; rasterio PROPOSED exception |
| No field-level data | No parcel/AOI source available | All recommendations carry limitations notice |

---

## Compliance with Roadmap Gates

- **Phase 1 DoD:** All 10 checklist items met (backend starts, frontend builds, ingestion works, raw files saved, processed JSON generated, API serves data, missing data = explicit 503, frontend displays real values, county scope identified, tests pass offline, smoke test performed)
- **Phase 2 DoD:** Real map with verified CDL + SSURGO WMS layers; county scope label; AOI blocker documented; stop condition honored
- **Phase 3 gate:** No `rasterio` import; no GeoTIFF parser; no NDVI computed; M2M client ready for when ERS credentials available
- **Phase 4 DoD:** All indicators computed from real ingested data; missing values = null
- **Phase 5 DoD:** 4 strategy cards with full explainability; transparent MCDA scoring; honest limitations