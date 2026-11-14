"""Offline tests for WMS URL building (no network)."""

from app.services.wms import build_wms_getmap_url, CDL_LAYERS, SSURGO_LAYERS, STORY_COUNTY_BBOX


def test_build_wms_getmap_url_cdl() -> None:
    url = build_wms_getmap_url(
        "https://crop.csiss.gmu.edu/cgi-bin/wms_cdl_ia?",
        ["cdl_2021_ia"],
        STORY_COUNTY_BBOX,
    )
    assert "SERVICE=WMS" in url
    assert "VERSION=1.1.1" in url
    assert "REQUEST=GetMap" in url
    assert "LAYERS=cdl_2021_ia" in url
    assert "SRS=EPSG:4326" in url
    assert "BBOX=-93.8,41.8,-93.3,42.3" in url
    assert "FORMAT=image/png" in url
    assert "TRANSPARENT=TRUE" in url


def test_build_wms_getmap_url_ssurgo() -> None:
    url = build_wms_getmap_url(
        "https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms?",
        ["MapunitPoly"],
        STORY_COUNTY_BBOX,
    )
    assert "LAYERS=MapunitPoly" in url
    assert "SRS=EPSG:4326" in url
    assert "BBOX=-93.8,41.8,-93.3,42.3" in url


def test_cdl_layers_cover_phase1_years() -> None:
    for year in (2021, 2022, 2023, 2024, 2025):
        assert year in CDL_LAYERS
        assert CDL_LAYERS[year] == f"cdl_{year}_ia"


def test_ssurgo_layers_verified() -> None:
    assert "MapunitPoly" in SSURGO_LAYERS
    assert "SurveyAreaPoly" in SSURGO_LAYERS