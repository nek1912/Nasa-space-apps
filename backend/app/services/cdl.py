"""USDA NASS Cropland Data Layer statistics via CropScape GetCDLStat.

GetCDLStat itself returns an XML document containing a ``returnURL`` to the
actual row-level JSON cache. We follow that URL and save both responses
unmodified. Only the fields the Phase 1 UI needs are parsed.
"""

from __future__ import annotations

import ast
import json
import re
import xml.etree.ElementTree as ET

import httpx

CDL_STAT_URL = "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLStat"
CDL_NAMESPACE = "{http://cropscape.csiss.gmu.edu/CDLService/}"

TIMEOUT = 30.0


class CdlError(RuntimeError):
    """Raised when the CDL service cannot be reached or returns unusable data."""


def _parse_cdl_cache(text: str) -> dict:
    """Parse a CDL cache response that may be JavaScript object notation, not strict JSON.

    The CropScape cache returns unquoted property names (e.g. {success:true, rows:[...]}),
    which json.loads rejects. We try strict JSON first, then fix up property names
    and use ast.literal_eval as a fallback.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Quote unquoted property names: word chars at { or , followed by optional ws and :
    fixed = re.sub(r"([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', text)
    # JavaScript booleans are not valid Python literals
    fixed = fixed.replace("true", "True").replace("false", "False")
    return ast.literal_eval(fixed)


def fetch_cdl_stat(year: int, county_fips: str) -> dict:
    """Request CDL county statistics for one year and return the parsed JSON cache."""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(
                CDL_STAT_URL,
                params={"year": year, "fips": county_fips, "format": "json"},
            )
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
            # The returnURL element is unprefixed (no namespace), so search without
            # a namespace qualifier even though the root element is namespaced.
            return_url = root.find("returnURL")
            if return_url is None or not return_url.text:
                # Fallback: try with the root's namespace in case the service changes.
                return_url = root.find(f"{CDL_NAMESPACE}returnURL")
            if return_url is None or not return_url.text:
                raise CdlError(
                    f"GetCDLStat returned no returnURL for year {year}, FIPS {county_fips}: {resp.text[:200]}"
                )
            cache = client.get(return_url.text)
            cache.raise_for_status()
            return _parse_cdl_cache(cache.text)
    except CdlError:
        raise
    except Exception as exc:
        raise CdlError(f"CDL GetCDLStat failed for year {year}, FIPS {county_fips}: {exc}") from exc


def parse_cdl_stat(raw: dict, year: int) -> dict:
    """Parse a GetCDLStat JSON cache into {year, classified_acres, crops[]}."""
    rows = raw.get("rows", []) if isinstance(raw, dict) else []
    crops: list[dict] = []
    total_acres = 0.0
    for row in rows:
        acres = float(row.get("acreage") or 0.0)
        total_acres += acres
        crops.append(
            {
                "crop_name": row.get("category"),
                "crop_code": row.get("value"),
                "acres": acres,
                "share_pct": None,
            }
        )
    for crop in crops:
        crop["share_pct"] = (crop["acres"] / total_acres * 100.0) if total_acres > 0 else None
    return {"year": year, "classified_acres": total_acres or None, "crops": crops}