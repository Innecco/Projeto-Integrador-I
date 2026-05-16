"""Coleta de dados meteorologicos da Open-Meteo."""

from __future__ import annotations

import csv
import json
import os
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .config import load_json
from .env import load_project_env


DEFAULT_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
DEFAULT_DAILY_VARIABLES = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "rain_sum",
    "precipitation_hours",
    "wind_speed_10m_max",
    "wind_speed_10m_mean",
    "relative_humidity_2m_mean",
]


def build_archive_url(config: dict[str, Any]) -> str:
    """Monta a URL da API historica da Open-Meteo."""
    load_project_env()
    location = config["location"]
    variables = config.get("daily_variables", DEFAULT_DAILY_VARIABLES)

    params = {
        "latitude": str(location["latitude"]),
        "longitude": str(location["longitude"]),
        "start_date": resolve_date_value(str(config.get("start_date", os.getenv("WEATHER_START_DATE")))),
        "end_date": resolve_date_value(str(config.get("end_date", os.getenv("WEATHER_END_DATE")))),
        "daily": ",".join(variables),
        "timezone": config.get("timezone", os.getenv("WEATHER_TIMEZONE", "auto")),
    }
    api_key = config.get("api_key") or os.getenv("OPEN_METEO_API_KEY")
    if api_key:
        params["apikey"] = str(api_key)

    base_url = str(config.get("source_url", os.getenv("OPEN_METEO_ARCHIVE_URL", DEFAULT_ARCHIVE_URL)))
    return base_url + "?" + urllib.parse.urlencode(params)


def fetch_archive_payload(config: dict[str, Any], timeout_seconds: int = 60) -> dict[str, Any]:
    """Busca o JSON historico diario na Open-Meteo."""
    url = build_archive_url(config)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Projeto-Integrador-1/1.0"},
    )

    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload.get("error"):
        reason = payload.get("reason", "motivo nao informado")
        raise RuntimeError(f"Erro retornado pela Open-Meteo: {reason}")

    if "daily" not in payload:
        raise RuntimeError("Resposta da Open-Meteo nao contem a chave 'daily'.")

    return payload


def daily_payload_to_rows(
    payload: dict[str, Any],
    location: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Converte o bloco daily da API para linhas tabulares."""
    daily = payload["daily"]
    dates = daily["time"]
    variables = [key for key in daily.keys() if key != "time"]
    location = location or {}

    rows: list[dict[str, str]] = []
    for index, date_value in enumerate(dates):
        row = {
            "city_id": str(location.get("id", "")),
            "city_name": str(location.get("name", "")),
            "state": str(location.get("state", "")),
            "date": str(date_value),
        }
        for variable in variables:
            value = daily[variable][index]
            row[variable] = "" if value is None else str(value)
        rows.append(row)

    return rows


def write_weather_csv(rows: list[dict[str, str]], output_path: str | Path) -> None:
    """Grava as linhas meteorologicas em CSV."""
    if not rows:
        raise ValueError("Nao ha linhas para gravar.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fetch_weather_to_csv(config_path: str | Path, output_path: str | Path) -> dict[str, object]:
    """Executa a coleta e salva os dados brutos em CSV."""
    config = load_json(config_path)
    payload = fetch_archive_payload(config)
    rows = daily_payload_to_rows(payload, config.get("location"))
    write_weather_csv(rows, output_path)

    return {
        "source": config.get("source_name", "Open-Meteo"),
        "location": config.get("location", {}).get("name", "local nao informado"),
        "start_date": config["start_date"],
        "end_date": config["end_date"],
        "row_count": len(rows),
        "output_path": str(output_path),
        "request_url": build_archive_url(config),
    }


def fetch_multi_city_weather_to_csv(
    config_path: str | Path,
    output_dir: str | Path,
    combined_output_path: str | Path,
) -> dict[str, object]:
    """Coleta dados para todas as cidades configuradas."""
    load_project_env()
    config = load_json(config_path)
    output_directory = Path(output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)

    start_date = resolve_date_value(os.getenv("WEATHER_START_DATE", "2021-01-01"))
    end_date = resolve_date_value(os.getenv("WEATHER_END_DATE", "2025-12-31"))
    timezone = os.getenv("WEATHER_TIMEZONE", "America/Sao_Paulo")

    combined_rows: list[dict[str, str]] = []
    city_reports: list[dict[str, object]] = []

    for location in config["locations"]:
        city_config = {
            "source_name": config.get("source_name", "Open-Meteo"),
            "source_url": os.getenv("OPEN_METEO_ARCHIVE_URL", DEFAULT_ARCHIVE_URL),
            "location": location,
            "daily_variables": config.get("daily_variables", DEFAULT_DAILY_VARIABLES),
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone,
        }
        payload = fetch_archive_payload(city_config)
        rows = daily_payload_to_rows(payload, location)
        city_path = output_directory / f"weather_{location['id']}_daily.csv"
        write_weather_csv(rows, city_path)
        combined_rows.extend(rows)
        city_reports.append(
            {
                "city_id": location["id"],
                "city_name": location["name"],
                "row_count": len(rows),
                "output_path": str(city_path),
                "request_url": build_archive_url(city_config),
            }
        )

    write_weather_csv(combined_rows, combined_output_path)

    return {
        "source": config.get("source_name", "Open-Meteo"),
        "start_date": start_date,
        "end_date": end_date,
        "city_count": len(city_reports),
        "row_count": len(combined_rows),
        "combined_output_path": str(combined_output_path),
        "cities": city_reports,
    }


def resolve_date_value(value: str) -> str:
    """Resolve valores relativos usados no .env."""
    normalized = value.strip().lower()
    if normalized == "today":
        return date.today().isoformat()
    if normalized == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    return value
