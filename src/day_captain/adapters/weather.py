"""Weather provider adapters for Day Captain."""

from datetime import datetime
import json
from typing import Any
from typing import Callable
from typing import Mapping
from typing import Optional
from urllib import error
from urllib import parse
from urllib import request
from zoneinfo import ZoneInfo

from day_captain.models import WeatherSnapshot


class WeatherApiError(RuntimeError):
    """Raised when a weather provider response cannot be used."""


class OpenMeteoWeatherProvider:
    def __init__(
        self,
        *,
        latitude: float,
        longitude: float,
        location_name: str = "",
        base_url: str = "https://api.open-meteo.com/v1/forecast",
        timeout_seconds: int = 10,
        opener: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.location_name = str(location_name or "").strip()
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._opener = opener or request.urlopen

    def get_weather(
        self,
        current_time: datetime,
        display_timezone: str,
    ) -> Optional[WeatherSnapshot]:
        timezone_name = _normalized_timezone(display_timezone)
        payload = self._fetch_payload(timezone_name)
        daily = payload.get("daily")
        if not isinstance(daily, Mapping):
            raise WeatherApiError("Expected `daily` weather payload from Open-Meteo.")

        times = tuple(str(item) for item in daily.get("time") or ())
        temperature_maxes = tuple(daily.get("temperature_2m_max") or ())
        temperature_mins = tuple(daily.get("temperature_2m_min") or ())
        weather_codes = tuple(daily.get("weather_code") or ())
        if not times:
            return None

        target_date = current_time.astimezone(ZoneInfo(timezone_name)).date().isoformat()
        try:
            index = times.index(target_date)
        except ValueError as exc:
            raise WeatherApiError("Open-Meteo response did not include the target forecast day.") from exc

        try:
            temperature_max = float(temperature_maxes[index])
            temperature_min = float(temperature_mins[index])
            weather_code = int(weather_codes[index])
        except (IndexError, TypeError, ValueError) as exc:
            raise WeatherApiError("Open-Meteo response was missing expected daily temperature fields.") from exc

        previous_temperature = None
        if index > 0:
            try:
                previous_temperature = float(temperature_maxes[index - 1])
            except (TypeError, ValueError):
                previous_temperature = None

        return WeatherSnapshot(
            forecast_date=current_time.astimezone(ZoneInfo(timezone_name)).date(),
            weather_code=weather_code,
            temperature_max_c=temperature_max,
            temperature_min_c=temperature_min,
            location_name=self.location_name,
            previous_temperature_max_c=previous_temperature,
        )

    def _fetch_payload(self, timezone_name: str) -> Mapping[str, Any]:
        params = {
            "latitude": "{0:.6f}".format(self.latitude),
            "longitude": "{0:.6f}".format(self.longitude),
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "forecast_days": 1,
            "past_days": 1,
            "timezone": timezone_name,
        }
        url = "{0}?{1}".format(self.base_url, parse.urlencode(params))
        req = request.Request(url, headers={"Accept": "application/json"}, method="GET")
        try:
            with self._opener(req, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise WeatherApiError("Weather request failed with {0}: {1}".format(exc.code, detail)) from exc
        except error.URLError as exc:
            raise WeatherApiError("Unable to reach weather provider: {0}".format(exc.reason)) from exc
        payload = json.loads(raw or "{}")
        if not isinstance(payload, dict):
            raise WeatherApiError("Expected weather provider JSON object response.")
        return payload


def _normalized_timezone(value: str) -> str:
    candidate = str(value or "").strip() or "UTC"
    try:
        ZoneInfo(candidate)
    except Exception:
        return "UTC"
    return candidate
