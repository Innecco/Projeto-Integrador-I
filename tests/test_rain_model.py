import tempfile
import unittest
from pathlib import Path

from src.projeto_integrador.features import build_rain_features
from src.projeto_integrador.rain_model import (
    evaluate_forecast_threshold,
    fit_rain_probability_model,
    temporal_split,
    train_and_backtest,
)
from src.projeto_integrador.pipeline import read_csv


FIXTURES = Path(__file__).parent / "fixtures"


class RainModelTest(unittest.TestCase):
    def test_model_fits_and_predicts_probability(self) -> None:
        rows = [
            {
                "month": "1",
                "rain_today": "0",
                "forecast_precipitation_tomorrow_mm": "2.0",
                "target_rain_tomorrow": "1",
                "date": "2024-01-01",
            },
            {
                "month": "1",
                "rain_today": "1",
                "forecast_precipitation_tomorrow_mm": "3.0",
                "target_rain_tomorrow": "1",
                "date": "2024-01-02",
            },
            {
                "month": "7",
                "rain_today": "0",
                "forecast_precipitation_tomorrow_mm": "0.0",
                "target_rain_tomorrow": "0",
                "date": "2024-07-01",
            },
            {
                "month": "7",
                "rain_today": "1",
                "forecast_precipitation_tomorrow_mm": "0.1",
                "target_rain_tomorrow": "0",
                "date": "2024-07-02",
            },
        ]

        model = fit_rain_probability_model(rows)
        probability = model.predict_proba(rows[0])

        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)
        self.assertEqual(model.train_row_count, 4)
        self.assertEqual(model.model_name, "calibrated_forecast_threshold")

    def test_forecast_threshold_metrics_are_calculated(self) -> None:
        rows = [
            {"forecast_precipitation_tomorrow_mm": "2.0", "target_rain_tomorrow": "1", "date": "2024-01-01"},
            {"forecast_precipitation_tomorrow_mm": "0.0", "target_rain_tomorrow": "0", "date": "2024-01-02"},
        ]

        metrics = evaluate_forecast_threshold(rows, threshold_mm=1.0)

        self.assertEqual(metrics["accuracy"], 1.0)

    def test_train_and_backtest_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            features_path = temp_path / "features.csv"
            report_path = temp_path / "report.json"
            model_path = temp_path / "model.json"
            build_rain_features(FIXTURES / "weather_raw_sample.csv", features_path)

            report = train_and_backtest(
                features_path,
                split_date="2024-01-04",
                report_path=report_path,
                model_path=model_path,
            )

            self.assertTrue(report_path.exists())
            self.assertTrue(model_path.exists())
            self.assertIn("test_metrics", report)

    def test_temporal_split_preserves_time_order(self) -> None:
        rows = read_csv(FIXTURES / "weather_raw_sample.csv")
        train_rows, test_rows = temporal_split(rows, "2024-01-04")

        self.assertEqual(train_rows[-1]["date"], "2024-01-03")
        self.assertEqual(test_rows[0]["date"], "2024-01-04")


if __name__ == "__main__":
    unittest.main()
