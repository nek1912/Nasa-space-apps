# DECISIONS.md — Architectural Decision Log (DO NOT REVERT)

## ADR-001: Zero Native Raster Libraries on Backend (No GDAL/Rasterio)
- **Context:** Processing raw HDF5/NetCDF/GeoTIFF granules in Python causes C-dependency build failures and >10s request latency.
- **Decision:** Render spatial rasters (`SMAP`, `MODIS`, `GPM`, `ECOSTRESS`, `CDL`, `NAIP`, `Sentinel-2`) directly in the browser via WMS/WMTS tiles (`MapLibre GL`), and run backend math strictly on pre-harmonized or REST-fetched 36-dekad JSON time-series using `numpy`/`scipy`.
- **Consequence:** Sub-second backend execution, <20 MB repo size, zero installation failures across Windows/Mac/Linux.

## ADR-002: Common Temporal Grid = 36 Dekads (10-Day Steps)
- **Context:** NASA datasets have mismatched temporal revisit rates (`SMAP` 2-3 days, `Landsat` 16 days, `MODIS` 8-16 days, `NASA POWER` daily, `GRACE-FO` monthly).
- **Decision:** Harmonize all seasonal curves to **36 dekads per year** (3 dekads per month, ~10 days each).
- **Consequence:** Fast vector math in `si_diagnostics.py` and clean rendering in `PhenologyTimeline.tsx` without noisy daily spikes or overly coarse monthly averages.

## ADR-003: Multi-Scale Spatial Separation (Macro vs. Field Grid)
- **Context:** `SMAP` (9km) and `GRACE-FO` (~300km) cannot resolve a 160-acre farm's sub-field variations.
- **Decision:** Use `SMAP`, `NLDAS/GLDAS`, `USGS NWIS`, and `GRACE-FO` strictly as **Regional Hydrologic Boundary Constraints** (e.g., penalizing irrigation-heavy rotations in depleting aquifers). Use 30m (`Landsat`, `SRTM`, `USDA CDL`, `SSURGO`) and 70m (`ECOSTRESS`, `OpenET`) for field-scale bare-soil and thermal stress diagnosis.

## ADR-004: Deterministic Agronomic SI + MCDA Over Black-Box LLM Generation
- **Context:** NASA judges require explainable evidence, uncertainty quantification, and sub-100ms response when dragging climate/priority sliders.
- **Decision:** Implement an explicit **Multi-Criteria Decision Analysis (MCDA) + FAO-56 Water Balance + RUSLE Erosion Engine** in `rotation_engine.py` rather than calling an external LLM API.
- **Consequence:** 100% deterministic, reproducible, explainable scores with zero API token costs or hallucinations.

## ADR-005: 2.5-Second Circuit Breaker with Benchmark Fallback
- **Context:** Government REST APIs (`NASA POWER`, `USDA NRCS SDA`, `USGS`) occasionally throttle or time out during live hackathon judging.
- **Decision:** Wrap all `httpx.AsyncClient` calls with a 2.5-second timeout that seamlessly falls back to the nearest benchmark profile in `backend/data/hero_farms.json`.

## ADR-009: Phase 3 Landsat NDVI — M2M API + Deferred Raster Processing (PROPOSED)
- **Context:** Phase 3 requires Landsat 8/9 Collection 2 Level-2 Surface Reflectance (30 m) to compute NDVI time series. Reading GeoTIFF pixels requires a raster library, but `rasterio`/`gdal` are banned by RULES.md §5.
- **Decision:** Two-part approach:
  1. **M2M API client** (implemented now, no raster dependency): authenticate via `login-token`, search scenes via `scene-search` using dataset `landsat_ot_c2_l2`, and drive the `download-options` → `download-request` → `download-retrieve` flow. Requires an ERS account with MACHINE role (approval takes days).
  2. **Raster processing** (deferred): NDVI computation from downloaded GeoTIFFs is NOT implemented. A `rasterio` exception is PROPOSED in RULES.md §5 for a single offline preprocessing script only. Until approved, no `rasterio` import, no hand-written GeoTIFF parser, and no computed NDVI values.
- **Consequence:** Phase 3 can acquire scene metadata and download URLs now, but quantitative NDVI values remain gated on the `rasterio` exception approval and Landsat data download. The app may display verified Landsat WMS tiles for context without computing NDVI.