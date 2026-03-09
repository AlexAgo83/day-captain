from datetime import datetime
from datetime import timezone
from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.adapters.weather import OpenMeteoWeatherProvider
from day_captain.adapters.weather import WeatherApiError


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class OpenMeteoWeatherProviderTest(unittest.TestCase):
    def test_parses_today_and_previous_day_temperatures(self) -> None:
        payload = {
            "daily": {
                "time": ["2026-03-08", "2026-03-09"],
                "weather_code": [3, 61],
                "temperature_2m_max": [11.0, 13.4],
                "temperature_2m_min": [5.2, 6.1],
            }
        }
        provider = OpenMeteoWeatherProvider(
            latitude=48.8566,
            longitude=2.3522,
            location_name="Paris",
            opener=lambda req, timeout=0: _FakeResponse(payload),
        )

        snapshot = provider.get_weather(
            current_time=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            display_timezone="Europe/Paris",
        )

        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.location_name, "Paris")
        self.assertEqual(snapshot.weather_code, 61)
        self.assertEqual(snapshot.temperature_max_c, 13.4)
        self.assertEqual(snapshot.previous_temperature_max_c, 11.0)

    def test_raises_when_target_day_is_missing(self) -> None:
        payload = {
            "daily": {
                "time": ["2026-03-08"],
                "weather_code": [3],
                "temperature_2m_max": [11.0],
                "temperature_2m_min": [5.2],
            }
        }
        provider = OpenMeteoWeatherProvider(
            latitude=48.8566,
            longitude=2.3522,
            opener=lambda req, timeout=0: _FakeResponse(payload),
        )

        with self.assertRaises(WeatherApiError):
            provider.get_weather(
                current_time=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
                display_timezone="Europe/Paris",
            )


if __name__ == "__main__":
    unittest.main()
