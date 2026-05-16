"""Backtests tecnicos para snapshots tabulares."""

from __future__ import annotations

from pathlib import Path

from .pipeline import validate_csv


def run_contract_backtest(input_dir: str | Path, contract_path: str | Path) -> dict[str, object]:
    """Executa validacao de contrato para todos os CSVs de uma pasta."""
    directory = Path(input_dir)
    files = sorted(directory.glob("*.csv"))

    if not files:
        return {
            "is_valid": False,
            "snapshots": [],
            "errors": [f"Nenhum CSV encontrado em {directory}."],
        }

    snapshots: list[dict[str, object]] = []
    for file_path in files:
        validation = validate_csv(file_path, contract_path)
        snapshots.append(
            {
                "file": str(file_path),
                "is_valid": validation.is_valid,
                "row_count": validation.row_count,
                "errors": validation.errors,
            }
        )

    return {
        "is_valid": all(snapshot["is_valid"] for snapshot in snapshots),
        "snapshots": snapshots,
        "errors": [
            error
            for snapshot in snapshots
            for error in snapshot["errors"]
        ],
    }

