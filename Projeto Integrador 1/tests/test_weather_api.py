import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from src.projeto_integrador.weather_api import fetch_multi_city_weather_to_csv, write_weather_csv


class WeatherApiTest(unittest.TestCase):
    def test_multi_city_fetch_uses_cached_csv_when_api_is_rate_limited(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_dir = root / "raw"
            config_path = root / "locations.json"
            combined_path = raw_dir / "weather_multi_city_daily.csv"

            locations = [
                {"id": "brasilia", "name": "Brasilia", "state": "DF", "latitude": -15.7, "longitude": -47.8},
                {"id": "goiania", "name": "Goiania", "state": "GO", "latitude": -16.6, "longitude": -49.2},
            ]
            config_path.write_text(
                json.dumps({"source_name": "Open-Meteo", "locations": locations}),
                encoding="utf-8",
            )

            for location in locations:
                write_weather_csv(
                    [
                        {
                            "city_id": location["id"],
                            "city_name": location["name"],
                            "state": location["state"],
                            "date": "2026-01-01",
                            "temperature_2m_mean": "22.0",
                            "precipitation_sum": "1.0",
                        }
                    ],
                    raw_dir / f"weather_{location['id']}_daily.csv",
                )

            error = urllib.error.HTTPError(
                url="https://archive-api.open-meteo.com/v1/archive",
                code=429,
                msg="Too Many Requests",
                hdrs=None,
                fp=None,
            )
            with patch("src.projeto_integrador.weather_api.fetch_archive_payload", side_effect=error):
                report = fetch_multi_city_weather_to_csv(config_path, raw_dir, combined_path)

            self.assertTrue(report["used_cached_data"])
            self.assertEqual(report["row_count"], 2)
            self.assertTrue(combined_path.exists())
            self.assertTrue(all(city["used_cached_data"] for city in report["cities"]))


if __name__ == "__main__":
    unittest.main()
