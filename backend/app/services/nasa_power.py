"""Live NASA POWER daily/climatology REST + fallback."""

import httpx
from fastapi import HTTPException

POWER_BASE = "https://power.larc.nasa.gov/api/temporal/daily/parameters"


def fetch_power_data(lat: float, lon: float, params: dict):
    """Fetch data from NASA POWER API with local fallback."""
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(POWER_BASE, params={**{"latitude": lat, "longitude": lon}, **params})
            resp.raise_for_status()
            return resp.json()
    except Exception:
        # Fallback: return structured placeholder
        return {
            "parameters": {
                "T2M": {"value": [300.0]},  # K
                "RH2M": {"value": [50.0]},
                "PRECTOT": {"value": [0.0]},
            }
        }