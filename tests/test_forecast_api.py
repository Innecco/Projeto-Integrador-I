import unittest

from src.projeto_integrador.forecast_api import (
    previous_day1_payload_to_daily_rows,
    split_date_range_by_year,
)


class ForecastApiTest(unittest.TestCase):
    def test_previous_day1_payload_is_aggregated_by_day(self) -> None:
        payload = {
            "hourly": {
                "time": [
                    "2026-01-01T00:00",
                    "2026-01-01T01:00",
                    "2026-01-02T00:00",
                ],
                "precipitation_previous_day1": [0.2, 0.9, 0.0],
            }
        }
        location = {"id": "brasilia", "name": "Brasilia", "state": "DF"}

        rows = previous_day1_payload_to_daily_rows(payload, location, rain_threshold_mm=1.0)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["date"], "2026-01-01")
        self.assertEqual(rows[0]["forecast_precipitation_sum"], "1.100")
        self.assertEqual(rows[0]["forecast_rain"], "1")
        self.assertEqual(rows[1]["forecast_rain"], "0")

    def test_date_range_is_split_by_year(self) -> None:
        chunks = split_date_range_by_year("2025-12-30", "2026-01-02")

        self.assertEqual(chunks, [("2025-12-30", "2025-12-31"), ("2026-01-01", "2026-01-02")])


if __name__ == "__main__":
    unittest.main()
