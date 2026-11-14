"""Offline parser tests for USDA NASS CDL GetCDLStat JSON caches."""

import json

from app.services.cdl import parse_cdl_stat

FIXTURE_PATH = "tests/fixtures/cdl_sample.json"


def _load_fixture(name: str) -> dict:
    import pathlib

    return json.loads(pathlib.Path(name).read_text())


def test_parse_cdl_stat_acres_and_shares() -> None:
    raw = _load_fixture(FIXTURE_PATH)
    parsed = parse_cdl_stat(raw, 2021)

    assert parsed["year"] == 2021
    assert parsed["classified_acres"] == 150.0
    crops = {c["crop_name"]: c for c in parsed["crops"]}
    assert crops["Corn"]["crop_code"] == 1
    assert crops["Corn"]["acres"] == 100.0
    assert crops["Corn"]["share_pct"] == 100.0 / 150.0 * 100.0
    assert crops["Soybeans"]["share_pct"] == 50.0 / 150.0 * 100.0
    # Shares of reported acres sum to 100%.
    assert abs(sum(c["share_pct"] for c in parsed["crops"]) - 100.0) < 1e-6