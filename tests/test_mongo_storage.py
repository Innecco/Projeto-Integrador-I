import unittest

from src.projeto_integrador.mongo_storage import MongoStorage


class MongoStorageTest(unittest.TestCase):
    def test_weather_rows_are_upserted_and_sorted(self) -> None:
        storage = MongoStorage("mongomock://local", "test_predicao_chuvas")
        rows = [
            {"city_id": "brasilia", "date": "2026-01-02", "precipitation_sum": "0.0"},
            {"city_id": "brasilia", "date": "2026-01-01", "precipitation_sum": "1.2"},
        ]

        report = storage.upsert_weather_rows(rows)
        stored_rows = storage.list_weather_rows("brasilia")

        self.assertEqual(report["row_count"], 2)
        self.assertEqual([row["date"] for row in stored_rows], ["2026-01-01", "2026-01-02"])
        self.assertEqual(stored_rows[0]["precipitation_sum"], "1.2")

    def test_feature_rows_keep_city_metadata_in_mongo(self) -> None:
        storage = MongoStorage("mongomock://local", "test_predicao_chuvas_features")

        report = storage.upsert_feature_rows(
            [{"date": "2026-01-01", "target_rain_tomorrow": "1"}],
            city_id="brasilia",
        )
        stored = storage.database.rain_features.find_one({"city_id": "brasilia"})

        self.assertEqual(report["row_count"], 1)
        self.assertEqual(stored["date"], "2026-01-01")


if __name__ == "__main__":
    unittest.main()
