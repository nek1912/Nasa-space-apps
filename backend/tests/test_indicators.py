"""Offline tests for Phase 4 indicators computed from real ingested data."""

from app.services.si_diagnostics import (
    classify_soil_texture,
    count_hot_days,
    crop_diversity_score,
    summarize_precipitation,
)


def test_count_hot_days_counts_above_threshold() -> None:
    values = [30.0, 35.0, 40.0, None, 25.0, 34.0, 36.0]
    result = count_hot_days(values, threshold_c=34.0)
    assert result["hot_day_count"] == 3  # 35, 40, 36
    assert result["total_days_reported"] == 6  # excludes None
    assert result["threshold_c"] == 34.0
    assert result["hot_day_fraction"] == round(3 / 6, 4)


def test_count_hot_days_all_missing() -> None:
    result = count_hot_days([None, None, None], threshold_c=30.0)
    assert result["hot_day_count"] == 0
    assert result["total_days_reported"] == 0
    assert result["hot_day_fraction"] is None


def test_summarize_precipitation() -> None:
    values = [0.0, 5.0, 10.0, None, 0.0, 3.0]
    result = summarize_precipitation(values)
    assert result["total_mm"] == 18.0
    assert result["mean_mm_per_day"] == round(18.0 / 5, 2)
    assert result["days_reported"] == 5
    assert result["wet_day_count"] == 3  # 5, 10, 3
    assert result["wet_day_fraction"] == round(3 / 5, 4)


def test_summarize_precipitation_all_missing() -> None:
    result = summarize_precipitation([None, None])
    assert result["total_mm"] is None
    assert result["days_reported"] == 0


def test_classify_soil_texture_known_classes() -> None:
    assert classify_soil_texture(40, 40, 20) == "Silt loam"
    assert classify_soil_texture(85, 10, 5) == "Sand"
    assert classify_soil_texture(20, 60, 20) == "Silt loam"
    assert classify_soil_texture(45, 35, 20) == "Sandy clay loam"
    assert classify_soil_texture(20, 20, 60) == "Clay"


def test_classify_soil_texture_invalid() -> None:
    assert classify_soil_texture(50, 30, 30) == "Unknown"  # sums to 110
    assert classify_soil_texture(-1, 50, 50) == "Unknown"  # negative
    assert classify_soil_texture(0, 0, 0) == "Unknown"  # sums to 0


def test_crop_diversity_score_monoculture() -> None:
    crop_years = [
        {
            "year": 2021,
            "crops": [
                {"crop_name": "Corn", "share_pct": 100.0},
            ],
        }
    ]
    result = crop_diversity_score(crop_years)
    assert result["dominant_crop"] == "Corn"
    assert result["dominant_share_pct"] == 100.0
    assert result["distinct_crop_count"] == 1
    assert result["diversity_score"] == 0.0


def test_crop_diversity_score_diverse() -> None:
    crop_years = [
        {
            "year": 2021,
            "crops": [
                {"crop_name": "Corn", "share_pct": 50.0},
                {"crop_name": "Soybeans", "share_pct": 50.0},
            ],
        }
    ]
    result = crop_diversity_score(crop_years)
    assert result["distinct_crop_count"] == 2
    # Herfindahl = (50^2 + 50^2)/10000 = 0.5, diversity = 100*(1-0.5) = 50
    assert result["diversity_score"] == 50.0


def test_crop_diversity_score_empty() -> None:
    result = crop_diversity_score([])
    assert result["dominant_crop"] is None
    assert result["diversity_score"] is None