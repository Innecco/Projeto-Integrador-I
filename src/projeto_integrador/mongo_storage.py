"""Camada de persistencia MongoDB do projeto."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Iterable

from .env import load_project_env


DEFAULT_MONGO_URI = "mongodb://localhost:27017"
DEFAULT_MONGO_DATABASE = "predicao_chuvas_brasilia"


class MongoStorage:
    """Repositorio pequeno e explicito para as colecoes do projeto."""

    def __init__(self, uri: str, database_name: str) -> None:
        self.uri = uri
        self.database_name = database_name
        self.client = _create_client(uri)
        self.database = self.client[database_name]
        self.ensure_indexes()

    @classmethod
    def from_env(cls) -> "MongoStorage":
        """Cria conexao usando `.env` e variaveis do ambiente."""
        load_project_env()
        uri = os.getenv("MONGO_URI", DEFAULT_MONGO_URI)
        database_name = os.getenv("MONGO_DATABASE", DEFAULT_MONGO_DATABASE)
        return cls(uri=uri, database_name=database_name)

    def ping(self) -> None:
        """Valida a conexao com o MongoDB quando o driver real esta em uso."""
        if self.uri.startswith("mongomock://"):
            return
        self.client.admin.command("ping")

    def ensure_indexes(self) -> None:
        """Cria indices das colecoes operacionais."""
        self.database.weather_daily.create_index(
            [("city_id", 1), ("date", 1)],
            unique=True,
            name="ux_weather_daily_city_date",
        )
        self.database.weather_forecasts.create_index(
            [("city_id", 1), ("date", 1), ("forecast_horizon", 1)],
            unique=True,
            name="ux_weather_forecast_city_date_horizon",
        )
        self.database.rain_features.create_index(
            [("city_id", 1), ("date", 1)],
            unique=True,
            name="ux_rain_features_city_date",
        )
        self.database.rain_predictions.create_index(
            [("city_id", 1), ("date", 1)],
            unique=True,
            name="ux_rain_predictions_city_date",
        )

    def upsert_weather_rows(self, rows: Iterable[dict[str, Any]]) -> dict[str, object]:
        """Grava observacoes meteorologicas diarias por cidade e data."""
        return self._upsert_rows(
            "weather_daily",
            rows,
            key_fields=("city_id", "date"),
        )

    def list_weather_rows(self, city_id: str | None = None) -> list[dict[str, str]]:
        """Le observacoes meteorologicas ordenadas."""
        filters: dict[str, object] = {}
        if city_id:
            filters["city_id"] = city_id
        return self._list_rows("weather_daily", filters, [("city_id", 1), ("date", 1)])

    def upsert_forecast_rows(self, rows: Iterable[dict[str, Any]]) -> dict[str, object]:
        """Grava previsoes operacionais de chuva por cidade, data e horizonte."""
        return self._upsert_rows(
            "weather_forecasts",
            rows,
            key_fields=("city_id", "date", "forecast_horizon"),
        )

    def list_forecast_rows(self, city_id: str | None = None) -> list[dict[str, str]]:
        """Le previsoes operacionais ordenadas."""
        filters: dict[str, object] = {}
        if city_id:
            filters["city_id"] = city_id
        return self._list_rows("weather_forecasts", filters, [("city_id", 1), ("date", 1)])

    def upsert_feature_rows(
        self,
        rows: Iterable[dict[str, Any]],
        city_id: str,
    ) -> dict[str, object]:
        """Grava features supervisionadas da cidade alvo."""
        materialized_rows = []
        for row in rows:
            document = dict(row)
            document["city_id"] = city_id
            materialized_rows.append(document)
        return self._upsert_rows(
            "rain_features",
            materialized_rows,
            key_fields=("city_id", "date"),
        )

    def upsert_prediction_rows(
        self,
        rows: Iterable[dict[str, Any]],
        city_id: str,
    ) -> dict[str, object]:
        """Grava predicoes geradas pelo modelo."""
        materialized_rows = []
        for row in rows:
            document = dict(row)
            document["city_id"] = city_id
            materialized_rows.append(document)
        return self._upsert_rows(
            "rain_predictions",
            materialized_rows,
            key_fields=("city_id", "date"),
        )

    def save_run_report(self, report: dict[str, object]) -> None:
        """Registra o relatorio de execucao do pipeline."""
        document = dict(report)
        document["saved_at"] = _utc_now()
        self.database.pipeline_runs.insert_one(document)

    def _upsert_rows(
        self,
        collection_name: str,
        rows: Iterable[dict[str, Any]],
        key_fields: tuple[str, ...],
    ) -> dict[str, object]:
        collection = self.database[collection_name]
        row_count = 0
        for row in rows:
            document = _clean_document(row)
            document["updated_at"] = _utc_now()
            filters = {field: document[field] for field in key_fields}
            collection.replace_one(filters, document, upsert=True)
            row_count += 1
        return {
            "collection": collection_name,
            "row_count": row_count,
            "key_fields": list(key_fields),
        }

    def _list_rows(
        self,
        collection_name: str,
        filters: dict[str, object],
        sort_fields: list[tuple[str, int]],
    ) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for document in self.database[collection_name].find(filters).sort(sort_fields):
            rows.append(_document_to_row(document))
        return rows


def _create_client(uri: str):
    if uri.startswith("mongomock://"):
        try:
            import mongomock
        except ImportError as error:
            raise RuntimeError(
                "Instale mongomock para usar MONGO_URI=mongomock://local."
            ) from error
        return mongomock.MongoClient()

    try:
        from pymongo import MongoClient
    except ImportError as error:
        raise RuntimeError(
            "Instale pymongo ou execute scripts/setup_venv.ps1 antes de usar MongoDB."
        ) from error
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


def _clean_document(row: dict[str, Any]) -> dict[str, Any]:
    document = {key: value for key, value in row.items() if key != "_id"}
    return {key: "" if value is None else value for key, value in document.items()}


def _document_to_row(document: dict[str, Any]) -> dict[str, str]:
    ignored = {"_id", "updated_at", "saved_at"}
    row: dict[str, str] = {}
    for key, value in document.items():
        if key in ignored:
            continue
        row[key] = str(value)
    return row


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
