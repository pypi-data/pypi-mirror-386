# tests/test_client_sync.py
import responses
from openweather import OpenWeatherClient, NotFoundError

BASE = "https://api.openweathermap.org/data/2.5"

def _cw_payload(name="Pune", temp=27.0, desc="clear sky"):
    return {
        "name": name,
        "weather": [{"id": 1, "main": "Clear", "description": desc, "icon": "01d"}],
        "main": {
            "temp": temp, "feels_like": temp, "temp_min": temp, "temp_max": temp,
            "pressure": 1000, "humidity": 40
        },
        "wind": {"speed": 1.2, "deg": 90},
        "sys": {"country": "IN"},
    }

@responses.activate
def test_current_weather_success_raw_dict():
    responses.add(
        responses.GET,
        f"{BASE}/weather",
        json=_cw_payload(name="Pune", temp=27.0),
        status=200,
    )
    c = OpenWeatherClient(api_key="k")
    data = c.get_current_weather(city="Pune")
    assert data["name"] == "Pune"
    assert isinstance(data["main"]["temp"], (int, float))

@responses.activate
def test_404_raises_not_found():
    responses.add(
        responses.GET,
        f"{BASE}/weather",
        json={"message": "city not found"},
        status=404,
    )
    c = OpenWeatherClient(api_key="k")
    try:
        c.get_current_weather(city="NopeCity")
        assert False, "Expected NotFoundError"
    except NotFoundError as e:
        assert "not found" in str(e).lower()

@responses.activate
def test_5xx_then_success_triggers_retry_and_returns_data():
    # First call -> 503, second call -> 200
    responses.add(
        responses.GET, f"{BASE}/weather",
        json={"message": "service unavailable"},
        status=503,
    )
    responses.add(
        responses.GET, f"{BASE}/weather",
        json=_cw_payload(name="Pune", temp=25.0),
        status=200,
    )
    c = OpenWeatherClient(api_key="k", max_retries=1)  # allow a single retry
    data = c.get_current_weather(city="Pune")
    assert data["name"] == "Pune"
    assert len(responses.calls) == 2  # verify retry happened