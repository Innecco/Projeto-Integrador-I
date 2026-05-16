"""Validacao simples de contratos de dados tabulares."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class DataContract:
    """Contrato minimo esperado para um arquivo tabular."""

    required_columns: tuple[str, ...]
    numeric_columns: tuple[str, ...] = ()
    unique_key: str | None = None
    unique_columns: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> "DataContract":
        """Cria um contrato a partir de um dicionario."""
        required_columns = _as_tuple(data.get("required_columns"), "required_columns")
        numeric_columns = _as_tuple(data.get("numeric_columns", []), "numeric_columns")
        unique_columns = _as_tuple(data.get("unique_columns", []), "unique_columns")
        unique_key = data.get("unique_key")

        if unique_key is not None and not isinstance(unique_key, str):
            raise ValueError("unique_key deve ser texto ou nulo.")

        return cls(
            required_columns=required_columns,
            numeric_columns=numeric_columns,
            unique_key=unique_key,
            unique_columns=unique_columns,
        )


@dataclass
class ValidationResult:
    """Resultado consolidado da validacao."""

    row_count: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Indica se a validacao passou sem erros."""
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        """Serializa o resultado para relatorios JSON."""
        return {
            "is_valid": self.is_valid,
            "row_count": self.row_count,
            "errors": self.errors,
        }


def validate_rows(rows: Iterable[dict[str, str]], contract: DataContract) -> ValidationResult:
    """Valida linhas tabulares contra o contrato informado."""
    materialized_rows = list(rows)
    result = ValidationResult(row_count=len(materialized_rows))

    if not materialized_rows:
        result.errors.append("O arquivo nao contem registros.")
        return result

    available_columns = set(materialized_rows[0].keys())
    missing_columns = sorted(set(contract.required_columns) - available_columns)
    if missing_columns:
        result.errors.append(f"Colunas obrigatorias ausentes: {', '.join(missing_columns)}.")
        return result

    _validate_required_values(materialized_rows, contract, result)
    _validate_numeric_values(materialized_rows, contract, result)
    _validate_unique_key(materialized_rows, contract, result)
    _validate_unique_columns(materialized_rows, contract, result)

    return result


def _validate_required_values(
    rows: list[dict[str, str]],
    contract: DataContract,
    result: ValidationResult,
) -> None:
    for row_number, row in enumerate(rows, start=2):
        for column in contract.required_columns:
            if row.get(column, "").strip() == "":
                result.errors.append(
                    f"Linha {row_number}: coluna obrigatoria '{column}' esta vazia."
                )


def _validate_numeric_values(
    rows: list[dict[str, str]],
    contract: DataContract,
    result: ValidationResult,
) -> None:
    for row_number, row in enumerate(rows, start=2):
        for column in contract.numeric_columns:
            value = row.get(column, "").strip()
            if value == "":
                continue
            try:
                float(value.replace(",", "."))
            except ValueError:
                result.errors.append(
                    f"Linha {row_number}: valor '{value}' na coluna '{column}' nao e numerico."
                )


def _validate_unique_key(
    rows: list[dict[str, str]],
    contract: DataContract,
    result: ValidationResult,
) -> None:
    if contract.unique_key is None:
        return

    seen: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        value = row.get(contract.unique_key, "").strip()
        if value in seen:
            result.errors.append(
                f"Linha {row_number}: chave duplicada na coluna '{contract.unique_key}': {value}."
            )
        seen.add(value)


def _validate_unique_columns(
    rows: list[dict[str, str]],
    contract: DataContract,
    result: ValidationResult,
) -> None:
    if not contract.unique_columns:
        return

    seen: set[tuple[str, ...]] = set()
    for row_number, row in enumerate(rows, start=2):
        value = tuple(row.get(column, "").strip() for column in contract.unique_columns)
        if value in seen:
            columns = ", ".join(contract.unique_columns)
            result.errors.append(
                f"Linha {row_number}: chave composta duplicada nas colunas {columns}: {value}."
            )
        seen.add(value)


def _as_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} deve ser uma lista de textos.")

    return tuple(value)
