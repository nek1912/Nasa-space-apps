"""Offline parser tests for USDA NRCS SDA SSURGO responses."""

import json

from app.services.usda_soil import parse_soil_data

FIXTURE_PATH = "tests/fixtures/ssurgo_sample.json"


def _load_fixture(name: str) -> dict:
    import pathlib

    return json.loads(pathlib.Path(name).read_text())


def test_parse_soil_data_groups_by_map_unit() -> None:
    raw = _load_fixture(FIXTURE_PATH)
    units = parse_soil_data(raw)

    assert len(units) == 2
    unit_a = units[0]
    assert unit_a["mukey"] == "1001"
    assert unit_a["map_unit_name"] == "Mukey A loam"
    assert unit_a["available_water_storage_cm"] == 12.5
    assert len(unit_a["components"]) == 1
    comp = unit_a["components"][0]
    assert comp["component_name"] == "Loam component"
    assert comp["component_pct"] == 85
    assert len(comp["horizons"]) == 2
    assert comp["horizons"][0] == {"depth_top_cm": 0, "depth_bottom_cm": 15, "sand_pct": 40, "silt_pct": 40, "clay_pct": 20}
    assert comp["horizons"][1] == {"depth_top_cm": 15, "depth_bottom_cm": 30, "sand_pct": 35, "silt_pct": 45, "clay_pct": 20}

    unit_b = units[1]
    assert unit_b["mukey"] == "1002"
    assert len(unit_b["components"][0]["horizons"]) == 1