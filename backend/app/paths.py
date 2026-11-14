"""Path helpers for the FieldShift backend.

Single place that knows where the repo's config, raw downloads and processed
data live, so services and scripts never rebuild paths by hand.
"""

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = BACKEND_ROOT / "config"
DATA_DIR = BACKEND_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

REGION_CONFIG_PATH = CONFIG_DIR / "region.json"
PROCESSED_REGION_SUMMARY_PATH = PROCESSED_DIR / "story_county.json"