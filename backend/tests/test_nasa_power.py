"""Offline parser tests for NASA POWER daily responses."""

import json

from app.services.nasa_power import parse_power_daily

FIXTURE_PATH = "tests/fixtures/power_daily_sample.json"


def _load_fixture(name: str) -> dict:
    import pathlib

    return json.loads(pathlib.Path(name).read_text())


def test_parse_power_daily_units_and_values() -> None:
    raw = _load_fixture(FIXTURE_PATH)
    parsed = parse_power_daily(raw)

    assert parsed["time_standard"] == "UTC"
    params = {p["parameter"]: p for p in parsed["parameters"]}

    tmax = params["T2M_MAX"]
    assert tmax["units"] == "C"
    assert tmax["long_name"] == "Temperature at 2 Meters Maximum"
    dates = [d["date"] for d in tmax["daily"]]
    assert dates == ["20210101", "20210102", "20210103"]
    assert tmax["daily"][0]["value"] == -3.64
    # The source fill value (-999) is normalized to null, never invented.
    assert tmax["daily"][1]["value"] is None
    assert tmax["daily"][2]["value"] == 0.8

    precip = params["PRECTOTCORR"]
    assert precip["units"] == "mm/day"
    assert precip["daily"][0]["value"] == 0.04
    assert precip["daily"][2]["value"] == 0.0