"""Bare-soil detector, RUSLE erosion, thermal stress, uncertainty.

Phase 4 adds transparent, documented indicators computed from the real
ingested Phase 1 data (NASA POWER weather, USDA NRCS SSURGO soil, USDA NASS
CDL crops). All functions are pure: they take raw source values and return a
computed indicator with no fabrication, no interpolation, and no invented
confidence scores. Missing source values propagate as None.
"""

from statistics import mean
def detect_bare_soil(soil_type: str, vegetation_cover: float, rainfall: float) -> bool:
    """Detect if bare-soil erosion window is open."""
    # Simple threshold: low cover + sandy soil + rain > threshold
    return vegetation_cover < 0.3 and soil_type in ("Sand", "Sandy Loam") and rainfall > 20


def compute_rusle(rainfall: float, cover: float, erodibility: float, slope: float, length: float) -> float:
    """Compute RUSLE erosion risk 0-1."""
    # R = R * K * LS * C * P simplified
    r_factor = rainfall
    k_factor = erodibility
    ls_factor = (slope / 5.0) * (length / 100.0)
    c_factor = 1.0 - cover
    p_factor = 1.0
    return min(1.0, r_factor * k_factor * ls_factor * c_factor * p_factor)


def thermal_stress(temp_k: float, opt_temp_k: float = 295.0, range_k: float = 15.0) -> float:
    """Compute thermal stress index 0-1."""
    deviation = abs(temp_k - opt_temp_k)
    return min(1.0, deviation / range_k)


def evaporative_stress(temp_k: float, humidity: float) -> float:
    """Compute evaporative stress index 0-1.

    Higher temp + lower humidity = more stress.
    """
    return min(1.0, (temp_k - 273.0) / 30.0 * (1.0 - humidity / 100.0))


# ---------------------------------------------------------------------------
# Phase 4 indicators — computed from real ingested source data
# ---------------------------------------------------------------------------


def count_hot_days(daily_tmax: list[float | None], threshold_c: float = 34.0) -> dict:
    """Count days where daily maximum temperature exceeds a threshold.

    Returns {hot_day_count, total_days_reported, threshold_c, hot_day_fraction}.
    Missing (None) values are excluded from both counts.
    """
    reported = [v for v in daily_tmax if v is not None]
    hot = [v for v in reported if v > threshold_c]
    total = len(reported)
    return {
        "hot_day_count": len(hot),
        "total_days_reported": total,
        "threshold_c": threshold_c,
        "hot_day_fraction": round(len(hot) / total, 4) if total > 0 else None,
    }
def summarize_precipitation(daily_precip: list[float | None]) -> dict:
    """Summarize daily precipitation into total, mean, and wet-day count.

    Missing (None) values are excluded. All values in mm/day from the source.
    """
    reported = [v for v in daily_precip if v is not None]
    wet_days = [v for v in reported if v > 0]
    return {
        "total_mm": round(sum(reported), 2) if reported else None,
        "mean_mm_per_day": round(mean(reported), 2) if reported else None,
        "days_reported": len(reported),
        "wet_day_count": len(wet_days),
        "wet_day_fraction": round(len(wet_days) / len(reported), 4) if reported else None,
    }


def classify_soil_texture(sand_pct: float, silt_pct: float, clay_pct: float) -> str:
    """Classify soil texture using the USDA texture triangle.

    Percentages must sum to ~100. Returns a USDA texture class name, or
    "Unknown" if values are out of range or don't sum to ~100.
    """
    total = sand_pct + silt_pct + clay_pct
    if not (95.0 <= total <= 105.0):
        return "Unknown"
    if any(v < 0 for v in (sand_pct, silt_pct, clay_pct)):
        return "Unknown"

    clay = clay_pct
    sand = sand_pct
    silt = silt_pct

    if clay >= 40:
        if sand >= 45:
            return "Sandy clay"
        if silt >= 40:
            return "Silty clay"
        return "Clay"
    if clay >= 35:
        if sand > 45:
            return "Sandy clay loam"
        if silt >= 40:
            return "Silty clay loam"
        return "Clay loam"
    if clay >= 27:
        if sand <= 20 and silt >= 40:
            return "Silty clay loam"
        if sand <= 45:
            return "Clay loam"
        return "Sandy clay loam"
    if clay >= 20:
        if sand >= 45:
            return "Sandy clay loam"
        if silt >= 40:
            return "Silt loam"
        return "Loam"
    if clay >= 7:
        if sand >= 45:
            return "Sandy loam"
        if silt >= 40:
            return "Silt loam"
        return "Loam"
    if sand >= 45:
        if sand >= 85:
            return "Sand"
        return "Loamy sand"
    if silt >= 50:
        return "Silt"
    return "Loam"


def crop_diversity_score(crop_years: list[dict]) -> dict:
    """Compute crop-diversity indicators from CDL annual statistics.

    Takes a list of {year, crops: [{crop_name, share_pct}]} and returns:
    {dominant_crop, dominant_share_pct, distinct_crop_count, diversity_score}
    where diversity_score is the average per-year inverse-Herfindahl index
    (0 = monoculture every year, 100 = perfectly diverse every year).
    Shares are normalized within each year before computing diversity.
    """
    all_crops: set[str] = set()
    dominant = ("None", 0.0)
    yearly_diversities: list[float] = []
    years_with_data = 0

    for cy in crop_years:
        year_shares = [c.get("share_pct") for c in cy.get("crops", []) if c.get("share_pct") is not None]
        year_total = sum(year_shares)
        if year_total <= 0:
            continue
        years_with_data += 1

        # Normalize within this year so shares sum to 100%
        normalized_shares = []
        for c in cy.get("crops", []):
            share = c.get("share_pct")
            if share is None:
                continue
            normalized = share / year_total * 100.0
            normalized_shares.append(normalized)
            all_crops.add(c.get("crop_name", "Unknown"))
            if normalized > dominant[1]:
                dominant = (c.get("crop_name", "Unknown"), normalized)

        # Inverse-Herfindahl for this year: 100 * (1 - sum((s/100)^2))
        herfindahl = sum(s * s for s in normalized_shares) / 10000.0
        yearly_diversities.append(100.0 * (1.0 - herfindahl))

    if not yearly_diversities:
        return {
            "dominant_crop": None,
            "dominant_share_pct": None,
            "distinct_crop_count": 0,
            "diversity_score": None,
            "years_represented": 0,
        }

    diversity = round(max(0.0, sum(yearly_diversities) / len(yearly_diversities)), 2)
    return {
        "dominant_crop": dominant[0],
        "dominant_share_pct": round(dominant[1], 2),
        "distinct_crop_count": len(all_crops),
        "diversity_score": diversity,
        "years_represented": years_with_data,
    }