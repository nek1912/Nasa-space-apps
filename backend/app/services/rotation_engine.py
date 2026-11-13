"""Multi-objective crop sequence ranker + climate perturbation."""


def rank_rotations(crop_sequence: list[str], soil_data: dict, climate_perturbation: float = 0.0) -> dict:
    """Rank a crop sequence by multiple objectives and return scores."""
    scores = []
    for i, crop in enumerate(crop_sequence):
        # Base score from crop type
        base = 1.0 if not crop.lower().startswith("c") else 0.8
        # Perturbation factor
        perturbation = 1.0 + climate_perturbation * (-1) ** i
        scores.append(base * perturbation)

    total = sum(scores) / len(scores) if scores else 0.0
    return {
        "sequence": crop_sequence,
        "score": round(total, 3),
        "per_crop_scores": {crop: s for crop, s in zip(crop_sequence, scores)},
    }