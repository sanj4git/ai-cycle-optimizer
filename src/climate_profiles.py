"""
Regional climate profiles for Indian precast yards.
Maps city/region to typical temperature, humidity, and monsoon characteristics.
"""

CLIMATE_PROFILES = {
    "Chennai (South)": {
        "region": "South",
        "ambient_temp_c": 34.0,
        "ambient_rh_pct": 78.0,
        "monsoon_flag": 0,
        "monsoon_temp_c": 28.0,
        "monsoon_rh_pct": 92.0,
        "label": "Humid-Hot",
        "icon": "🌴",
        "description": "High humidity year-round. Steam curing less effective due to moisture saturation."
    },
    "Delhi (North)": {
        "region": "North",
        "ambient_temp_c": 32.0,
        "ambient_rh_pct": 55.0,
        "monsoon_flag": 0,
        "monsoon_temp_c": 30.0,
        "monsoon_rh_pct": 85.0,
        "label": "Seasonal Extremes",
        "icon": "🏙️",
        "description": "Hot summers, cold winters. Winter curing can be very slow below 15°C."
    },
    "Rajasthan (West)": {
        "region": "West",
        "ambient_temp_c": 38.0,
        "ambient_rh_pct": 30.0,
        "monsoon_flag": 0,
        "monsoon_temp_c": 32.0,
        "monsoon_rh_pct": 65.0,
        "label": "Dry-Hot",
        "icon": "🏜️",
        "description": "Very low humidity accelerates surface drying. Moist curing critical."
    },
    "Mumbai (West)": {
        "region": "West",
        "ambient_temp_c": 30.0,
        "ambient_rh_pct": 82.0,
        "monsoon_flag": 0,
        "monsoon_temp_c": 27.0,
        "monsoon_rh_pct": 95.0,
        "label": "Coastal Humid",
        "icon": "🌊",
        "description": "Coastal humidity and salt air. Long monsoon season affects outdoor curing."
    },
    "Kolkata (East)": {
        "region": "East",
        "ambient_temp_c": 31.0,
        "ambient_rh_pct": 75.0,
        "monsoon_flag": 0,
        "monsoon_temp_c": 28.0,
        "monsoon_rh_pct": 90.0,
        "label": "Tropical Humid",
        "icon": "🌿",
        "description": "High humidity with extended monsoon. Moderate temperatures year-round."
    }
}

def get_profile(city: str, monsoon: bool = False) -> dict:
    """Get climate parameters for a city, optionally during monsoon."""
    profile = CLIMATE_PROFILES[city].copy()
    if monsoon:
        profile["ambient_temp_c"] = profile["monsoon_temp_c"]
        profile["ambient_rh_pct"] = profile["monsoon_rh_pct"]
        profile["monsoon_flag"] = 1
    return profile

def get_city_names() -> list:
    return list(CLIMATE_PROFILES.keys())
