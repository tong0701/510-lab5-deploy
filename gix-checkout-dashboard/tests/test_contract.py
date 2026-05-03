import requests

UW_FORECAST = (
    "https://api.open-meteo.com/v1/forecast?"
    "latitude=47.6566&longitude=-122.3035"
    "&daily=precipitation_sum&timezone=America/Los_Angeles&forecast_days=3"
)


def test_open_meteo_valid_uw_coordinates():
    r = requests.get(UW_FORECAST, timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "daily" in data
    assert "precipitation_sum" in data["daily"]
    assert len(data["daily"]["precipitation_sum"]) == 3


def test_open_meteo_invalid_extreme_latitude():
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        "latitude=999&longitude=-122.3035"
        "&daily=precipitation_sum&timezone=America/Los_Angeles&forecast_days=3"
    )
    r = requests.get(url, timeout=5)
    if r.status_code != 200:
        assert r.status_code != 200
        return
    data = r.json()
    assert "error" in data or "reason" in str(data).lower()


def test_open_meteo_non_numeric_latitude():
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        "latitude=abc&longitude=-122.3035"
        "&daily=precipitation_sum&timezone=America/Los_Angeles&forecast_days=3"
    )
    r = requests.get(url, timeout=5)
    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    assert r.status_code != 200 or "error" in data
