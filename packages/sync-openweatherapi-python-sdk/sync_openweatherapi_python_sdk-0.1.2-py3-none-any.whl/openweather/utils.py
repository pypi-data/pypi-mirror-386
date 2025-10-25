from typing import Dict, Optional

DEFAULT_TIMEOUT = 15  # seconds

def build_common_params(api_key: str, units: str = "metric", lang: str = "en") -> Dict[str, str]:
    return {"appid": api_key, "units": units, "lang": lang}

def coalesce_location(
    *,
    city: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    city_id: Optional[int] = None,
) -> Dict[str, str]:
    """Return query params for location. Prefers (lat, lon) > city_id > city name."""
    if lat is not None and lon is not None:
        return {"lat": str(lat), "lon": str(lon)}
    if city_id is not None:
        return {"id": str(city_id)}
    if city:
        return {"q": city}
    raise ValueError("Provide either city, (lat & lon), or city_id")