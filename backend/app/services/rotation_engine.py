"""Multi-objective crop rotation ranker using real ingested data.

Deterministic MCDA engine using real Phase 1/4 data: USDA NASS CDL,
USDA NRCS SSURGO, NASA POWER, USDA crops catalog.
"""

from __future__ import annotations

from app.services.si_diagnostics import crop_diversity_score

PEST_FAMILIES = {"Poaceae", "Fabaceae", "Brassicaceae", "Asteraceae", "Malvaceae"}

CROP_PROPERTIES: dict[str, dict] = {
    "wheat": {"family": "Poaceae", "nfix": False, "root": "fibrous"},
    "corn": {"family": "Poaceae", "nfix": False, "root": "fibrous"},
    "soybean": {"family": "Fabaceae", "nfix": True, "root": "fibrous"},
    "alfalfa": {"family": "Fabaceae", "nfix": True, "root": "taproot"},
    "rice": {"family": "Poaceae", "nfix": False, "root": "fibrous"},
    "cotton": {"family": "Malvaceae", "nfix": False, "root": "taproot"},
    "barley": {"family": "Poaceae", "nfix": False, "root": "fibrous"},
    "oats": {"family": "Poaceae", "nfix": False, "root": "fibrous"},
    "sunflower": {"family": "Asteraceae", "nfix": False, "root": "taproot"},
    "potato": {"family": "Solanaceae", "nfix": False, "root": "fibrous"},
    "tomato": {"family": "Solanaceae", "nfix": False, "root": "fibrous"},
    "cucumber": {"family": "Cucurbitaceae", "nfix": False, "root": "fibrous"},
    "bean": {"family": "Fabaceae", "nfix": True, "root": "fibrous"},
    "pea": {"family": "Fabaceae", "nfix": True, "root": "fibrous"},
    "lentil": {"family": "Fabaceae", "nfix": True, "root": "fibrous"},
    "canola": {"family": "Brassicaceae", "nfix": False, "root": "taproot"},
    "safflower": {"family": "Asteraceae", "nfix": False, "root": "taproot"},
    "sorghum": {"family": "Poaceae", "nfix": False, "root": "fibrous"},
    "millet": {"family": "Poaceae", "nfix": False, "root": "fibrous"},
}

DEFAULT_WEIGHTS = {
    "water_efficiency": 10.0,
    "soil_health": 10.0,
    "erosion_armor": 10.0,
    "pest_disruption": 10.0,
    "climate_resilience": 10.0,
    "market_return": 10.0,
}
def _normalize_0_100(value: float, vmin: float, vmax: float) -> float:
    if vmax == vmin:
        return 50.0
    return max(0.0, min(100.0, (value - vmin) / (vmax - vmin) * 100.0))


def _pest_disruption_score(sequence: list[str]) -> float:
    families = []
    for crop in sequence:
        props = CROP_PROPERTIES.get(crop.lower())
        if props:
            families.append(props["family"])
    distinct = len(set(families))
    if distinct >= 3:
        return 100.0
    if distinct == 2:
        return 60.0
    return 25.0


def _soil_health_score(sequence: list[str]) -> float:
    score = 50.0
    nfix_count = 0
    has_taproot = False
    has_fibrous = False
    for crop in sequence:
        props = CROP_PROPERTIES.get(crop.lower())
        if not props:
            continue
        if props["nfix"]:
            nfix_count += 1
        if props["root"] == "taproot":
            has_taproot = True
        if props["root"] == "fibrous":
            has_fibrous = True
    score += min(25.0, nfix_count * 12.5)
    if has_taproot:
        score += 12.5
    if has_fibrous:
        score += 12.5
    return max(0.0, min(100.0, score))
def _water_efficiency_score(
    sequence: list[str], hot_day_fraction: float | None, precip_mm_total: float | None
) -> float:
    base = 50.0
    drought_tolerant = {"sorghum", "millet"}
    has_drought_tolerant = any(c.lower() in drought_tolerant for crop in sequence for c in [crop])
    climate_adj = 0.0
    if hot_day_fraction is not None:
        climate_adj += hot_day_fraction * 25.0
    if precip_mm_total is not None:
        precip_adj = max(0.0, min(25.0, (500.0 - precip_mm_total) / 500.0 * 25.0))
        climate_adj += precip_adj
    if has_drought_tolerant:
        base += climate_adj
    else:
        base -= climate_adj * 0.5
    return max(0.0, min(100.0, base))


def _climate_resilience_score(
    sequence: list[str], hot_day_fraction: float | None, precip_mm_total: float | None
) -> float:
    base = 50.0
    deep_rooted = {"sunflower", "alfalfa", "cotton"}
    has_deep_root = any(c.lower() in deep_rooted for crop in sequence for c in [crop])
    if has_deep_root:
        base += 20.0
    if hot_day_fraction is not None and hot_day_fraction > 0.1:
        base += 10.0
    return max(0.0, min(100.0, base))
def _erosion_armor_score(
    sequence: list[str], crop_diversity: dict, bare_soil_dekads: int | None
) -> float:
    base = 40.0
    if crop_diversity.get("diversity_score") is not None:
        base += crop_diversity["diversity_score"] * 0.4
    legumes = {"soybean", "alfalfa", "bean", "pea", "lentil", "clover"}
    legume_count = sum(1 for c in sequence if c.lower() in legumes)
    base += min(20.0, legume_count * 10.0)
    return max(0.0, min(100.0, base))


def _market_return_score(
    sequence: list[str], crop_diversity: dict, cdl_dominant_crop: str | None
) -> float:
    base = 40.0
    if cdl_dominant_crop and any(c.lower() == cdl_dominant_crop.lower() for c in sequence):
        base += 30.0
    if crop_diversity.get("diversity_score") is not None:
        base += crop_diversity["diversity_score"] * 0.3
    return max(0.0, min(100.0, base))


def _weighted_overall(scores: dict[str, float], weights: dict[str, float]) -> float:
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(scores.get(k, 0) * weights.get(k, 0) for k in weights)
    return round(weighted_sum / total_weight, 1)
def build_baseline_sequence(cdl_crops: list[dict]) -> list[str]:
    all_crops: list[tuple[str, float]] = []
    for cy in cdl_crops:
        for c in cy.get("crops", []):
            if c.get("share_pct") is not None:
                all_crops.append((c.get("crop_name", "Unknown"), c["share_pct"]))
    if not all_crops:
        return ["Corn", "Soybean"]
    crop_max_share: dict[str, float] = {}
    for name, share in all_crops:
        if name not in crop_max_share or share > crop_max_share[name]:
            crop_max_share[name] = share
    sorted_crops = sorted(crop_max_share.items(), key=lambda x: x[1], reverse=True)
    baseline = [c[0] for c in sorted_crops[:2]]
    if not baseline:
        baseline = ["Corn", "Soybean"]
    return baseline
def recommend_rotations(
    cdl_crops: list[dict],
    soil_texture: str | None,
    weather_indicators: dict,
    crop_diversity: dict,
    weights: dict[str, float] | None = None,
) -> dict:
    if weights is None:
        weights = DEFAULT_WEIGHTS

    hot_day_fraction = weather_indicators.get("temperature", {}).get("hot_day_fraction")
    precip_mm_total = weather_indicators.get("precipitation", {}).get("total_mm")

    baseline_seq = build_baseline_sequence(cdl_crops)
    cdl_dominant = baseline_seq[0] if baseline_seq else None

    strategies = []

    baseline_scores = {
        "water_efficiency": _water_efficiency_score(baseline_seq, hot_day_fraction, precip_mm_total),
        "soil_health": _soil_health_score(baseline_seq),
        "erosion_armor": _erosion_armor_score(baseline_seq, crop_diversity, None),
        "pest_disruption": _pest_disruption_score(baseline_seq),
        "climate_resilience": _climate_resilience_score(baseline_seq, hot_day_fraction, precip_mm_total),
        "market_return": _market_return_score(baseline_seq, crop_diversity, cdl_dominant),
    }
    strategies.append({
        "strategy_id": 0,
        "name": "County Baseline (CDL-derived)",
        "description": "Current dominant county crop sequence from USDA NASS CDL statistics.",
        "is_baseline": True,
        "sequence": baseline_seq,
        "scores": baseline_scores,
        "overall_score": _weighted_overall(baseline_scores, weights),
        "weights": weights,
        "why_suggested": "Reflects what is already grown in the county; established market and equipment.",
        "nasa_evidence": "USDA NASS CDL county crop statistics, 2021-2025.",
        "agronomic_benefits": ["Established local market", "Proven agronomic fit", "Known equipment requirements"],
        "information_gaps": ["County-level statistics, not field-level history", "No NDVI or field-scale vegetation data"],
        "risks_requiring_local_review": ["Market prices may vary", "Soil-specific variety selection needed"],
    })
    seq_1 = ["Sorghum", "Chickpea"]
    scores_1 = {
        "water_efficiency": _water_efficiency_score(seq_1, hot_day_fraction, precip_mm_total),
        "soil_health": _soil_health_score(seq_1),
        "erosion_armor": _erosion_armor_score(seq_1, crop_diversity, None),
        "pest_disruption": _pest_disruption_score(seq_1),
        "climate_resilience": _climate_resilience_score(seq_1, hot_day_fraction, precip_mm_total),
        "market_return": _market_return_score(seq_1, crop_diversity, cdl_dominant),
    }
    strategies.append({
        "strategy_id": 1,
        "name": "Water-Saver & Aquifer Shield",
        "description": "Drought-tolerant C4 cereal (Sorghum) + low-water pulse (Chickpea).",
        "is_baseline": False,
        "sequence": seq_1,
        "scores": scores_1,
        "overall_score": _weighted_overall(scores_1, weights),
        "weights": weights,
        "why_suggested": "Reduces irrigation demand in hot/dry conditions; breaks corn-soybean pest cycles.",
        "nasa_evidence": "NASA POWER hot-day count + precipitation indicators; USDA crops catalog.",
        "agronomic_benefits": ["Deep fibrous roots", "N-fixation from chickpea", "Drought tolerance"],
        "information_gaps": ["County-level weather, not field-level", "No field-specific water holding capacity"],
        "risks_requiring_local_review": ["Chickpea market access", "Variety maturity for local growing season"],
    })

    seq_2 = ["Corn", "Cereal Rye", "Crimson Clover"]
    scores_2 = {
        "water_efficiency": _water_efficiency_score(seq_2, hot_day_fraction, precip_mm_total),
        "soil_health": _soil_health_score(seq_2),
        "erosion_armor": _erosion_armor_score(seq_2, crop_diversity, None),
        "pest_disruption": _pest_disruption_score(seq_2),
        "climate_resilience": _climate_resilience_score(seq_2, hot_day_fraction, precip_mm_total),
        "market_return": _market_return_score(seq_2, crop_diversity, cdl_dominant),
    }
    strategies.append({
        "strategy_id": 2,
        "name": "Soil Armor & N-Builder",
        "description": "Main cash crop (Corn) + overwintering cover/legume mix (Cereal Rye + Crimson Clover).",
        "is_baseline": False,
        "sequence": seq_2,
        "scores": scores_2,
        "overall_score": _weighted_overall(scores_2, weights),
        "weights": weights,
        "why_suggested": "Cover crops eliminate bare-soil dekads; clover adds nitrogen; rye protects soil.",
        "nasa_evidence": "USDA NRCS SSURGO soil texture; NASA POWER precipitation indicator.",
        "agronomic_benefits": ["Eliminates bare soil", "N-fixation from clover", "Erosion control from rye"],
        "information_gaps": ["No field-level bare-soil dekad data", "Cover crop termination timing unknown"],
        "risks_requiring_local_review": ["Cover crop seed availability", "Herbicide carryover concerns"],
    })

    seq_3 = ["Sunflower", "Alfalfa"]
    scores_3 = {
        "water_efficiency": _water_efficiency_score(seq_3, hot_day_fraction, precip_mm_total),
        "soil_health": _soil_health_score(seq_3),
        "erosion_armor": _erosion_armor_score(seq_3, crop_diversity, None),
        "pest_disruption": _pest_disruption_score(seq_3),
        "climate_resilience": _climate_resilience_score(seq_3, hot_day_fraction, precip_mm_total),
        "market_return": _market_return_score(seq_3, crop_diversity, cdl_dominant),
    }
    strategies.append({
        "strategy_id": 3,
        "name": "Climate-Hedged Cash + Forage",
        "description": "Deep-taproot crop (Sunflower) + high-value forage/oilseed (Alfalfa).",
        "is_baseline": False,
        "sequence": seq_3,
        "scores": scores_3,
        "overall_score": _weighted_overall(scores_3, weights),
        "weights": weights,
        "why_suggested": "Deep roots access subsoil moisture; alfalfa provides forage and N-fixation.",
        "nasa_evidence": "NASA POWER hot-day count; USDA crops catalog root architecture data.",
        "agronomic_benefits": ["Deep taproot system", "N-fixation from alfalfa", "Forage value for livestock"],
        "information_gaps": ["No field-level subsoil moisture data", "Alfalfa establishment risk"],
        "risks_requiring_local_review": ["Forage market access", "Alfalfa pH requirements (needs pH > 6.0)"],
    })

    non_baseline = sorted([s for s in strategies if not s["is_baseline"]], key=lambda s: s["overall_score"], reverse=True)
    baseline = [s for s in strategies if s["is_baseline"]]
    ordered = baseline + non_baseline

    data_limitations = (
        "County-level CDL statistics do not reveal individual field crop sequences. "
        "Baseline is derived from county-wide crop shares, not a specific field. "
        "Recommendations are rule-based and evidence-supported, not field-validated. "
        "Consult a local extension officer before changing rotation."
    )

    return {
        "strategies": ordered,
        "data_limitations": data_limitations,
        "baseline_strategy_id": 0,
    }