# PRD.md — Product Requirements, Math Formulas & Acceptance Criteria

## 1. Core Problem & User Persona
Farmers face shifting temperatures, erratic rainfall, aquifer depletion, and soil degradation, but lack accessible tools to test how new crop rotations will perform on their specific soil and microclimate. **FieldShift** translates 26 satellite and ground datasets into an interactive rotation explorer that supports—and never replaces—farmer judgment and local extension expertise.

## 2. Exact Mathematical Specifications (`si_diagnostics.py` & `rotation_engine.py`)

### A. Bare-Soil Exposure Detection
For each dekad $t \in \{1..36\}$:
- Flag `is_bare_vulnerable = True` when `ndvi_landsat < 0.25` AND `bsi_bare_soil > 0.02`.
- `bare_soil_days_per_year = count(is_bare_vulnerable) * 10`.

### B. Coupled Storm-Slope Erosion Score (RUSLE-Lite)
For each bare-soil dekad $t$:
$$E_t = \text{GPM\_precip\_mm}_t \times \text{SSURGO\_kwfact} \times \left(0.1 + 0.25 \times \text{SRTM\_slope\_pct}\right) \times (1 - \text{NDVI}_t)$$
Normalize $\sum E_t$ to `[0, 100]` as `rusle_erosion_score` and identify the highest-scoring 2-month window as `peak_erosion_risk_season`.

### C. Crop Heat & Evaporative Stress Detection
Flag `is_heat_stress = True` for dekad $t$ when active crop cover (`ndvi_landsat >= 0.40`) coincides with either:
- `esi_ecostress < -1.0` (severe evaporative deficit where actual ET lags potential ET), OR
- `tmax_c > 34.0` (reproductive heat shock).

### D. Climate Scenario Perturbation (`rain_shift_pct`, `temp_shift_c`)
When sliders are adjusted:
- $P_{\text{adj}} = P_{\text{annual}} \times (1 + \text{rain\_shift\_pct}/100)$
- $\text{ET}_{c\text{,adj}} = \text{WaterNeed}_{\text{crop}} \times (1 + 0.045 \times \text{temp\_shift\_c})$
- Heat stress penalty increases by $8 \times \max(0, T_{\max\text{,peak}} + \text{temp\_shift\_c} - T_{\text{crit,crop}})$.

### E. Multi-Objective Rotation Scoring (`0-100` across 6 axes)
Every call to `/api/recommend-rotations` must return **4 cards**:
1. **Strategy 0 (`is_baseline: True`):** Current 5-year rotation derived from `USDA CDL` history.
2. **Strategy 1 (`Water-Saver & Aquifer Shield`):** Drought-tolerant C4 cereal (Sorghum/Millet) + low-water pulse (Chickpea/Cowpea).
3. **Strategy 2 (`Soil Armor & N-Builder`):** Main cash crop + overwintering cover/legume mix (Cereal Rye + Crimson Clover / Brassica bio-fumigant) eliminating bare-soil dekads.
4. **Strategy 3 (`Climate-Hedged Cash + Forage`):** Deep-taproot crop (Sunflower/Pigeonpea/Alfalfa) + high-value forage/oilseed.

Compute 6 normalized radar scores `[0..100]` per strategy:
- `water_efficiency`: Reduction in irrigation deficit vs. Baseline, amplified if `aquifer_trend_cm_yr < -1.0`.
- `soil_health`: Biological N-fixation ($\text{kg N/ha}$) + root architecture diversity (`deep_taproot` + `dense_fibrous`).
- `erosion_armor`: Percentage of `is_bare_vulnerable` dekads covered by living roots.
- `pest_disruption`: `100` if 3 consecutive crops span 3 distinct botanical families (`Poaceae`, `Fabaceae`, `Brassicaceae`, `Asteraceae`, `Malvaceae`); penalized down to `25` for monoculture.
- `climate_resilience`: Margin of safety under active `rain_shift_pct` and `temp_shift_c` sliders.
- `market_return`: Risk-adjusted net return (`$/acre`) from `USDA NASS` county yields $\times$ `USDA AMS` prices + forage value (boosted if `has_livestock == True`).

Weighted `overall_score`:
$$\text{Score} = \frac{\sum w_i S_i}{\sum w_i}$$
where $w_i$ maps directly to `FarmerPriorities` sliders (`0..10`). Hard constraint: if `rainfed_only == True`, apply a `-35` point penalty to any rotation whose water deficit exceeds soil storage capacity.

### F. Uncertainty & Ground-Truth Override Math
- Base confidence = `92%`.
- Subtract `cloud_interpolation_pct * 0.25`.
- Subtract `12%` if `soil.source != "USER_SOIL_TEST_OVERRIDE"`.
- When user submits a custom soil test override (e.g., updating pH or Organic Matter %), `soil.source` becomes `"USER_SOIL_TEST_OVERRIDE"`, confidence jumps by `+12%`, and pH-sensitive crops (e.g., Alfalfa if $\text{pH} < 6.0$) dynamically re-rank.

## 3. UI & Functional Acceptance Criteria
- [ ] **3 Hero Farms + Custom Click:** Instant switching between Finney Co (KS), Story Co (IA), and Fresno Co (CA), or clicking any map coordinate.
- [ ] **Satellite Layer Switcher:** Toggle between `USDA NAIP`, `USDA CDL`, `NASA MODIS NDVI`, `NASA SMAP`, and `NASA ECOSTRESS` on the MapLibre canvas.
- [ ] **12-Month Bare-Soil & Stress Timeline:** Displays `NDVI` greenness curve, red highlight blocks for bare-soil exposure windows, `GPM` rainfall bars, and `ECOSTRESS` thermal stress markers.
- [ ] **Interactive Sliders:** 5 Farmer Priority sliders, 2 hard constraint toggles (`Rainfed Only`, `Has Livestock`), and 2 Climate What-If sliders (`Rainfall %`, `Temperature +C`) re-rank the 4 strategy cards in `< 150ms`.
- [ ] **Complete Explainability per Card:** Every strategy card renders `why_suggested`, `nasa_evidence`, `agronomic_benefits`, `information_gaps`, and `risks_requiring_local_review`.
- [ ] **Plain-Language Tooltips & Extension Checklist:** Every scientific term (`NDVI`, `ESI`, `SMAP`, `SSURGO K-factor`) has a 1-sentence farmer tooltip, plus a printable/visible checklist of questions for a local agricultural extension officer.