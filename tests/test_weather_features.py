import tempfile
import unittest
from pathlib import Path

from src.projeto_integrador.features import build_rain_features
from src.projeto_integrador.pipeline import read_csv


FIXTURES = Path(__file__).parent / "fixtures"


class WeatherFeatureTest(unittest.TestCase):
    def test_build_rain_features_uses_next_day_as_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "features.csv"

            report = build_rain_features(
                FIXTURES / "weather_raw_sample.csv",
                output_path,
                rain_threshold_mm=1.0,
            )
            rows = read_csv(output_path)

        self.assertEqual(report["input_rows"], 5)
        self.assertEqual(report["feature_rows"], 4)
        self.assertEqual(rows[0]["date"], "2024-01-01")
        self.assertEqual(rows[0]["target_date"], "2024-01-02")
        self.assertEqual(rows[0]["rain_today"], "0")
        self.assertEqual(rows[0]["forecast_available"], "0")
        self.assertEqual(rows[0]["forecast_precipitation_tomorrow_mm"], "")
        self.assertEqual(rows[0]["forecast_rain_tomorrow"], "")
        self.assertEqual(rows[0]["target_rain_tomorrow"], "1")
        self.assertEqual(rows[1]["rain_today"], "1")
        self.assertEqual(rows[1]["target_rain_tomorrow"], "0")


if __name__ == "__main__":
    unittest.main()
