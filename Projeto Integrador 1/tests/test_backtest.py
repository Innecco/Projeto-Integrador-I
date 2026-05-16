import unittest
from pathlib import Path

from src.projeto_integrador.backtest import run_contract_backtest


FIXTURES = Path(__file__).parent / "fixtures"
CONTRACT = FIXTURES / "contract.sample.json"


class BacktestTest(unittest.TestCase):
    def test_contract_backtest_validates_all_snapshots(self) -> None:
        report = run_contract_backtest(FIXTURES / "backtest_snapshots", CONTRACT)

        self.assertTrue(report["is_valid"])
        self.assertEqual(len(report["snapshots"]), 2)
        self.assertEqual(report["errors"], [])

    def test_contract_backtest_reports_empty_directory(self) -> None:
        report = run_contract_backtest(FIXTURES / "missing_snapshots", CONTRACT)

        self.assertFalse(report["is_valid"])
        self.assertEqual(report["snapshots"], [])
        self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()

