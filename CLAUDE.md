# FieldShift AI Coding Agent Rules (CLAUDE.md)

## 1. Mission Context
We are building **FieldShift**, a decision-support web application for the 2026 NASA Space Apps Challenge ("Field Shift: Adapting Farms with NASA Data"). It fuses NASA Earth Observations (SMAP, GPM IMERG, Landsat, MODIS, NASA POWER, SRTM, ECOSTRESS, GEDI) with USDA/USGS datasets (SSURGO, CropScape CDL, NAIP, OpenET, NASS, AMS Market News, NWIS) to diagnose field vulnerabilities (bare-soil erosion windows, heat/evaporative stress, aquifer depletion) and compare >= 4 crop rotation strategies (1 existing baseline + 3 tailored strategies).

## 2. Karpathy Coding Guidelines (STRICT ENFORCEMENT)
1. **Think Before Coding:** State assumptions explicitly. Never silently invent endpoints or change field names in `schemas.py` / `fieldshift.ts`.
2. **Simplicity First:** Write the minimum code required. No database servers (use in-memory JSON + static file cache), no Celery/Redis queues, no authentication boilerplate, no heavy C-binding geospatial libraries (`gdal`/`rasterio` are BANNED—use pure `numpy`/`scipy` on JSON arrays and WMS tiles on the frontend).
3. **Surgical Changes:** Touch only files specified in the active Phase. Do not reformat unrelated files.
4. **Goal-Driven Execution:** Every phase has explicit `verify:` commands. Run them and make all tests pass before moving to the next phase.

## 3. Non-Negotiable Architecture Rules
- **Latency Ceiling:** Every API endpoint MUST respond in under 2.0 seconds. External calls to `NASA POWER` or `USDA SDA` must use a `2.5s` timeout and fall back seamlessly to `backend/data/hero_farms.json`.
- **Scientific Honesty:** Never claim 9km SMAP or basin-scale groundwater data resolves sub-field variations; label them as `Regional Context` while using 30m Landsat/CDL/SRTM and 70m ECOSTRESS/OpenET for `Field-Scale Vulnerability`.
- **Explainability:** Every recommended rotation MUST output: (1) `why_suggested`, (2) `nasa_usda_evidence`, (3) `agronomic_benefits`, (4) `information_gaps`, and (5) `local_review_risks`.