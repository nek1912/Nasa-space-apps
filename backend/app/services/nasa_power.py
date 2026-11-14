"""Live NASA POWER daily point weather + parser.

No placeholder fallback: on timeout or HTTP error the caller records the
source as unavailable and continues with the other providers.
"""

from __future__ import annotations

import httpx

POWER_BASE = "https://power.larc.nasa.gov/api/temporal/daily/point"
TIMEOUT = 30.0
FILL_VALUE = -999.0


class PowerError(RuntimeError):
    """Raised when the NASA POWER request fails."""


def fetch_power_daily(
    latitude: float,
    longitude: float,
    parameters: list[str],
    start_date: str,
    end_date: str,
) -> dict:
    """Request daily POWER data and return the raw JSON response."""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(
                POWER_BASE,
                params={
                    "parameters": ",".join(parameters),
                    "community": "AG",
                    "longitude": longitude,
                    "latitude": latitude,
                    "start": start_date.replace("-", ""),
                    "end": end_date.replace("-", ""),
                    "format": "JSON",
                    "time-standard": "UTC",
                },
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        raise PowerError(f"NASA POWER request failed: {exc}") from exc


def parse_power_daily(raw: dict) -> dict:
    """Parse a POWER daily response into per-parameter series with units."""
    header = raw.get("header", {}) or {}
    params_meta = raw.get("parameters", {}) or {}
    daily_blocks = (raw.get("properties") or {}).get("parameter", {}) or {}
    fill_value = header.get("fill_value", FILL_VALUE)

    parameters_out: list[dict] = []
    for param_name, values in daily_blocks.items():
        meta = params_meta.get(param_name, {}) or {}
        daily: list[dict] = []
        for date_str, value in values.items():
            daily.append(
                {"date": date_str, "value": None if value == fill_value else float(value)}
            )
        daily.sort(key=lambda d: d["date"])
        parameters_out.append(
            {
                "parameter": param_name,
                "units": meta.get("units"),
                "long_name": meta.get("longname"),
                "daily": daily,
            }
        )
    parameters_out.sort(key=lambda p: p["parameter"])
    return {
        "geometry": raw.get("geometry"),
        "time_standard": header.get("time_standard"),
        "parameters": parameters_out,
    }