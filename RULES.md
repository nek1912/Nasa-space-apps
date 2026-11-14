# RULES.md — Karpathy Guidelines & Hard Technical Constraints

## 1. Think Before Coding
- State assumptions explicitly before implementing non-trivial logic.
- If multiple interpretations exist, surface them briefly—never pick silently.
- Never invent API endpoints, query parameters, or JSON keys not listed in `ARCHITECTURE.md`.

## 2. Simplicity First
- Write the minimum code required to solve the specified phase.
- No speculative abstractions, base classes, factory patterns, or single-use wrappers.
- If a module exceeds 250 lines and can be written in 80 lines of clear NumPy/Python or React, rewrite it.

## 3. Surgical Changes
- Touch ONLY the files required by the user's current prompt.
- Preserve existing formatting, naming conventions, and imports in adjacent code.
- Clean up unused imports/variables created by YOUR changes; do not delete pre-existing code unless instructed.
- **Schema Lock Law:** `backend/app/schemas.py` and `frontend/src/types/fieldshift.ts` are the single source of truth. Never rename or remove fields in either file without updating both simultaneously.

## 4. Goal-Driven Execution
- Define verifiable steps before coding:
  `1. [Step] -> verify: [exact command]`
- Fix failing tests immediately before moving to the next file.

## 5. Hard Technical Guardrails (NON-NEGOTIABLE)
- **BANNED Backend Packages:** `gdal`, `fiona`, `geopandas`, `netCDF4`, `h5py`, `celery`, `redis`, `sqlalchemy`. All backend math operates on JSON/CSV arrays using `numpy` and `scipy`.
- **`rasterio` — PROPOSED EXCEPTION (Phase 3 only):** `rasterio` is banned by default. A narrowly scoped exception is proposed for Phase 3 preprocessing only: a single offline script that reads Landsat Collection 2 Level-2 GeoTIFFs, applies QA/scaling, calculates NDVI, and produces a small AOI summary. This exception is **not active** until:
  1. It is explicitly approved and moved from "PROPOSED" to "ACTIVE" in this file, and
  2. `DECISIONS.md` ADR-009 is updated to record the approval, and
  3. `rasterio` is added to `backend/requirements.txt` and installation is verified on all team machines.
  Until then, do not import `rasterio` anywhere, do not hand-write a GeoTIFF parser, and do not compute NDVI from raw pixels.
- **Latency Ceiling:** Every FastAPI endpoint must return in `< 2000ms` (and `< 150ms` for cached Hero Farms).
- **Mandatory Timeout Fallback:** Every live external HTTP call (`NASA POWER`, `USDA SDA`, `USGS`) must set `timeout=2.5` seconds and fall back deterministically to `backend/data/hero_farms.json` on timeout or HTTP error.
- **Scientific Integrity:** Never claim coarse datasets (`SMAP` 9km, `GRACE-FO` basin scale) resolve sub-field boundaries. Label them as `Regional Context` and use 30m (`Landsat`, `SRTM`, `USDA CDL`) and 70m (`ECOSTRESS`, `OpenET`) for `Field-Scale Vulnerability`.