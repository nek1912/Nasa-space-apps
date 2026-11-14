import json
from pathlib import Path
from typing import Any

from app.paths import (
    PROCESSED_DIR,
    PROCESSED_REGION_SUMMARY_PATH,
    RAW_DIR,
    REGION_CONFIG_PATH,
)


class SourceDataUnavailable(Exception):
    """Raised when a provider's data was never ingested or cannot be used."""


def load_region_config() -> dict[str, Any]:
    """Load the single active region configuration."""
    with open(REGION_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_raw_response(source_id: str, filename: str, payload: Any) -> Path:
    """Persist an unmodified provider response under `data/raw/<source_id>/`."""
    target_dir = RAW_DIR / source_id
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def save_processed_summary(payload: dict[str, Any]) -> Path:
    """Write the normalized region summary consumed by the API."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_REGION_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return PROCESSED_REGION_SUMMARY_PATH


def load_processed_summary() -> dict[str, Any]:
    """Read the processed region summary, raising if it was never generated."""
    if not PROCESSED_REGION_SUMMARY_PATH.exists():
        raise SourceDataUnavailable(
            "No processed region data found. Run `python scripts/ingest_story_county.py` first."
        )
    with open(PROCESSED_REGION_SUMMARY_PATH, encoding="utf-8") as f:
        return json.load(f)