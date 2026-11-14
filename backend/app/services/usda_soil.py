"""Live USDA NRCS Soil Data Access (SSURGO) client + parser.

No hardcoded fallback values: on failure the caller records the source as
unavailable and continues with the other providers.
"""

from __future__ import annotations

SDA_URL = "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest"
TIMEOUT = 30.0


class SdaError(RuntimeError):
    """Raised when the Soil Data Access request fails."""


def _post_query(sql: str) -> dict:
    import httpx

    body = {
        "SERVICE": "query",
        "REQUEST": "query",
        "FORMAT": "JSON+COLUMNNAME",
        "QUERY": sql,
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.post(SDA_URL, data=body)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        raise SdaError(f"SSURGO SDA request failed: {exc}") from exc


def confirm_survey_area(state: str, county_name: str) -> str | None:
    """Look up the SSURGO survey-area symbol for a state/county."""
    sql = (
        "SELECT areasymbol, areaname FROM legend "
        f"WHERE areasymbol LIKE '{state}%' AND areaname LIKE '%{county_name}%'"
    )
    raw = _post_query(sql)
    rows = raw.get("rows", []) if isinstance(raw, dict) else []
    if rows:
        return rows[0][0]
    return None


def fetch_soil_data(areasymbol: str) -> dict:
    """Fetch major components and horizon attributes for a survey area."""
    sql = (
        "SELECT l.areasymbol, mu.mukey, mu.musym, mu.muname, c.compname, "
        "c.comppct_r, ch.hzdept_r, ch.hzdepb_r, ch.sandtotal_r, ch.silttotal_r, "
        "ch.claytotal_r, ma.aws025wta "
        "FROM legend l "
        "JOIN mapunit mu ON mu.lkey = l.lkey "
        "JOIN component c ON c.mukey = mu.mukey "
        "LEFT JOIN chorizon ch ON ch.cokey = c.cokey "
        "LEFT JOIN muaggatt ma ON ma.mukey = mu.mukey "
        f"WHERE l.areasymbol = '{areasymbol}' AND c.majcompflag = 'yes' "
        "ORDER BY mu.musym, c.comppct_r DESC, ch.hzdept_r"
    )
    return _post_query(sql)


def parse_soil_data(raw: dict) -> list[dict]:
    """Parse SDA response into map units grouped by mukey.

    The SDA JSON+COLUMNNAME response is ``{"Table": [[headers], [row1], [row2], ...]}``
    where the first inner array lists column names and subsequent arrays are rows.
    """
    table = raw.get("Table", []) if isinstance(raw, dict) else []
    if not table:
        return []
    columns = table[0]
    rows = table[1:]

    units: dict[str, dict] = {}
    for row in rows:
        record = dict(zip(columns, row))
        mukey = str(record.get("mukey"))
        if mukey not in units:
            units[mukey] = {
                "mukey": mukey,
                "musym": record.get("musym"),
                "map_unit_name": record.get("muname"),
                "available_water_storage_cm": record.get("aws025wta"),
                "components": {},
            }
        comp = units[mukey]["components"].setdefault(
            record.get("compname"),
            {
                "component_name": record.get("compname"),
                "component_pct": record.get("comppct_r"),
                "horizons": [],
            },
        )
        if record.get("hzdept_r") is not None:
            comp["horizons"].append(
                {
                    "depth_top_cm": record.get("hzdept_r"),
                    "depth_bottom_cm": record.get("hzdepb_r"),
                    "sand_pct": record.get("sandtotal_r"),
                    "silt_pct": record.get("silttotal_r"),
                    "clay_pct": record.get("claytotal_r"),
                }
            )

    result = []
    for mu in units.values():
        mu["components"] = list(mu["components"].values())
        result.append(mu)
    result.sort(key=lambda m: m["musym"] or m["mukey"])
    return result