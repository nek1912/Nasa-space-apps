"""Live USGS SRTM slope/TWI & NWIS groundwater + fallback."""


def fetch_terrain_water_data(lat: float, lon: float):
    """Fetch slope, TWI, and groundwater data for a location."""
    # Placeholder - would query USGS elevation/hydro APIs
    return {
        "slope_percent": 5.0,
        "twi": 12.5,
        "groundwater_depth_m": 2.3,
    }