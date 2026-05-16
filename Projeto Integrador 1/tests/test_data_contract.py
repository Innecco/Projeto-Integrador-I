import unittest
from pathlib import Path

from src.projeto_integrador.pipeline import validate_csv
from src.projeto_integrador.data_contract import DataContract, validate_rows


FIXTURES = Path(__file__).parent / "fixtures"
CONTRACT = FIXTURES / "contract.sample.json"


class DataContractTest(unittest.TestCase):
    def test_valid_csv_passes_contract_validation(self) -> None:
        result = validate_csv(FIXTURES / "sample_valid.csv", CONTRACT)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.row_count, 3)
        self.assertEqual(result.errors, [])

    def test_invalid_csv_reports_quality_errors(self) -> None:
        result = validate_csv(FIXTURES / "sample_invalid.csv", CONTRACT)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.row_count, 3)
        self.assertTrue(any("chave duplicada" in error for error in result.errors))
        self.assertTrue(any("nao e numerico" in error for error in result.errors))
        self.assertTrue(any("esta vazia" in error for error in result.errors))

    def test_composite_unique_columns_are_validated(self) -> None:
        contract = DataContract(
            required_columns=("city_id", "date", "value"),
            unique_columns=("city_id", "date"),
        )
        rows = [
            {"city_id": "brasilia", "date": "2026-01-01", "value": "1"},
            {"city_id": "brasilia", "date": "2026-01-01", "value": "2"},
        ]

        result = validate_rows(rows, contract)

        self.assertFalse(result.is_valid)
        self.assertTrue(any("chave composta duplicada" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
