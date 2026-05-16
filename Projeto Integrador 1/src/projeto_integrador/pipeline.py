"""Pipeline minimo para leitura, validacao e escrita de relatorios."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .config import load_json
from .data_contract import DataContract, ValidationResult, validate_rows


def read_csv(path: str | Path) -> list[dict[str, str]]:
    """Le um CSV UTF-8 e retorna linhas como dicionarios."""
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def validate_csv(input_path: str | Path, contract_path: str | Path) -> ValidationResult:
    """Valida um CSV a partir de um contrato JSON."""
    contract = DataContract.from_mapping(load_json(contract_path))
    rows = read_csv(input_path)
    return validate_rows(rows, contract)


def write_json_report(report: dict[str, object], output_path: str | Path) -> None:
    """Grava um relatorio JSON com criacao automatica da pasta destino."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write("\n")

