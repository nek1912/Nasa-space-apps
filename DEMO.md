# FieldShift — Hackathon Demo Script

## Overview

FieldShift is a geospatial decision-support web app for the 2026 NASA Space Apps Challenge. It fuses NASA, USDA, USGS, and ESA datasets to diagnose field vulnerabilities and recommend crop rotation strategies.

**Demo region:** Story County, Iowa (FIPS 19169)
**Data period:** 2021–2025
**Data sources:** USDA NASS CDL, USDA NRCS SSURGO, NASA POWER

---

## Pre-requisites

### 1. Backend data must be ingested

Run once to download real data from USDA/NASA services:

```bash
cd backend
pip install -r requirements.txt
python scripts/ingest_story_county.py
```

Expected output:
```
Ingestion complete
  cdl: ok
  ssurgo: ok
  nasa_power: ok
  data_status: ok
  processed -> backend/data/processed/story_county.json
```

### 2. Start the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Verify: `http://localhost:8000/health` returns `{"status": "healthy"}`

---

## Demo Walkthrough (5 minutes)

### Step 1: Region selection (30 seconds)

The dashboard opens on Story County, Iowa. The region label confirms county-level scope — not parcel- or field-level. This is intentional and honest: CDL statistics describe county-wide crop classification, not individual field history.

### Step 2: Map exploration (1 minute)

- **Base map:** OpenStreetMap centered on Story County reference point (42.03° N, -93.631° W)
- **CDL overlay:** Select a year (2021–2025) from the dropdown to see USDA NASS Cropland Data Layer crop classification. WMS layer verified against live CropScape GetCapabilities.
- **SSURGO overlay:** Toggle soil map units from USDA NRCS Soil Data Access WMS.

### Step 3: Data sources panel (30 seconds)

View provenance for each provider:
- USDA NASS — Cropland Data Layer county statistics
- USDA NRCS — SSURGO mapped soil survey data
- NASA POWER — Daily gridded meteorological data

Each source shows: provider, product, geographic scope, period, units, retrieval time, and status.
### 3. Start the frontend

### Step 4: Crop history chart (30 seconds)

Annual CDL classified acres for Story County, 2021–2025. Corn and soybeans dominate — typical for Iowa.

### Step 5: Soil profile table (30 seconds)

SSURGO map units with names, available water storage, and major components. First map unit: Webster clay loam (Clay loam texture class).

### Step 6: Weather chart (30 seconds)

NASA POWER monthly aggregates — precipitation totals and maximum temperature means. Derived only from returned daily values; missing days are excluded (not interpolated).

### Step 7: Rotation recommendations (1 minute)

Four MCDA-scored strategies:

| Strategy | Sequence | Overall Score |
|----------|----------|---------------|
| County Baseline | Corn, Soybean | ~49.6 |
| Climate-Hedged Cash + Forage | Sunflower, Alfalfa | ~57.5 |
| Soil Armor & N-Builder | Corn, Cereal Rye, Crimson Clover | ~49.6 |
| Water-Saver & Aquifer Shield | Sorghum, Chickpea | ~44.6 |

Each card shows:
- 6-axis radar chart (water efficiency, soil health, erosion armor, pest disruption, climate resilience, market return)
---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | GET | Health check |
| `GET /health` | GET | Health check |
| `GET /api/region-summary` | GET | Ingested CDL + SSURGO + NASA POWER data |
| `GET /api/layer-info` | GET | Verified WMS map layer metadata |
| `GET /api/indicators` | GET | Phase 4 indicators (hot days, precipitation, soil texture, crop diversity) |
| `GET /api/recommend-rotations` | GET | Phase 5 rotation recommendations (4 MCDA-scored strategies) |

---

## Test Suite

```bash
cd backend
pip install pytest
python -m pytest -q
```
---

## Evidence Trail

### Data provenance (all raw responses saved)

```
backend/data/raw/
  cdl/
    story_county_2021.json  (USDA NASS CDL GetCDLStat cache)
    story_county_2022.json
    story_county_2023.json
    story_county_2024.json
    story_county_2025.json
  ssurgo/
    story_county.json  (USDA NRCS SDA SQL response)
  nasa_power/
    story_county_daily_2021_2025.json  (NASA POWER daily point)
backend/data/processed/
  story_county.json  (normalized summary, 866 KB)
```

### Service verification documents

```
backend/docs/data/
  cdl_service_verification.md       (GetCapabilities + GetMap verified)
  ssurgo_service_verification.md    (WMS GetMap verified, WFS timed out)
  landsat_c2l2_api.md               (M2M API spec documented)
```

### Known limitations (documented, not hidden)

1. **CDL AOI statistics blocked:** GetCDLStat returns HTTP 500 for bbox/aoi/box parameters. API stays at county scope.
2. **NRCS WFS timed out:** SSURGO map units available via WMS only; spatial WFS query not reliable.
3. **No Landsat NDVI:** Phase 3 blocked — needs ERS MACHINE account approval + rasterio exception (PROPOSED, not active).
4. **County scope only:** No field-level data anywhere. All recommendations carry explicit limitations.

---

## Stop conditions honored

Per roadmap §16 and §17:
- AOI proof-of-concept stopped (CDL WFS blocked, NRCS WFS unreliable)
- No field-level data simulated
- No `rasterio` import (banned by RULES.md §5)
- No NDVI computed from raw pixels

---

## Hackathon talking points

1. **Real data, not placeholders:** Every value traces to USDA/NASA source responses. No synthetic data.
2. **Honest about limitations:** County scope acknowledged; AOI blocked; NDVI deferred.
3. **Transparent methodology:** MCDA weights, scoring rules, and data sources are all visible and documented.
4. **Farmer-first language:** Plain-language explanations with extension officer checklist on every strategy card.

Expected: `29 passed`

Tests cover:
- NASA POWER response parsing (units, missing values → null)
- CDL GetCDLStat parsing (acres, share percentages)
- SSURGO SDA parsing (map units, components, horizons)
- Region summary schema round-trip
- 503 when data not ingested (no placeholder data)
- WMS URL building (verified layer names, EPSG:4326)
- Rotation engine output (4 strategies, 6 axes each)
- Indicator computation (hot days, precipitation, soil texture, crop diversity)
- Why suggested / NASA evidence / agronomic benefits
- Information gaps / risks requiring local review

**Key message:** Recommendations are rule-based and evidence-supported, not field-validated. Consult a local extension officer before changing rotation.
```bash
cd frontend
npm install
npm run dev
```

Verify: `http://localhost:5173` loads the FieldShift dashboard