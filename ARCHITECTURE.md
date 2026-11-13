# ARCHITECTURE.md — System Structure & Locked Data Contracts

## 1. Monorepo Directory Tree
```text
fieldshift/
├── AGENT.md
├── RULES.md
├── ARCHITECTURE.md
├── DECISIONS.md
├── PRD.md
├── backend/
│   ├── requirements.txt
│   ├── data/
│   │   ├── crops_catalog.json         # 20 crops: FAO-56, GAEZ, N-fix, root, pest family, AMS price
│   │   ├── hero_farms.json            # 3 pre-harmonized 36-dekad cubes (ks_finney, ia_story, ca_fresno)
│   │   └── nass_county_baselines.csv  # USDA NASS county yields
│   ├── scripts/
│   │   └── seed_static_data.py        # Deterministic generator for data/*.json
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint + CORS
│   │   ├── schemas.py                 # Locked Pydantic v2 contracts
│   │   ├── api/
│   │   │   ├── routes_field.py        # GET /api/hero-farms, POST /api/analyze-field
│   │   │   └── routes_recommend.py    # POST /api/recommend-rotations
│   │   └── services/
│   │       ├── nasa_power.py          # Live NASA POWER daily/climatology REST + fallback
│   │       ├── usda_soil.py           # Live USDA NRCS SSURGO SQL-REST + fallback
│   │       ├── terrain_water.py       # Live USGS SRTM slope/TWI & NWIS groundwater + fallback
│   │       ├── si_diagnostics.py      # Bare-soil detector, RUSLE erosion, thermal stress, uncertainty
│   │       └── rotation_engine.py     # Multi-objective crop sequence ranker + climate perturbation
│   └── tests/
│       ├── test_schemas.py
│       ├── test_live_ingest.py
│       ├── test_si_diagnostics.py
│       └── test_rotation_engine.py
└── frontend/
    ├── package.json
    └── src/
        ├── App.tsx
        ├── types/fieldshift.ts        # Exact TS mirror of backend/app/schemas.py
        ├── api/client.ts              # Fetch client targeting http://localhost:8000/api
        ├── config/mapLayers.ts        # WMS/WMTS tile templates (NASA GIBS, CDL, NAIP, Sentinel-2)
        └── components/
            ├── FarmSelectorBar.tsx
            ├── FieldMapCanvas.tsx
            ├── PhenologyTimeline.tsx
            ├── PrioritySliders.tsx
            ├── ClimateStressBar.tsx
            ├── RotationMatrix.tsx
            └── UncertaintyBadge.tsx