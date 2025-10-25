from __future__ import annotations
from typing import Any, Dict, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from .endpoints import BASE_URL_V25, CURRENT_WEATHER, FORECAST_5DAY_3H
from .exceptions import (
    OpenWeatherError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from .utils import build_common_params, coalesce_location, DEFAULT_TIMEOUT


class OpenWeatherClient:
    """Synchronous OpenWeatherMap client with connection pooling & retries."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL_V25,
        timeout: Union[int, float] = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._session = session or requests.Session()
        retry = Retry(
            total=max_retries,
            read=max_retries,
            connect=max_retries,
            status=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=50)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def get_current_weather(
        self,
        *,
        city: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        city_id: Optional[int] = None,
        units: str = "metric",
        lang: str = "en",
        as_model: bool = False,
    ) -> Dict[str, Any]:
        params = build_common_params(self.api_key, units=units, lang=lang)
        params.update(coalesce_location(city=city, lat=lat, lon=lon, city_id=city_id))
        url = f"{self.base_url}{CURRENT_WEATHER}"
        data = self._get(url, params)
        if as_model:
            from .models import CurrentWeather
            return CurrentWeather.model_validate(data)  # type: ignore[return-value]
        return data

    def get_forecast(
        self,
        *,
        city: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        city_id: Optional[int] = None,
        units: str = "metric",
        lang: str = "en",
        as_model: bool = False,
    ) -> Dict[str, Any]:
        params = build_common_params(self.api_key, units=units, lang=lang)
        params.update(coalesce_location(city=city, lat=lat, lon=lon, city_id=city_id))
        url = f"{self.base_url}{FORECAST_5DAY_3H}"
        data = self._get(url, params)
        if as_model:
            from .models import Forecast
            return Forecast.model_validate(data)  # type: ignore[return-value]
        return data

    def _get(self, url: str, params: Dict[str, str]) -> Dict[str, Any]:
        resp = self._session.get(url, params=params, timeout=self.timeout)
        return self._handle_response(resp)

    @staticmethod
    def _handle_response(resp: requests.Response) -> Dict[str, Any]:
        if resp.status_code == 200:
            return resp.json()
        try:
            payload = resp.json()
            message = payload.get("message") or payload
        except Exception:
            message = resp.text
        if resp.status_code in (401, 403):
            raise AuthenticationError(message)
        if resp.status_code == 404:
            raise NotFoundError(message)
        if resp.status_code == 429:
            raise RateLimitError(message)
        if 500 <= resp.status_code < 600:
            raise ServerError(message)
        raise OpenWeatherError(f"Unexpected {resp.status_code}: {message}")