"""Offline tests for the Phase 4/5 rotation engine."""

from app.services.rotation_engine import (
    build_baseline_sequence,
    recommend_rotations,
)


def test_build_baseline_sequence_from_cdl() -> None:
    cdl_crops = [
        {
            "year": 2021,
            "classified_acres": 150.0,
            "crops": [
                {"crop_name": "Corn", "crop_code": 1, "acres": 100.0, "share_pct": 66.67},
                {"crop_name": "Soybeans", "crop_code": 5, "acres": 50.0, "share_pct": 33.33},
            ],
        },
        {
            "year": 2022,
            "classified_acres": 160.0,
            "crops": [
                {"crop_name": "Corn", "crop_code": 1, "acres": 120.0, "share_pct": 75.0},
                {"crop_name": "Soybeans", "crop_code": 5, "acres": 40.0, "share_pct": 25.0},
            ],
        },
    ]
    result = build_baseline_sequence(cdl_crops)
    assert "Corn" in result
    assert result[0] == "Corn"  # highest share crop


def test_build_baseline_sequence_empty() -> None:
    result = build_baseline_sequence([])
    assert result == ["Corn", "Soybean"]


def test_recommend_rotations_returns_4_strategies() -> None:
    cdl_crops = [
        {
            "year": 2021,
            "classified_acres": 150.0,
            "crops": [
                {"crop_name": "Corn", "crop_code": 1, "acres": 100.0, "share_pct": 66.67},
                {"crop_name": "Soybeans", "crop_code": 5, "acres": 50.0, "share_pct": 33.33},
            ],
        }
    ]
    weather_indicators = {
        "temperature": {"hot_day_count": 61, "hot_day_fraction": 0.0334},
        "precipitation": {"total_mm": 3761.38, "days_reported": 1826},
    }
    crop_diversity = {
        "diversity_score": 70.92,
        "distinct_crop_count": 41,
        "dominant_crop": "Corn",
    }
    result = recommend_rotations(cdl_crops, "Clay loam", weather_indicators, crop_diversity)

    assert len(result["strategies"]) == 4
    assert result["baseline_strategy_id"] == 0
    assert result["strategies"][0]["is_baseline"] is True
    assert result["strategies"][0]["sequence"] == ["Corn", "Soybeans"]

    # All strategies should have 6 scores with overall_score
    for s in result["strategies"]:
        assert set(s["scores"].keys()) == {
            "water_efficiency",
            "soil_health",
            "erosion_armor",
            "pest_disruption",
            "climate_resilience",
            "market_return",
        }
        assert 0 <= s["overall_score"] <= 100
        assert s["why_suggested"]
        assert s["nasa_evidence"]
        assert s["agronomic_benefits"]
        assert s["information_gaps"]
        assert s["risks_requiring_local_review"]

    # Non-baseline strategies should be sorted by overall_score descending
    non_baseline = [s for s in result["strategies"] if not s["is_baseline"]]
    scores = [s["overall_score"] for s in non_baseline]
    assert scores == sorted(scores, reverse=True)


def test_recommend_rotations_empty_cdl() -> None:
    result = recommend_rotations([], None, {"temperature": {}, "precipitation": {}}, {})
    assert len(result["strategies"]) == 4
    assert result["strategies"][0]["sequence"] == ["Corn", "Soybean"]