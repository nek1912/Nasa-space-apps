"""Bare-soil detector, RUSLE erosion, thermal stress, uncertainty."""


def detect_bare_soil(soil_type: str, vegetation_cover: float, rainfall: float) -> bool:
    """Detect if bare-soil erosion window is open."""
    # Simple threshold: low cover + sandy soil + rain > threshold
    return vegetation_cover < 0.3 and soil_type in ("Sand", "Sandy Loam") and rainfall > 20


def compute_rusle(rainfall: float, cover: float, erodibility: float, slope: float, length: float) -> float:
    """Compute RUSLE erosion risk 0-1."""
    # R = R * K * LS * C * P simplified
    r_factor = rainfall
    k_factor = erodibility
    ls_factor = (slope / 5.0) * (length / 100.0)
    c_factor = 1.0 - cover
    p_factor = 1.0
    return min(1.0, r_factor * k_factor * ls_factor * c_factor * p_factor)


def thermal_stress(temp_k: float, opt_temp_k: float = 295.0, range_k: float = 15.0) -> float:
    """Compute thermal stress index 0-1."""
    deviation = abs(temp_k - opt_temp_k)
    return min(1.0, deviation / range_k)


def evaporative_stress(temp_k: float, humidity: float) -> float:
    """Compute evaporative stress index 0-1."""
    # Higher temp + lower humidity = more stress
    return min(1.0, (temp_k - 273.0) / 30.0 * (1.0 - humidity / 100.0))