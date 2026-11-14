# FieldShift — Phase 1 Implementation Plan

**Phase:** Real-data working demo  
**Initial region:** Story County, Iowa, USA  
**Data period:** 2021–2025  
**Team:** 2 people working in parallel, with AI coding agents/subagents  
**Priority:** A small, working, verifiable data pipeline — not a startup platform

---

## 1. What this phase is for

### For a person

This phase makes FieldShift work with real agricultural and environmental data for one place: Story County, Iowa.

A user should be able to open the app and see:

- What crops USDA maps in the county over the last five years.
- What soil properties USDA's soil survey reports for the area.
- What historical temperature, rainfall, humidity, and solar-radiation data NASA reports for the county's reference location.
- Where each displayed value came from and what geographic area it actually represents.

The purpose is to prove that FieldShift can acquire real data, process it, send it through the backend, and display it in the frontend. It is not a polished commercial product, a global release, or a complete agronomy engine.

### For the AI agents working on the code

Build one complete, testable path:

`Official data sources → raw downloaded responses → normalized local data → FastAPI → React UI`

Every displayed scientific value must come from a real source response or a calculation based on that response. Keep the original response and its source metadata. Never replace missing data with invented values.

AI agents are implementation assistants, not sources of scientific truth. They must not invent API fields, crop observations, soil values, yields, confidence percentages, or successful test results.

## 2. Scope decision

The project keeps the **region-independent direction (Option B)**, but this phase implements only one region.

- The first configured region is Story County, Iowa.
- Source and location identifiers are kept in one small region configuration file rather than scattered through the code.
- Adding another region later should mainly require a new region configuration and checking that the relevant data providers cover it.
- Do not build a provider plugin system, generic geospatial framework, multi-country rule engine, database, cloud pipeline, authentication system, or agent orchestration framework in this phase.

### Important geographic honesty

The first data slice is **county-level/regional**, not parcel-level:

- CropScape CDL county statistics describe crop classification across Story County. They do not tell us the exact five-year crop sequence of an individual farm field.
- SSURGO reports mapped soil map units and their components. A county/survey-area summary is not a laboratory soil test for a specific field.
- NASA POWER is gridded meteorological data queried at a reference coordinate. It is regional weather context, not a farm weather station.

The UI and API must label these scopes accurately. Do not call county statistics “field history” or county soil summaries “the farmer's soil test.” Field-polygon analysis can be a later phase after the county-level data path works.

## 3. What is in and out of this phase

### Build now

1. Real USDA Cropland Data Layer (CDL) crop statistics for Story County, 2021–2025.
2. Real USDA NRCS SSURGO soil attributes for the Story County soil survey area.
3. Real NASA POWER daily historical weather data for a Story County reference coordinate, 2021–2025.
4. A small ingestion script that saves raw responses and produces one normalized JSON file.
5. FastAPI endpoints that read the processed local data.
6. A React page that displays the real crop, soil, and weather data with source labels.
7. Offline automated tests and a manual live-source smoke test.

### Do not build now

- All 26 datasets from the original concept.
- Landsat/Sentinel NDVI time series, ECOSTRESS, GPM IMERG, SMAP, GRACE, OpenET, PRISM, or USGS terrain processing.
- RUSLE or FAO-56 calculations that require inputs not yet acquired and validated.
- A 36-dekad phenology/stress timeline. Annual CDL classifications and daily POWER weather do not by themselves provide a measured dekadal NDVI curve.
- Market-return predictions, yield forecasts, irrigation predictions, or six-axis rotation scores. NASS yield and AMS price data are not part of this phase.
- Four attractive-looking rotation cards populated by assumptions or generated values.
- Runtime multi-agent systems, LangChain/CrewAI-style frameworks, or an LLM making numerical agronomic decisions.

A recommendation should only be shown when its inputs and rule are supported by the acquired data and clearly stated agronomic references. Otherwise show the measured data and state that the recommendation engine is not part of this phase. An honest missing feature is better than a fabricated result.

---

## 4. Real data sources and exact request starting points

Use these three sources only for this phase. These are service requests, not static files that already exist on disk. The ingestion script must make the requests and save the responses.

### A. USDA NASS — Cropland Data Layer via CropScape

**Purpose:** Annual crop/land-cover statistics for Story County.

- County FIPS: `19169` (Iowa `19` + Story County `169`).
- Years: `2021`, `2022`, `2023`, `2024`, `2025`.
- Format: JSON.
- Endpoint pattern:

```text
https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLStat?year=2025&fips=19169&format=json
```

Call once per year, changing `year` from 2021 through 2025. Save each response separately, for example:

```text
backend/data/raw/cdl/story_county_2021.json
backend/data/raw/cdl/story_county_2022.json
backend/data/raw/cdl/story_county_2023.json
backend/data/raw/cdl/story_county_2024.json
backend/data/raw/cdl/story_county_2025.json
```

Use crop acreage/share values returned by the service. Do not type crop percentages into the app. The CropScape service documentation includes `GetCDLStat` requests by year and FIPS, and also describes AOI/bounding-box options. The county request is the simplest reliable starting point.

For a map layer, first request the Iowa WMS capabilities document and inspect its actual layer names. Do not assume a layer name from an old example:

```text
https://nassgeodata.gmu.edu/CropScapeService/wms_cdl_ia.cgi?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities
```

**Display label:** `USDA NASS CDL — county crop statistics`.

### B. USDA NRCS — Soil Data Access (SSURGO)

**Purpose:** Real soil map-unit/component attributes for the Story County soil survey area.

- Service endpoint (POST):

```text
https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest
```

- Use the query service with `FORMAT=JSON+COLUMNNAME`.
- First verify the Story County survey-area symbol with a small query. `IA169` is the expected candidate, but confirm it against the live SDA result before saving it into the region configuration. A soil survey area is not guaranteed to match a county boundary exactly.

Area-symbol lookup query:

```sql
SELECT areasymbol, areaname
FROM legend
WHERE areasymbol LIKE 'IA%'
  AND areaname LIKE '%Story%'
```

After confirming the area symbol, query only the required fields. A starting query is:

```sql
SELECT
    l.areasymbol,
    mu.mukey,
    mu.musym,
    mu.muname,
    c.compname,
    c.comppct_r,
    ch.hzdept_r,
    ch.hzdepb_r,
    ch.sandtotal_r,
    ch.silttotal_r,
    ch.claytotal_r,
    ma.aws025wta
FROM legend l
JOIN mapunit mu ON mu.lkey = l.lkey
JOIN component c ON c.mukey = mu.mukey
LEFT JOIN chorizon ch ON ch.cokey = c.cokey
LEFT JOIN muaggatt ma ON ma.mukey = mu.mukey
WHERE l.areasymbol = 'IA169'
  AND c.majcompflag = 'yes'
ORDER BY mu.musym, c.comppct_r DESC, ch.hzdept_r
```

Send the SQL as a form-encoded POST body with:

```text
SERVICE=query
REQUEST=query
FORMAT=JSON+COLUMNNAME
QUERY=<SQL above>
```

Save the unmodified response to:

```text
backend/data/raw/ssurgo/story_county.json
```

The query returns components and horizons, so repeated map-unit rows are expected. Preserve the raw rows. For the UI summary, group by map unit and show the dominant components and available-water-storage attribute where the source returns it. Do not average soil values without a documented aggregation method.

**Display label:** `USDA NRCS SSURGO — mapped soil survey data`.

### C. NASA POWER — Daily point weather data

**Purpose:** Real historical daily weather for the Story County reference location.

- Reference latitude: `42.030`
- Reference longitude: `-93.631`
- Dates: `2021-01-01` through `2025-12-31`
- Parameters: `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `RH2M`, `ALLSKY_SFC_SW_DWN`
- Community: `AG`
- Time standard: `UTC`
- Format: JSON

Exact request:

```text
https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,ALLSKY_SFC_SW_DWN&community=AG&longitude=-93.631&latitude=42.030&start=20210101&end=20251231&format=JSON&time-standard=UTC
```

Save the raw response to:

```text
backend/data/raw/nasa_power/story_county_daily_2021_2025.json
```

Normalize dates and units explicitly. Record the parameter units from the API response/metadata; do not assume all source parameters use the same units. Treat this as gridded regional context, not field sensor data.

**Display label:** `NASA POWER — daily gridded weather at Story County reference point`.

---

## 5. Minimal repository changes

The existing repository is a useful starting scaffold. Keep its overall `backend/` and `frontend/` split. Do not redesign the project into a new architecture.

### Backend — expected additions/changes

```text
backend/
├── app/
│   ├── main.py                         # Fix app startup; register routers
│   ├── schemas.py                      # Real-data response contracts
│   ├── api/
│   │   └── routes_field.py             # Read region summary
│   └── services/
│       ├── nasa_power.py               # Replace placeholder with real POWER request/parser
│       ├── cdl.py                      # New: CropScape CDL statistics request/parser
│       └── usda_soil.py                # Replace hardcoded soil response with SDA request/parser
├── config/
│   └── region.json                     # One active region; IDs/coordinates/date range
├── data/
│   ├── raw/
│   │   ├── cdl/
│   │   ├── ssurgo/
│   │   └── nasa_power/
│   └── processed/
│       └── story_county.json           # Normalized output consumed by the API
├── scripts/
│   └── ingest_story_county.py          # One command to download and normalize all three sources
└── tests/
    ├── test_nasa_power.py
    ├── test_cdl.py
    ├── test_usda_soil.py
    └── test_region_summary.py
```

Use the existing `terrain_water.py`, `si_diagnostics.py`, and `rotation_engine.py` only if a real supported calculation is added. Do not force them into the first demo merely because those files exist.

The region configuration should contain only what this implementation needs, for example:

```json
{
  "region_id": "us-ia-story",
  "country": "USA",
  "state": "Iowa",
  "county": "Story",
  "county_fips": "19169",
  "soil_survey_area": "IA169",
  "latitude": 42.03,
  "longitude": -93.631,
  "start_date": "2021-01-01",
  "end_date": "2025-12-31"
}
```

Set `soil_survey_area` only after the SDA lookup confirms it. Do not add a generic region registry or dozens of configurable provider fields.

### Frontend — expected changes

```text
frontend/
├── index.html                         # Add Vite HTML entry if absent
└── src/
    ├── main.tsx                       # Add React entry if absent
    ├── App.tsx                        # Real-data Story County dashboard
    ├── api/client.ts                  # Use configured API base URL
    ├── types/fieldshift.ts            # Exact mirror of backend response types
    ├── config/mapLayers.ts            # Keep only verified layer definitions
    └── components/
        ├── FarmSelectorBar.tsx        # Replace 3-farm selector with single-region label
        ├── FieldMapCanvas.tsx         # Story County map and verified CDL layer, if available
        ├── CropHistoryChart.tsx       # New: annual CDL statistics
        ├── SoilSummary.tsx            # New or reuse a simple component for SSURGO results
        ├── WeatherChart.tsx           # New: NASA POWER monthly aggregation
        └── DataSourcesPanel.tsx       # New: source, date range, scope, retrieval status
```

The exact component names may follow the existing style. The important requirement is that the screen displays actual API data, not hardcoded chart arrays.

### One backend/frontend contract

Agree on the response shape before both people implement against it. Keep it small. A single `GET /api/region-summary` endpoint is sufficient for this phase. It should return:

- Region identity and geographic scope.
- CDL annual crop statistics for 2021–2025.
- SSURGO soil map-unit/component summary.
- NASA POWER daily data or monthly aggregates derived from the raw daily data.
- Per-source metadata: provider/product, retrieval time, source geography, date range, and units.

The backend `schemas.py` and frontend `types/fieldshift.ts` must match. The frontend must not create its own alternative field names. If the contract changes, both owners update and review the two files together.

---

## 6. Person 1 — Backend, data pipeline, and AI-agent lead

**Owns:** `backend/`, the data contract, and backend-related documentation changes.  
**Main result:** One command downloads three real sources and creates the JSON the frontend can consume.

### Task 1 — Fix the existing backend startup blockers

Before adding data features:

- Fix the syntax error in the request logging middleware (`start time` must be a valid variable name and used consistently).
- Make `/` and `/health` actually return their response objects.
- Register the existing routers with the FastAPI app.
- Check CORS against Vite's actual development origin (`http://localhost:5173` unless changed).
- Keep the current FastAPI stack; do not add a database or a new framework.

**Expected result:** FastAPI imports and starts; `/health` returns a real HTTP response; route documentation shows the registered endpoints.

**Test:**

```bash
cd backend
python -m compileall app
uvicorn app.main:app --reload --port 8000
```

Then open `http://localhost:8000/health` and `http://localhost:8000/api/docs`.

### Task 2 — Implement the three source integrations

Work in the existing service modules where appropriate. Add only the new CDL service file.

For each source:

1. Make the documented request.
2. Check the HTTP status and response shape.
3. Save the original response without modifying it.
4. Parse only the fields the Phase 1 UI needs.
5. Record source name, product, request location, date range, retrieval timestamp, and units.
6. Raise/report a clear source error if the request fails. Do not return a made-up fallback value.

Use reasonable finite timeouts for the **ingestion script**. Do not run a five-year download inside a UI request. The API should read the locally processed JSON and remain fast.

### Task 3 — Build one ingestion command

Implement:

```bash
cd backend
python scripts/ingest_story_county.py
```

The script should:

- Read the single active region configuration.
- Download CDL statistics for 2021–2025.
- Verify the Story County SSURGO survey-area symbol and download the required soil rows.
- Download NASA POWER daily data for the configured point and date range.
- Save each raw response under `data/raw/`.
- Normalize the information into `data/processed/story_county.json`.
- Print a compact success/failure summary for the three providers.

Rerunning the command should replace/update the same region files, not append duplicate observations.

### Task 4 — Implement only calculations supported by these data

Allowed for Phase 1:

- Annual county crop shares/acreage from CDL.
- Monthly precipitation and temperature summaries derived from daily POWER data.
- Soil map-unit/component display from SSURGO.

Do not call these values field-level. Do not infer a same-field crop rotation from county-wide annual crop shares. Do not calculate erosion, evapotranspiration, irrigation demand, yield, profitability, or confidence scores without the necessary measured inputs and a documented formula.

If a small recommendation is required for the demo, it must be a transparent rule using actual returned values, with its evidence and geographic limitation included in the API response. Do not use an LLM to invent the recommendation or its score.

### Task 5 — Make the API data-only and predictable

The API should read the processed local file. If it does not exist, return a clear `503`/data-not-ingested response. If a source is missing, identify that source as unavailable and do not fabricate its values.

Remove placeholder behaviour from `nasa_power.py`, `usda_soil.py`, `terrain_water.py`, and any route that returns fake success. A last-known-good cache is acceptable only when it contains a previously downloaded real response and the API marks it as stale with its retrieval date.

**Expected result:** `GET /api/region-summary` returns the processed real dataset and provenance metadata.

### Task 6 — Tests

Add tests for:

- NASA POWER response parsing, dates, units, and missing-value handling.
- CropScape response parsing and year/county identification.
- SSURGO row parsing and map-unit grouping.
- Missing raw/processed data: API reports unavailable instead of returning a placeholder.
- Region summary schema and provenance metadata.

Normal automated tests must run without network access. Use small test-only response fixtures for parser tests; never bundle those fixtures into the application or display them in the demo.

**Commands:**

```bash
cd backend
python -m pytest -q
python -m compileall app scripts
```

Add `pytest` to the development/test dependencies if it is not already installed.

---

## 7. Person 2 — Frontend and demo experience lead

**Owns:** `frontend/`.  
**Main result:** A working page that displays the backend's real Story County data and clearly identifies its source and scope.

### Task 1 — Make the current frontend boot

The current `App.tsx` has invalid/missing component imports, and the repository tree does not currently contain `frontend/index.html` or `frontend/src/main.tsx`. Add the minimum Vite entry files and fix the imports. Do not redesign the application structure.

**Test:**

```bash
cd frontend
npm install
npm run build
```

### Task 2 — Remove fake demo UI

- Replace the three-farm selector with a single `Story County, Iowa` region label.
- Remove hardcoded farm area, crop, soil, yield, and uncertainty values.
- Do not use a fixed uncertainty badge such as `0.45`.
- Do not show placeholder charts or static crop-history arrays.
- Hide unfinished sliders and recommendation cards rather than displaying fake results.

### Task 3 — Build the real-data dashboard

Show these sections:

1. **Region:** Story County, Iowa; state and county identifiers; note that this phase is county/regional level.
2. **Crop history:** annual CDL crop statistics, 2021–2025. Use values returned by the backend.
3. **Soil profile:** SSURGO map units, components, texture/horizon attributes, and available-water storage where present.
4. **Weather:** NASA POWER monthly precipitation and temperature summaries computed from the daily source data.
5. **Sources and coverage:** provider/product, retrieval time, period, units, and geographic scale.

A MapLibre map can show Story County and the verified Iowa CDL WMS layer. First verify the WMS capabilities and layer identifier. If the layer cannot be loaded reliably, show the map location and a clear “CDL map overlay unavailable” state; do not substitute an unrelated or fake layer.

### Task 4 — Connect to the backend contract

- Use the agreed `GET /api/region-summary` response.
- Keep frontend TypeScript definitions in sync with backend Pydantic schemas.
- Read the API base from `VITE_API_BASE_URL`, with `http://localhost:8000/api` as the development default.
- Show loading, source-unavailable, stale-cache, and request-error states.
- Do not create local mock data to make charts appear populated while the backend is incomplete.

### Task 5 — Verify the demo

**Commands:**

```bash
cd frontend
npm run build
npm run dev
```

With the backend running and real data ingested, verify:

- The page loads with Story County as the only active region.
- Crop, soil, and weather values match the backend response.
- Source labels and units are visible.
- Missing data is shown as unavailable, not as zero or a default number.
- The UI does not claim field-level precision.
- The app remains usable if one source is unavailable.

---

## 8. How both people work in parallel

### First shared checkpoint — before coding

Spend a short joint session agreeing on only these items:

1. Story County, Iowa is the only active region in this phase.
2. Data years are 2021–2025.
3. The three providers are CDL, SSURGO, and NASA POWER.
4. The response contract for `GET /api/region-summary` is fixed.
5. Backend owner owns Pydantic schemas; frontend owner mirrors them in TypeScript.
6. No synthetic application data or placeholder success responses.

After this checkpoint, work can proceed in parallel.

### Parallel work split

| Person 1 — Backend/data/AI | Person 2 — Frontend |
|---|---|
| Fix FastAPI startup and route registration. | Fix Vite entry files and React imports. |
| Verify the official source requests. | Build the single-region dashboard layout. |
| Implement NASA POWER, CDL, and SSURGO ingestion. | Create crop, soil, weather, and source-status components. |
| Build raw-to-processed data script. | Connect the agreed API client and types. |
| Define and implement the backend response schema. | Mirror the schema; do not independently rename fields. |
| Add parsing, data-contract, and API tests. | Add loading, unavailable, and stale-data states. |
| Run real-source ingestion and verify provenance. | Run the UI against the real API response and verify displayed values. |

### Integration checkpoints

- **Checkpoint 1:** The response contract is agreed. Frontend can develop against types and empty/loading/error states without fake data.
- **Checkpoint 2:** Backend has one successful real source response and the raw-file format is stable. Frontend can connect the first section.
- **Checkpoint 3:** All three raw source responses and `story_county.json` exist. Frontend connects the remaining sections.
- **Checkpoint 4:** Both owners run the complete local demo from a clean checkout and verify the visible figures against the processed JSON.

Avoid having two people or two subagents edit the same schema, route, or component simultaneously. The owner of a file makes the change; the other person reviews it.

---

## 9. AI and subagent working rules

Use AI agents to accelerate bounded tasks, not to create a complex agent platform.

### Backend subagents

Person 1 may delegate three isolated tasks:

- **CDL agent:** inspect the CropScape documentation, implement only `cdl.py` and its parser tests.
- **POWER agent:** implement only the NASA POWER request/parser and its tests.
- **SSURGO agent:** implement only the SDA request/parser and its tests.

Person 1 remains responsible for the shared ingestion script, schemas, integration, and scientific correctness.

### Frontend subagents

Person 2 may delegate a component implementation or a review pass, but should retain ownership of `App.tsx`, API integration, and the final user flow.

### Rules for every coding agent

Every task prompt must include:

- The exact goal and acceptance check.
- The allowed files to edit.
- The relevant existing project instructions (`RULES.md`, `ARCHITECTURE.md`, `DECISIONS.md`, and `PRD.md`).
- The requirement to use real source responses and preserve provenance.
- A requirement to report changed files, tests actually run, and remaining limitations.

Agents must not:

- Invent endpoints, response fields, or source values.
- generate demo observations or fake data to make the UI look complete.
- Modify files outside their ownership without approval.
- Change the backend schema without notifying the frontend owner.
- Claim a command or test passed unless it was actually run.
- Add dependencies or architecture layers without showing why the existing stack cannot solve the task.

No runtime LLM or multi-agent framework is required for this phase. The app's first trustworthy result should come from real source data and deterministic transformations. A grounded natural-language explanation can be added later, after the data contract and diagnostics are stable.

---

## 10. Two-day execution order

### Day 1 — Make the data path real

**Joint start:** freeze region, time range, sources, and response contract.

**Person 1:** fix backend startup; verify and implement the three source requests; get raw JSON files saved; build the first version of the ingestion script.

**Person 2:** make Vite/React boot; remove fake farm UI; build the single-region dashboard layout and components using the agreed TypeScript contract; add loading/error states.

**End-of-day check:** at least one provider has been downloaded successfully and can be read from disk by the backend. The frontend builds and calls the agreed endpoint without displaying mock values.

### Day 2 — Complete and verify the vertical slice

**Person 1:** complete the remaining source integrations; normalize all three sources; write processed JSON; finish parsing and API tests; verify the live ingestion command.

**Person 2:** connect the actual response; finish charts/tables/source labels; verify the map layer if time permits; test missing/stale source states.

**Joint finish:** start backend, run ingestion, start frontend, and demonstrate the complete data path. Record exactly which source integrations succeeded and which failed; do not hide a failure with hardcoded output.

If one provider takes too long to integrate, keep it explicitly unavailable and finish the working path for the other real sources. Do not replace it with synthetic data.

---

## 11. Definition of done

The phase is complete only when all applicable checks below pass:

- [ ] The backend starts without syntax/import errors.
- [ ] The frontend builds and starts.
- [ ] The ingestion command requests real CDL, SSURGO, and NASA POWER data.
- [ ] Original source responses are saved under `backend/data/raw/`.
- [ ] A normalized `backend/data/processed/story_county.json` is generated.
- [ ] Processed values can be traced to their provider, product, period, units, and retrieval time.
- [ ] The API serves the processed data without requesting external providers on every page load.
- [ ] Missing data returns an explicit unavailable/error state, not placeholder values.
- [ ] The frontend displays the actual returned crop, soil, and weather values.
- [ ] County/regional resolution is clearly identified in the UI.
- [ ] Automated tests pass without network access.
- [ ] A manual live-source smoke test has been performed and its result recorded.
- [ ] The demo can be started using the commands below from a clean checkout.

### Local run commands

Backend:

```bash
cd backend
python -m venv .venv
# Activate the virtual environment for your operating system
pip install -r requirements.txt
python scripts/ingest_story_county.py
python -m pytest -q
uvicorn app.main:app --reload --port 8000
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run build
npm run dev
```

---

## 12. Existing repository issues that must be accounted for

This plan is based on the repository's current `main` branch structure and file contents, not on the intended architecture alone.

1. **`backend/app/main.py` currently has a syntax error** in the request logger (`start time = time.time()`). The root and health handlers also construct dictionaries without returning them. The field and recommendation routers are not registered in the app.
2. **The backend routes are placeholders.** `/api/hero-farms` returns an empty list; analysis and recommendation routes return empty structures.
3. **The data services are not real integrations yet.** `nasa_power.py` uses a placeholder endpoint/fixed values on failure; `usda_soil.py` and `terrain_water.py` return hardcoded soil/terrain values.
4. **`seed_static_data.py` creates synthetic hero-farm/yield records.** `hero_farms.json` and `nass_county_baselines.csv` contain example values, not verified real observations. Do not use or seed these files for the demo. Remove them from the runtime data path; retain test-only fixtures only where needed for automated parser tests.
5. **The current frontend is mostly placeholder UI.** Components display explanatory text rather than data. `App.tsx` has missing/invalid imports. `frontend/index.html` and `frontend/src/main.tsx` are absent from the current repository tree.
6. **The frontend client and backend contract do not currently agree.** For example, the client sends `farmId`, while the backend schema uses `farm_id`; the returned recommendation types are also inconsistent. Replace this with the single Phase 1 summary contract.
7. **The current product documents overstate the Phase 1 scope.** `PRD.md` refers to three farms in three states, a multi-axis rotation score, market return, and inputs from sources that are not implemented. `ARCHITECTURE.md` describes 26 datasets and pre-harmonized time-series cubes that are not present in the repository. Mark those as later-phase goals; do not attempt to implement them now.
8. **`DECISIONS.md` describes a benchmark fallback.** A fabricated benchmark fallback conflicts with the real-data requirement. Change the rule to use only a previously downloaded real response, marked stale, or return an explicit unavailable response.

Do not refactor unrelated code while fixing these blockers. Each edit should support the Phase 1 acceptance criteria.

---

## 13. Source references

- [NASA POWER Daily API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) — request structure, time standards, formats, and daily data availability.
- [NASA POWER parameter documentation](https://power.larc.nasa.gov/docs/services/api/) — available meteorological parameters.
- [USDA NASS Cropland Data Layer release page](https://www.nass.usda.gov/Research_and_Science/Cropland/Release/index.php) — annual CDL releases and downloads.
- [USDA NASS CDL description and metadata](https://www.nass.usda.gov/Research_and_Science/Cropland/sarsfaqs2.php) — annual crop classification, spatial resolution, and geographic coverage.
- [CropScape Web Service documentation](https://nassgeodata.gmu.edu/CropScape/devhelp/getexamples.html) — `GetCDLStat`, `GetCDLFile`, `GetCDLValue`, and AOI request examples.
- [CropScape Iowa WMS documentation](https://nassgeodata.gmu.edu/CropScape/devhelp/cdlwms.html) — Iowa WMS/WCS request patterns.
- [USDA NRCS Soil Data Access Web Service Help](https://sdmdataaccess.nrcs.usda.gov/WebServiceHelp.aspx) — POST query service, JSON output formats, and AOI capabilities.
- [USDA NRCS Soil Data Access Query Help](https://sdmdataaccess.nrcs.usda.gov/QueryHelp.aspx) — SQL query examples and recommended SSURGO joins.
- [USDA NRCS SSURGO overview](https://www.nrcs.usda.gov/resources/data-and-reports/soil-survey-geographic-database-ssurgo) — mapped soil units, components, and reported soil properties.


---

# Part II — Remaining implementation roadmap (after Phase 1)

**Read this only after the Phase 1 Definition of Done passes.** These phases are deliberately gated. Do not start Phase 3 while Phase 2's data path is still unreliable, and do not build a recommendation engine around data that has not been acquired and checked.

## 14. Complete project roadmap at a glance

| Phase | Purpose | Main deliverable | Priority |
|---|---|---|---|
| 1 | Prove real data acquisition and display | Story County dashboard using CDL, SSURGO, and NASA POWER | Required first |
| 2 | Make the data spatially understandable | Real county map layers and a verified Area of Interest (AOI) workflow if the source APIs support it | Required next |
| 3 | Add actual satellite vegetation evidence | A small, quality-screened Landsat NDVI time series for the selected AOI | High value; gated by raster-processing proof |
| 4 | Turn observations into defensible indicators | A small set of transparent crop, weather, soil, and vegetation indicators | Required before recommendations |
| 5 | Produce explainable crop-rotation options | Baseline plus a small number of evidence-backed alternatives | Only after required inputs exist |
| 6 | Integrate, validate, and prepare the hackathon demo | Stable end-to-end demo, tests, evidence trail, and demo script | Required final phase |
| 7 | Post-hackathon expansion | Add another region or source only when there is a clear use case | Not part of the hackathon build |

The end goal is a credible agricultural decision-support demo, not a global product. The app should become more useful phase by phase without introducing databases, cloud orchestration, accounts, microservices, or a runtime agent framework.

## 15. Important corrections to the existing PRD before later phases

The current `PRD.md` is an ambition document, not proof that the required data or scientific methods are ready. Keep it, but annotate these items as deferred until the relevant phase passes its data and science checks.

1. **Three hero farms:** Do not restore Finney County, Story County, and Fresno County merely to make the selector look complete. The initial demo is Story County only. A second region is a later portability test, not a Phase 2 task.
2. **Field history:** County-level CDL statistics do not reveal a particular field's crop sequence. A baseline rotation can only be created after a real field/AOI crop-history query succeeds.
3. **36 dekads:** Do not create 36 populated timeline points by interpolating daily weather or annual CDL values. Observations must be aggregated into a time bin only when the source has actual observations for that bin. Missing bins remain missing.
4. **RUSLE:** The current PRD's simplified expression using precipitation total, a soil factor, a slope expression, and NDVI is not automatically a validated RUSLE calculation. Do not label it `RUSLE` or an erosion-risk score until the R, K, LS, C, and P inputs, units, temporal aggregation, and method are sourced and checked. A simpler bare-soil/rainfall/slope exposure flag may be shown as a screening indicator, with that label and limitation.
5. **Heat stress:** A single `34 °C` threshold is not a universal crop stress threshold. Without crop identity and growth-stage information, show observed hot-day counts or temperature exposure, not a claim that the crop experienced physiological heat stress.
6. **Evaporative stress:** Temperature and relative humidity alone do not provide actual evapotranspiration or an Evaporative Stress Index. Do not calculate `ESI` from those two variables.
7. **Confidence:** Remove the fixed `92%` base confidence and fixed confidence bonuses. Until there is a calibrated validation method, show data completeness, source coverage, cloud/missing-data percentage, and known limitations instead of a fabricated confidence percentage.
8. **Market return:** County yield multiplied by a price is not farm profit. A return estimate also needs a valid crop-area basis, price period, input costs, and a clear geographic scope. Keep market-return ranking out of the initial hackathon demo.
9. **Four rotation cards:** Four cards are a UI requirement only if four evidence-backed strategies can actually be built. Never fill a quota with assumed values. It is acceptable to show one measured baseline and two supported alternatives.
10. **SMAP and other coarse products:** SMAP L4 is a 9 km, 3-hourly root-zone/surface soil-moisture product; it is regional context, not a field sensor. GPM IMERG is a 0.1° half-hourly precipitation product; it is also regional context. Neither should be represented as sub-field measurements. See the official product descriptions in Section 22.

These corrections are not scope reduction for its own sake. They prevent a judge or agronomist from finding that a polished chart is based on unsupported values.

---

## 16. Phase 2 — Map the real data and prove one spatial AOI

### What this phase is for

**For a person:** Phase 1 tells the user what the data says about Story County as a whole. Phase 2 puts that information on a map so the user can see where crop and soil patterns occur. It also investigates whether a user-selected area can be queried reliably. The map must show actual source layers, not decorative map colours.

**For AI coding agents:** Add a real geospatial viewing path and perform a small AOI proof-of-concept. Do not build a generic GIS system. First verify the exact source request and coordinate system; then implement only the path that works.

### Build

1. Show a Story County boundary and a verified base map.
2. Add a USDA CDL map layer with a year selector. Use the official CropScape layer/service only after checking its current `GetCapabilities` response and confirming the layer name, coordinate system, and tile request format.
3. Add an optional SSURGO map layer if the official WMS/WFS can be loaded reliably. The table summary from Phase 1 remains available even if the map overlay fails.
4. Add a legend, selected year, source name, product, and geographic resolution/scope. Make clear that CDL is a crop classification product and SSURGO is mapped soil survey data.
5. Run a **time-boxed AOI proof-of-concept**: take one real user-supplied polygon or a documented test AOI, request CDL statistics for it, and request intersecting SSURGO map units. CropScape documents statistics requests by county, bounding box, points, and vector-AOI URL. NRCS documents spatial WFS services with spatial filters. Verify the actual requests before designing the UI around them.
6. Only if the AOI proof works, add a simple draw/upload/select-one-area control. Do not support multiple farms, editing history, accounts, or saved projects.

### Person 1 — Backend/data owner

- Inspect the current CropScape and NRCS service capabilities and save the exact successful request/response examples in `docs/data/` or the existing documentation location.
- Verify the coordinate reference system expected by each service. Do not assume that longitude/latitude can be sent to a service that expects projected coordinates.
- Implement one CDL map/statistics request path and one SSURGO spatial query path only after the proof-of-concept succeeds.
- If the AOI request requires a vector format, implement only the minimum conversion needed for the supported source request. Do not create a general geometry-conversion package.
- Add `aoi_id`, geometry source, geometry CRS, and AOI area to the response. Preserve the original geometry and source request metadata.
- If no reliable AOI request can be completed within the time box, keep the API at Story County scope and record the blocker. Do not simulate field-level data.

**Likely files:** existing `backend/app/services/cdl.py`, `backend/app/services/usda_soil.py`, `backend/app/api/routes_field.py`, `backend/app/schemas.py`, plus a small AOI utility only if necessary. Keep the Phase 1 ingestion script working.

### Person 2 — Frontend owner

- Replace the placeholder map with a real map centered on Story County.
- Add the real CDL overlay and year selector; add SSURGO overlay only if its service is verified.
- Display layer loading/error states and the data source/legend.
- Add one AOI interaction only after the backend has returned a successful real AOI response. Until then, do not show a fake “selected field analysis” panel.
- Show a visible scope label: `County-level` or `Selected AOI`, according to the actual API response.

**Likely files:** `frontend/src/components/FieldMapCanvas.tsx`, `frontend/src/config/mapLayers.ts`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/types/fieldshift.ts`.

### AI/subagent split

- **Map-service research agent:** inspect official CropScape and NRCS capabilities; return exact working request URLs, required CRS, supported formats, and one response example. No code changes.
- **CDL implementation agent:** edit only the CDL service and parser tests.
- **SSURGO implementation agent:** edit only the SSURGO spatial service and parser tests.
- **Frontend map agent:** edit only map components/config after the backend layer contract is agreed.
- Person 1 owns the contract and integration. Person 2 owns the map user experience.

### Expected result

The user can select a CDL year and see the real Story County crop classification layer. Soil map units are visible if the verified SSURGO spatial layer works. A single AOI can be queried only if the end-to-end proof succeeds.

### Tests and acceptance

```bash
cd backend
python -m pytest -q
python -m compileall app scripts

cd ../frontend
npm run build
```

Manual checks:

- [ ] The map extent matches Story County.
- [ ] Every enabled map layer comes from a verified service response.
- [ ] Changing the year changes the CDL layer, not just its label.
- [ ] Legend values and source labels match the layer.
- [ ] Layer failure produces a visible error state, not a fake layer.
- [ ] If AOI is enabled, CDL/soil statistics are returned for that AOI and its geometry/CRS are recorded.
- [ ] If AOI fails, the app remains explicitly county-level.

**Stop condition:** If the AOI proof is blocked by geometry conversion, access, or source behaviour, stop the AOI feature. Finish the county map and proceed with county-level analysis. Do not consume the hackathon schedule building a GIS subsystem.

---

## 17. Phase 3 — Add a real satellite vegetation time series

### What this phase is for

**For a person:** The app currently knows the crops mapped by USDA and the historical weather reported by NASA. This phase adds evidence about how green or vegetated the land appeared in actual satellite observations over time. It lets the app distinguish a measured satellite observation from a weather-based assumption.

**For AI coding agents:** Acquire a small set of real Landsat scenes, apply documented reflectance scaling and quality masking, calculate NDVI, and store date-stamped measurements. This phase is not complete because a satellite image appears on the map; actual pixel values must be processed and tested.

### Data choice

Use **Landsat 8/9 Collection 2 Level-2 Surface Reflectance** as the first and only quantitative vegetation source. USGS documents 30 m surface-reflectance products, global scene coverage, and the Collection 2 scale factor `SR = DN × 0.0000275 − 0.2`. Use the product guide to apply the correct quality mask and scale factors.

Keep the initial sample small:

- One Story County test AOI, preferably the AOI proven in Phase 2.
- One complete crop season, such as April–October 2025, or the latest complete season with enough usable scenes.
- A small number of usable Landsat 8/9 scenes, selected by date and location; cloud-cover metadata is only a first filter, not a substitute for pixel-level QA.
- Keep each scene's acquisition date, product ID, processing level, cloud/QA information, bands, scaling factors, and download provenance.

Do not download the full national archive or every scene from 2013 onward.

### Important implementation gate: raster processing

The current `RULES.md` and `DECISIONS.md` ban `rasterio`, GDAL, and other native raster libraries. That restriction conflicts with computing NDVI from downloaded Landsat GeoTIFF pixels.

Before implementing this phase, Person 1 must perform a small technical spike using one real Landsat scene and report one of these two outcomes:

- **Option A:** a minimal offline preprocessing script can read the GeoTIFF, apply QA/scaling, calculate NDVI, and produce a small AOI summary. If this requires `rasterio`, propose a narrowly scoped exception for the preprocessing script only, test installation on the team's machines, and update `RULES.md`/`DECISIONS.md` explicitly before using it.
- **Option B:** a verified external processing service returns the needed AOI/time-series values with traceable inputs and documented processing. Use it only if the team can query it reliably and reproduce the result.

Do not hand-write a GeoTIFF parser and do not silently violate the current dependency ban. If neither option is reliable, defer quantitative NDVI. The app may display a verified satellite image layer for context, but it must not show computed NDVI values.

### Person 1 — Backend/data owner

- Search and select a small set of Landsat 8/9 Collection 2 Level-2 scenes for the test area and season.
- Implement the approved raster-processing path as an offline script, not inside a user-facing API request.
- Apply the official scale factors and mask cloud, cloud shadow, snow, fill, and other invalid pixels using the product QA band.
- Calculate NDVI from red and near-infrared reflectance: `(NIR - Red) / (NIR + Red)`. For Landsat 8/9 OLI, use the documented red and NIR bands from the product guide; do not infer band IDs from another sensor.
- Aggregate valid pixels over the AOI into a date-stamped statistic (for example median and valid-pixel count). Keep cloud/invalid pixel proportion so the frontend can expose data quality.
- Save raw scene metadata and derived summaries separately. Do not commit large scene files to Git; add download manifests and small processed results instead.
- Preserve gaps. Do not fill cloudy dates with interpolated NDVI and do not create a smooth curve where observations do not exist.

**Likely files:** `backend/scripts/process_landsat.py`, `backend/data/raw/landsat/` (ignored from Git), `backend/data/processed/landsat_ndvi.json`, one small service/parser, and focused tests.

### Person 2 — Frontend owner

- Add a vegetation timeline showing the actual acquisition dates.
- Plot median NDVI and valid-pixel coverage; distinguish missing/cloudy observations from zero vegetation.
- Display the scene date, spatial resolution (30 m), source/product, and AOI scope.
- If a satellite image map layer is available, make it a separate visual layer from the derived NDVI chart. Do not imply that a rendered image is the numeric source of the chart unless it is.
- Do not create a 36-dekad chart by filling gaps. Show the actual number and timing of usable observations.

**Likely files:** new `VegetationTimeline.tsx`, `FieldMapCanvas.tsx`, `App.tsx`, API client, and TypeScript contract.

### AI/subagent split

- **Landsat research agent:** identify exact Collection 2 products, QA bands/bit flags, scaling, and scene IDs. Return links and documentation; do not write processing code.
- **Raster spike agent:** use one real scene to prove the approved processing path; report install commands and output values.
- **NDVI test agent:** write tests for scaling, masking, NDVI range, zero denominators, and no-valid-pixel scenes.
- **Timeline agent:** implement only the chart using the agreed backend response.

### Expected result

At least several real, QA-screened date observations for one season/AOI, each traceable to a Landsat scene. If the raster-processing gate fails, this phase is explicitly deferred and Phase 4 must not depend on NDVI.

### Tests and acceptance

Backend tests should verify:

- [ ] A known pair of scaled red/NIR values produces the expected NDVI.
- [ ] Cloud/shadow/fill pixels are excluded.
- [ ] NDVI values are bounded between -1 and +1 for valid inputs.
- [ ] Zero denominator and no-valid-pixel cases are handled as missing, not zero.
- [ ] AOI summary records valid-pixel count and data-quality fraction.
- [ ] Re-running processing for the same scenes does not duplicate observations.

Frontend checks:

- [ ] Timeline dates match the processed JSON exactly.
- [ ] Missing dates are displayed as gaps.
- [ ] Chart labels state NDVI, units (dimensionless), source, resolution, and AOI.
- [ ] The UI does not display NDVI when the raster-processing gate has not passed.

---

## 18. Phase 4 — Build a small evidence-based diagnostic layer

### What this phase is for

**For a person:** Raw data is useful, but users need help understanding what it may indicate. This phase turns observations into a few carefully labelled indicators. It does not claim to diagnose every farm problem or predict yield.

**For AI coding agents:** Implement small deterministic calculations with tests, explicit units, and source provenance. Every indicator must say which observations and assumptions it uses. No black-box numerical generation.

### Build only indicators with valid inputs

Start with the following, and add no others until they pass the data/method gate:

1. **Crop composition/history:** report CDL class and area/share for the actual geographic scope and years available. Call it a field crop sequence only if a field AOI history was actually queried.
2. **Weather exposure:** derive monthly/seasonal precipitation summaries and counts of days exceeding clearly stated temperature thresholds from NASA POWER. Until crop stage and a crop-specific threshold are available, call these `hot-day exposure` or `temperature exposure`, not crop heat injury.
3. **Soil context:** show SSURGO map-unit/component attributes, including available-water storage where the actual query returns it. Preserve component percentages and depth; do not flatten horizons into a misleading field soil test.
4. **Vegetation observation:** if Phase 3 passes, show the measured NDVI series and low-vegetation observation windows. Call threshold-based results a `screening flag` unless thresholds have been validated for the crop, season, and sensor.
5. **Data coverage:** show valid-observation count, cloud/invalid fraction, missing days, time span, and source age. Do not turn this into a confidence percentage without a calibration method.

### Optional environmental layers — only when a diagnostic needs them

- **USGS 3DEP DEM:** add terrain slope only if the selected AOI and processing method need terrain information. The 1/3 arc-second product is approximately 10 m; choose a suitable resolution for the AOI and do not imply that it resolves every micro-topographic feature.
- **NASA GPM IMERG:** add precipitation-event context if rainfall intensity/timing matters. IMERG provides half-hourly fields at 0.1°; it is regional context. It is not, by itself, a RUSLE R-factor.
- **NASA SMAP L4:** add root-zone/surface soil-moisture context only if useful to the demo. Version 8 is 9 km and 3-hourly, requires a free NASA Earthdata Login, and must be labelled `Regional Context`, never field-level moisture.

Do not add GPM, SMAP, ECOSTRESS, OpenET, PRISM, and 3DEP all at once. Select the one extra dataset that directly supports the diagnostic being demonstrated.

### Erosion logic — explicit stop/go gate

Do not implement the PRD's current `rusle_erosion_score` as written. A defensible RUSLE result requires a defined and documented method for R (rainfall erosivity), K (soil erodibility), LS (slope length/steepness), C (cover-management), and P (support practice), with compatible units and temporal/spatial aggregation. Monthly or daily precipitation totals cannot simply be substituted for rainfall erosivity. If the team cannot obtain and validate these inputs, implement only a descriptive `bare-soil + rainfall exposure` screen and name it accordingly. Do not output a 0–100 erosion score.

### Evaporative stress logic — explicit stop/go gate

Do not infer actual ET, potential ET, or ESI from NASA POWER temperature and relative humidity alone. Only add an evaporative-stress metric after a real ET/ESI product is acquired and its units, spatial scale, quality flags, and access method are understood. Otherwise show the actual weather variables and label the metric unavailable.

### Person 1 — Backend/data/science owner

- Create a small `diagnostics.py` or extend `si_diagnostics.py` with only the accepted indicators.
- For each indicator, document its inputs, formula, units, geographic scope, missing-data handling, and interpretation.
- Keep raw measurements separate from derived indicators.
- Add data-quality fields to the API response. Do not return a single synthetic `uncertainty` number.
- Ask a domain reviewer or use an authoritative agronomy/method reference to check each agronomic threshold before enabling it. Record the reference beside the rule.
- Implement deterministic tests using small, clearly labelled test fixtures. Tests may use fixtures; the application/demo may not use them as real observations.

### Person 2 — Frontend owner

- Add an `Evidence / indicators` section with a compact display of the accepted metrics.
- For every metric, show a one-sentence explanation, source, period, units, and geographic scale.
- Distinguish `Measured`, `Calculated from measured data`, `Screening flag`, `Unavailable`, and `Needs local validation`.
- Link each displayed metric to the evidence/source panel or show its source inline.
- Do not use red/green risk badges for unsupported values. Do not show an empty metric as 0.

### AI/subagent split

- **Science reviewer agent:** review formulas, units, spatial/temporal fit, and claims. It must cite official documentation or named agronomy sources and list unresolved assumptions. It cannot approve its own invented formula.
- **Unit-test agent:** generate test cases for formula edge cases using the exact agreed method.
- **UI explanation agent:** write plain-language metric descriptions from approved definitions only.
- Person 1 retains responsibility for scientific approval and implementation. Person 2 retains responsibility for truthful display.

### Expected result

A small diagnostic panel based only on available real observations, plus explicit gaps. A diagnostic may be unavailable; that is a valid outcome if the required data is absent.

### Tests and acceptance

- [ ] Every displayed indicator has a written formula/definition, unit, source, and spatial/temporal scope.
- [ ] Unit tests cover valid, invalid, missing, and boundary inputs.
- [ ] Weather summaries reconcile to the processed NASA POWER observations.
- [ ] Soil summaries preserve map-unit/component distinctions.
- [ ] NDVI-based indicators only appear if Phase 3 passed.
- [ ] No uncalibrated confidence percentage, false ESI, or unsupported RUSLE score is returned.
- [ ] Frontend labels match the API's evidence status.

---

## 19. Phase 5 — Add the explainable crop-rotation comparison

### What this phase is for

**For a person:** Once FieldShift has real information about the selected area, it can compare a few possible crop sequences and explain their trade-offs. It is an aid for discussion with a farmer or extension officer, not an automatic instruction or guaranteed yield/profit forecast.

**For AI coding agents:** Build a deterministic rule-based comparison from actual data and cited agronomic rules. Use an LLM only to phrase an explanation from the calculated result, if a natural-language feature is genuinely needed. Do not let the LLM choose crops, invent values, or calculate scores.

### Preconditions

Do not start this phase until all are true:

- A real geographic scope is selected and consistently used by CDL, SSURGO, and weather sources.
- Actual crop history exists for that AOI, or the UI explicitly labels the history as county-level context and does not claim a field baseline.
- Soil and weather inputs are available, with units and source metadata.
- Candidate crop/cover-crop rules for Iowa are supported by trustworthy agricultural references, ideally Iowa State University Extension/USDA/NRCS sources.
- The team can explain why each candidate is agronomically plausible for the region and what data is missing.

### Minimum implementation

1. **Baseline:** derive from observed CDL crop classifications for the same AOI and years. If only county-level crop statistics exist, show `County crop context`; do not call it a field baseline rotation.
2. **Candidates:** start with one or two alternatives supported by regional agronomy sources. Add a third only if its assumptions and required inputs are available.
3. **Hard constraints:** implement only user constraints with clear meaning and required inputs. Do not add `rainfed_only` or `has_livestock` unless the recommendation rules genuinely use them.
4. **Criteria:** use only measurable or sourced criteria, such as crop-family diversity, mapped soil water-storage context, observed hot/dry exposure, and cover/vegetation evidence when available.
5. **Scoring:** define the direction and normalization of each criterion; show the contribution to the result. A weighted score is allowed only after each score has a traceable definition. Missing criteria are marked unavailable and handled explicitly; they must not silently become zero or a neutral score.
6. **Trade-offs:** show the reason for each suggestion, expected agronomic benefit according to the cited source, data evidence, risks, and missing information.
7. **Climate what-if:** if included, label it as a sensitivity scenario, not a climate forecast. State the formula and range. It should perturb only variables that the model actually uses.

### Keep out of this phase unless proven necessary

- Profit, net return, or yield prediction.
- A universal crop score or a fixed default confidence value.
- A generic global crop database.
- Automated LLM crop selection.
- A large simulation framework.
- Unverified root-depth, nitrogen-fixation, drought-tolerance, or pest-family numbers copied into a static catalog without sources.

`USDA NASS Quick Stats` can later provide county-level historic crop yield context. It must be labelled county-level. It does not convert the model into a field-yield predictor. USDA AMS market prices and farm-specific production costs are separate data needs; postpone financial ranking until both are available and correctly aligned.

### Person 1 — Backend/decision-engine owner

- Audit `rotation_engine.py` and `crops_catalog.json`; remove any synthetic scoring behaviour from the active path.
- Create a small, explicit input model containing AOI, crop history, accepted soil/weather/vegetation indicators, candidate sequence, and evidence references.
- Implement the baseline and supported alternatives using deterministic rules.
- Store the agronomy rule's source URL/title, applicability, and caveats with the output.
- Return a `why_suggested` explanation assembled from structured facts, plus `benefits`, `tradeoffs`, `information_gaps`, and `local_review_required`.
- Implement criterion-level score tests and deterministic rankings. Confirm changing a user priority changes rankings only when that criterion is actually available.
- Do not call an external LLM API to generate the numeric recommendation.

**Likely files:** `backend/app/services/rotation_engine.py`, a small crop/rule data file with citations, `backend/app/schemas.py`, `backend/app/api/routes_recommend.py`, and focused tests.

### Person 2 — Frontend owner

- Build a comparison view for the observed baseline and the available candidate sequences.
- Show sequence, score only if it is valid, criteria, evidence, trade-offs, missing data, and local-review warnings.
- Add priority sliders only for criteria implemented in the API.
- Add climate sensitivity controls only if the API has a tested calculation for them.
- Do not display three alternative cards just to satisfy a design mock-up. Display the number of supported results returned by the backend.
- Add a plain-language disclaimer that the output is decision support and requires local agronomic review.

### AI/subagent split

- **Agronomy research agent:** find region-specific extension/USDA/NRCS references for crop sequences and cover-crop suitability. Return citations, exact relevant claims, applicability limits, and publication date. No crop rule goes into production from an uncited agent summary.
- **Scoring review agent:** inspect score normalization, edge cases, and rank stability; do not alter the agronomic rule source.
- **API contract agent:** check that backend Pydantic and frontend TypeScript contracts remain identical.
- Person 1 approves the agronomic rules and scoring implementation. Person 2 approves the explanation and visual trade-offs.

### Expected result

The app compares a real baseline where data supports it and a small number of evidence-backed alternatives. Every suggestion can be traced to inputs and a source. The app can return fewer than four options if that is all the evidence supports.

### Tests and acceptance

- [ ] Baseline sequence is derived from actual AOI CDL observations, or clearly labelled as unavailable/county context.
- [ ] Each candidate has at least one cited regional agronomy rule and a documented assumption set.
- [ ] Numeric scores are deterministic and fully defined.
- [ ] Missing input never becomes a fabricated score or value.
- [ ] Priority changes produce predictable ranking changes.
- [ ] API and frontend types match.
- [ ] No yield/profit prediction is shown without a separately validated model and data.
- [ ] The UI shows benefits, trade-offs, information gaps, and need for local review.

---

## 20. Phase 6 — End-to-end integration, validation, and hackathon demo

### What this phase is for

**For a person:** This phase makes sure every screen and calculation is connected to the same real observations. The team rehearses a short demonstration and can answer where each number came from, what it means, and what the app cannot yet say.

**For AI coding agents:** Find integration defects, verify reproducibility, check that claims match data, and improve only the parts that block the demo. Do not add new features during stabilization.

### Person 1 — Backend/data/science owner

- Run the complete ingestion pipeline from a clean environment.
- Verify the generated raw and processed files and confirm there are no seeded or synthetic observations in the runtime path.
- Add a compact data manifest for every source: product, request/area, period, units, retrieval time, and processing version.
- Confirm API responses are served from processed data and are not dependent on a live third-party source during each page load.
- Verify missing-source behaviour, stale real-cache behaviour, and invalid-data handling.
- Run all backend tests and inspect logs for swallowed provider failures.
- Produce a one-page `METHODS_AND_LIMITATIONS.md`: inputs, transformations, formulas, units, known limitations, and deferred indicators.

### Person 2 — Frontend/demo owner

- Test the entire user flow from initial load to map, evidence, diagnostics, and recommendations if Phase 5 passed.
- Remove remaining placeholder text, hardcoded values, dead controls, and unsupported layers.
- Ensure all sections show loading, error, missing-data, and stale-data states appropriately.
- Ensure chart axes, units, time zones, source labels, and geographic scope are clear.
- Prepare one 3–5 minute demo walkthrough using the real Story County data.
- Prepare a backup screen recording or screenshots from the successful local run; do not use fabricated data as a backup.

### Joint validation

- Compare a sample of CDL results against the provider's own response/export.
- Compare selected NASA POWER daily values and monthly aggregates against the saved raw API response.
- Compare a few SSURGO map-unit attributes against the original SDA rows and official field definitions.
- If Landsat is included, inspect at least one source scene/QA mask and independently recalculate a small NDVI sample.
- If recommendations are included, manually trace one result from data input to final criterion score and narrative.
- Have a knowledgeable reviewer (agriculture faculty, extension adviser, or domain mentor) review the recommendations if available. If unavailable, state that expert field validation has not yet been done.

### AI/subagent split

- **End-to-end test agent:** run documented commands and report exact outputs; no claims without logs.
- **Data provenance audit agent:** trace displayed values back to raw responses and processing steps.
- **Scientific claims audit agent:** flag wording that overstates spatial resolution, causal inference, confidence, erosion, heat, ET, or crop recommendation certainty.
- **Demo rehearsal agent:** follow the script as a first-time judge and list confusing or broken steps.
- Person 1 owns backend/data correctness; Person 2 owns frontend usability and demo flow. Both approve the final result.

### Expected result

A reproducible demo that can be run from a clean checkout, with a clear account of which phases and data sources actually work. The final presentation demonstrates the completed slice, not the future roadmap.

### Final acceptance checklist

- [ ] Fresh setup instructions work on the demo machine.
- [ ] Ingestion succeeds for the sources claimed in the demo.
- [ ] All runtime observations come from real sources or documented calculations from them.
- [ ] No placeholder/fallback numbers are visible.
- [ ] Source provenance exists for every data panel and recommendation input.
- [ ] One sample of every displayed value can be traced to a raw response or source scene.
- [ ] Map and charts accurately describe spatial/temporal resolution.
- [ ] Backend and frontend builds/tests pass.
- [ ] The demo survives an unavailable external provider after ingestion because it uses local processed data.
- [ ] Known gaps are stated directly.
- [ ] The team can explain one complete user journey and one complete calculation.

---

## 21. Phase 7 — After the hackathon (not part of the current build)

Only start this phase if the hackathon demo is complete and there is a concrete reason to extend it.

Possible next steps, in this order:

1. **Second U.S. region:** add one additional county as a portability test. Confirm that each provider actually covers it; a region config is not a guarantee of source availability.
2. **More field AOIs:** allow a user to save more than one real field boundary only after the first AOI workflow is reliable.
3. **More data sources:** add one source only when it fills a specific evidence gap. Examples include additional satellite vegetation, crop yield, terrain, rainfall, or ET data. Do not add a 26-source checklist as an objective.
4. **Model validation:** collect field observations or trusted local outcomes and measure whether diagnostics/recommendations are useful. Do not claim predictive performance without a validation dataset.
5. **AI explanation:** optionally use a language model to explain already-calculated evidence in farmer-friendly language. Constrain it to the structured evidence object; do not let it fabricate measurements or score rotations.
6. **Region portability:** extract only the repeated configuration/provider mappings that have actually emerged. Do not build a generic plugin architecture before there are multiple working regions.

Not planned unless specifically requested: user accounts, billing, SaaS dashboards, multi-tenant infrastructure, large-scale cloud data pipelines, autonomous agents in production, enterprise monitoring, or a commercial market platform.

---

## 22. Later-phase data references and their correct use

These are candidates for later phases, not a requirement to download all of them. Verify the exact query, product version, date coverage, authentication, and geographic resolution before implementation.

| Dataset/source | Why it may be useful | Correct limitation / use | Official link |
|---|---|---|---|
| Landsat 8/9 Collection 2 Level-2 Surface Reflectance | Derive real vegetation indices such as NDVI | 30 m scene-based data; apply Collection 2 scale factors and QA masks; raster processing is required | [USGS Landsat Collection 2 Surface Reflectance](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-reflectance) |
| USGS 3DEP 1/3 arc-second DEM | Derive terrain/elevation and possibly slope for an AOI | Approximately 10 m; terrain alone does not calculate erosion risk | [USGS 3DEP DEM collection](https://data.usgs.gov/datacatalog/data/USGS%3A3a81321b-c153-416f-98b7-cc8e5f0e17c3) |
| NASA GPM IMERG V07 | Understand rainfall timing and heavy-rainfall events | Half-hourly, 0.1° grid; regional context; rainfall totals are not automatically the RUSLE R-factor | [NASA IMERG V07 documentation](https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation) |
| NASA SMAP L4 Version 8 | Add surface/root-zone soil-moisture context | 9 km, 3-hourly; free Earthdata Login required; regional only, not field-scale | [NSIDC SPL4SMGP Version 8](https://nsidc.org/data/spl4smgp/versions/8) |
| USDA NASS Quick Stats | County-level historic yields for comparison/context | Yield data depends on commodity, statistic, geography, and year filters; not field yield | [USDA NASS Quick Stats](https://www.nass.usda.gov/Quick_Stats/) |
| USDA NRCS Soil Data Access WFS/WMS | Spatial soil map-unit lookup and visualization | Use the documented spatial filter and verify coordinate system/feature type | [NRCS Soil Data Access Web Service Help](https://sdmdataaccess.nrcs.usda.gov/WebServiceHelp.aspx) |
| USDA CropScape Web Services | CDL map, statistics, and AOI-based requests | Service docs show county, bbox, points, and vector-AOI requests; confirm the current service response before relying on it | [CropScape request examples](https://nassgeodata.gmu.edu/CropScape/devhelp/getexamples.html) |

Additional scientific/data notes:

- USGS states that Landsat Collection 2 surface-reflectance products are 30 m and documents the scaling equation `SR = (DN × 0.0000275) − 0.2`: [USGS product documentation](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-reflectance).
- CropScape's official examples show `GetCDLStat` by county FIPS, bounding box, points, and a vector AOI URL, and `GetCDLFile` can return a GeoTIFF URL: [CropScape examples](https://nassgeodata.gmu.edu/CropScape/devhelp/getexamples.html).
- NRCS documents tabular REST/POST, spatial WFS, and WMS services; WFS requests support spatial filters and are constrained by requested area: [NRCS service help](https://sdmdataaccess.nrcs.usda.gov/WebServiceHelp.aspx).
- NASA describes IMERG as half-hourly 0.1° × 0.1° fields: [IMERG V07 technical documentation](https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation).
- NSIDC describes SMAP L4 Version 8 as 9 km and 3-hourly, with surface and root-zone soil-moisture fields and Earthdata Login access: [SPL4SMGP V8](https://nsidc.org/data/spl4smgp/versions/8).
- USDA NASS describes Quick Stats as a queryable/exportable agricultural statistics database: [Quick Stats](https://www.nass.usda.gov/Quick_Stats/).

---

## 23. AI-agent operating method for every remaining phase

AI agents are used to research, code, test, and review. The application does not need autonomous agents to make agricultural decisions.

### Team ownership

- **Person 1:** backend, ingestion, processing, schemas, science/method correctness, recommendation calculations.
- **Person 2:** frontend, map and charts, API wiring, interaction states, accessibility/readability, demo experience.
- **Shared:** response contract, phase gate, manual source verification, final acceptance.

### Required workflow for every subagent task

1. Read `RULES.md`, `ARCHITECTURE.md`, `DECISIONS.md`, and the relevant parts of `PRD.md`.
2. State the exact task goal, assumptions, accepted inputs, expected output, and files it may edit.
3. Research official source documentation before implementing a provider or scientific formula.
4. Implement one bounded change. Do not edit shared contracts unless assigned.
5. Add a focused test or a documented manual verification step.
6. Run the exact verification command and include its actual output/result.
7. Report changed files, source references, tests run, failed tests, unresolved assumptions, and known limitations.
8. Stop. Do not continue into the next phase or add adjacent features without a new task.

### Copyable backend subagent prompt

```text
You are a bounded implementation subagent for FieldShift.
Read RULES.md, ARCHITECTURE.md, DECISIONS.md, and the relevant PRD section first.
Task: [one precise backend task].
Allowed files: [exact file list]. Do not edit other files.
Use only the official data source and method specified in the task. Do not invent API fields,
observations, thresholds, units, or fallback values. Preserve raw-source provenance.
Keep the change minimal and consistent with the current architecture. Add tests for the
parser/calculation and missing-data cases. Run the exact test command and report the real
result. In the final report list changed files, source links, test output, assumptions,
limitations, and anything not completed. Do not claim success for work not run.
```

### Copyable frontend subagent prompt

```text
You are a bounded frontend implementation subagent for FieldShift.
Read RULES.md and ARCHITECTURE.md first. Use the existing React/TypeScript stack.
Task: [one precise component or interaction].
Allowed files: [exact file list]. Do not edit backend files or invent response fields.
Use only values returned by the agreed API contract. Do not add mock/demo numbers,
placeholder charts, fake map layers, or unsupported status badges. Provide loading,
error, missing-data, and stale-data states where relevant. Run npm run build and report
its actual result, changed files, assumptions, and remaining limitations.
```

### Shared API contract rule

The backend owner changes `backend/app/schemas.py`; the frontend owner mirrors it in `frontend/src/types/fieldshift.ts`. Agree before changing either. Never let two agents edit the same shared file concurrently. Merge one phase at a time and run backend tests plus frontend build after each integration.

### Final instruction to all agents

**A missing result is allowed. A fabricated result is not.** If a source, calculation, map layer, or recommendation cannot be verified, return an explicit unavailable state and report the blocker. Do not make the demo look complete by making the science less truthful.

---

## 24. Recommended order if hackathon time is tight

Do not attempt every phase equally. Use this priority order:

1. Complete Phase 1 end to end.
2. Complete the Phase 2 county map and data-layer verification. Attempt the AOI proof only with a strict time box.
3. If the raster-processing spike succeeds quickly, add one small Landsat NDVI series in Phase 3. If it does not, defer it.
4. Build only the Phase 4 indicators supported by the acquired data.
5. Implement Phase 5 crop rotations only if a true AOI crop history and region-specific agronomy rules exist.
6. Reserve the remaining time for Phase 6 integration, validation, and demo rehearsal.

A verified crop/soil/weather dashboard with one real map layer is stronger than a dashboard showing 26 datasets, 4 rotation cards, heat stress, evapotranspiration, erosion, market returns, and confidence values that the project cannot substantiate.

## 25. Final project completion definition

The hackathon build is complete when the team can demonstrate, on one real Story County data slice:

- [ ] Real USDA CDL crop data.
- [ ] Real USDA SSURGO mapped soil data.
- [ ] Real NASA POWER historical weather data.
- [ ] Clear spatial scope and a working map layer.
- [ ] Real satellite-derived vegetation evidence only if the raster-processing gate passed.
- [ ] A small set of measured or calculated indicators with documented methods.
- [ ] Evidence-backed rotation comparisons only if the prerequisite data and agronomy references exist.
- [ ] End-to-end API/UI integration, tests, source provenance, and honest limitations.
- [ ] A repeatable 3–5 minute demo.

The global architecture remains the direction, but **the hackathon implementation remains one region until the demo is working and verified**.
