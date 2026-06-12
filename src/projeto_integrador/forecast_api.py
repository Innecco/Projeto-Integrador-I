"""Coleta da previsao operacional da Open-Meteo para benchmark e calibracao."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .env import load_project_env
from .weather_api import resolve_date_value


DEFAULT_PREVIOUS_RUNS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
PREVIOUS_DAY1_PRECIPITATION = "precipitation_previous_day1"


def build_previous_day1_forecast_url(
    location: dict[str, Any],
    start_date: str,
    end_date: str,
    timezone: str,
) -> str:
    """Monta URL para previsao de precipitacao feita no dia anterior."""
    load_project_env()
    params = {
        "latitude": str(location["latitude"]),
        "longitude": str(location["longitude"]),
        "start_date": resolve_date_value(start_date),
        "end_date": resolve_date_value(end_date),
        "hourly": PREVIOUS_DAY1_PRECIPITATION,
        "timezone": timezone,
    }
    base_url = os.getenv("OPEN_METEO_PREVIOUS_RUNS_URL", DEFAULT_PREVIOUS_RUNS_URL)
    return base_url + "?" + urllib.parse.urlencode(params)


def fetch_previous_day1_forecast_payload(
    location: dict[str, Any],
    start_date: str,
    end_date: str,
    timezone: str,
    timeout_seconds: int | None = None,
    max_retries: int | None = None,
    retry_sleep_seconds: float = 2.0,
) -> dict[str, Any]:
    """Busca previsao historica de precipitacao horaria feita no dia anterior."""
    timeout_seconds = timeout_seconds or int(os.getenv("OPEN_METEO_TIMEOUT_SECONDS", "45"))
    max_retries = max_retries if max_retries is not None else int(
        os.getenv("OPEN_METEO_MAX_RETRIES", "1")
    )
    url = build_previous_day1_forecast_url(location, start_date, end_date, timezone)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Projeto-Integrador-1/1.0"},
    )

    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt >= max_retries:
                raise
            time.sleep(retry_sleep_seconds * (attempt + 1))
        except (TimeoutError, urllib.error.URLError):
            if attempt >= max_retries:
                raise
            time.sleep(retry_sleep_seconds * (attempt + 1))
    else:
        raise RuntimeError("Falha inesperada ao consultar a previsao Open-Meteo.")

    if payload.get("error"):
        reason = payload.get("reason", "motivo nao informado")
        raise RuntimeError(f"Erro retornado pela Open-Meteo Previous Runs API: {reason}")
    if "hourly" not in payload:
        raise RuntimeError("Resposta da Open-Meteo nao contem a chave 'hourly'.")
    return payload


def previous_day1_payload_to_daily_rows(
    payload: dict[str, Any],
    location: dict[str, Any],
    rain_threshold_mm: float,
) -> list[dict[str, str]]:
    """Agrega a previsao horaria do dia anterior para total diario."""
    hourly = payload["hourly"]
    times = hourly["time"]
    precipitations = hourly[PREVIOUS_DAY1_PRECIPITATION]
    daily_precipitation: dict[str, float] = defaultdict(float)

    for timestamp, value in zip(times, precipitations):
        if value is None:
            continue
        daily_precipitation[str(timestamp)[:10]] += float(value)

    rows: list[dict[str, str]] = []
    for forecast_date, precipitation in sorted(daily_precipitation.items()):
        rows.append(
            {
                "city_id": str(location["id"]),
                "city_name": str(location["name"]),
                "state": str(location["state"]),
                "date": forecast_date,
                "forecast_horizon": "previous_day1",
                "forecast_precipitation_sum": f"{precipitation:.3f}",
                "forecast_rain": "1" if precipitation >= rain_threshold_mm else "0",
            }
        )
    return rows


def fetch_previous_day1_forecast_rows(
    location: dict[str, Any],
    start_date: str,
    end_date: str,
    timezone: str,
    rain_threshold_mm: float,
) -> tuple[list[dict[str, str]], str]:
    """Busca e converte a previsao operacional em blocos anuais."""
    rows: list[dict[str, str]] = []
    request_urls: list[str] = []
    for chunk_start, chunk_end in split_date_range_by_year(start_date, end_date):
        payload = fetch_previous_day1_forecast_payload(
            location,
            chunk_start,
            chunk_end,
            timezone,
        )
        rows.extend(previous_day1_payload_to_daily_rows(payload, location, rain_threshold_mm))
        request_urls.append(
            build_previous_day1_forecast_url(location, chunk_start, chunk_end, timezone)
        )
    return rows, " | ".join(request_urls)


def write_forecast_csv(rows: list[dict[str, str]], output_path: str | Path) -> None:
    """Exporta previsoes para CSV apenas como anexo/referencia."""
    import csv

    if not rows:
        raise ValueError("Nao ha linhas de previsao para gravar.")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def split_date_range_by_year(start_date: str, end_date: str) -> list[tuple[str, str]]:
    """Divide um intervalo ISO em blocos anuais fechados."""
    current = date.fromisoformat(resolve_date_value(start_date))
    final = date.fromisoformat(resolve_date_value(end_date))
    chunks: list[tuple[str, str]] = []
    while current <= final:
        year_end = date(current.year, 12, 31)
        chunk_end = min(year_end, final)
        chunks.append((current.isoformat(), chunk_end.isoformat()))
        current = chunk_end + timedelta(days=1)
    return chunks
