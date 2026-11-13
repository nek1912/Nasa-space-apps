# AGENT.md — FieldShift Master Agent Entrypoint

## Project Identity
**FieldShift** is a geospatial decision-support web app for the 2026 NASA Space Apps Challenge ("Field Shift: Adapting Farms with NASA Data"). It fuses 26 NASA, USDA, USGS, FAO, and ESA datasets to diagnose field vulnerabilities (bare-soil erosion windows, thermal/evaporative stress, aquifer depletion) and recommend >= 4 crop rotation strategies (1 existing baseline + 3 optimized alternatives).

## Context Routing (Read Before Acting)
1. **Before writing any code:** Read `RULES.md` (Karpathy guidelines & banned patterns).
2. **Before touching routes, types, or files:** Read `ARCHITECTURE.md` (directory structure & locked schemas).
3. **Before proposing new libraries or changing data flow:** Read `DECISIONS.md` (why our architecture is locked).
4. **Before implementing math, scoring, or UI features:** Read `PRD.md` (exact formulas & acceptance criteria).

## Tech Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, HTTPX (async), NumPy, SciPy, Pytest.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, MapLibre GL JS, Recharts, Lucide React.
- **Storage:** Zero database server. Static JSON/CSV benchmarks in `backend/data/` + live REST APIs with local fallback.

## Goal-Driven Verification Commands
Never mark a task complete without running and passing the relevant check:
- **Backend Unit/Contract Tests:** `cd backend && pytest -v`
- **Seed Static Data:** `cd backend && python scripts/seed_static_data.py`
- **Backend Live Run:** `cd backend && uvicorn app.main:app --reload --port 8000`
- **Frontend Type & Build Check:** `cd frontend && npm run build`
- **Frontend Dev Run:** `cd frontend && npm run dev`