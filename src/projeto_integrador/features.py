"""Criacao de features para previsao de chuva no dia seguinte."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .pipeline import read_csv


FEATURE_COLUMNS = [
    "date",
    "target_date",
    "month",
    "temperature_2m_mean",
    "temperature_range",
    "precipitation_sum",
    "rain_sum",
    "precipitation_hours",
    "wind_speed_10m_max",
    "wind_speed_10m_mean",
    "relative_humidity_2m_mean",
    "rain_today",
    "forecast_available",
    "forecast_precipitation_tomorrow_mm",
    "forecast_rain_tomorrow",
    "target_precipitation_tomorrow_mm",
    "target_rain_tomorrow",
]


def build_rain_features(
    input_path: str | Path,
    output_path: str | Path,
    rain_threshold_mm: float = 1.0,
    forecast_rows: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    """Cria uma base supervisionada para prever chuva no dia seguinte."""
    raw_rows = sorted(read_csv(input_path), key=lambda row: row["date"])
    feature_rows = create_feature_rows(raw_rows, rain_threshold_mm, forecast_rows)
    write_feature_csv(feature_rows, output_path)

    rain_count = sum(int(row["target_rain_tomorrow"]) for row in feature_rows)
    return {
        "input_rows": len(raw_rows),
        "feature_rows": len(feature_rows),
        "rain_threshold_mm": rain_threshold_mm,
        "target_rain_rate": round(rain_count / len(feature_rows), 4) if feature_rows else 0.0,
        "output_path": str(output_path),
    }


def create_feature_rows(
    raw_rows: list[dict[str, str]],
    rain_threshold_mm: float,
    forecast_rows: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Converte linhas diarias em exemplos com alvo do dia seguinte."""
    forecast_by_date = _forecast_by_date(forecast_rows or [])
    feature_rows: list[dict[str, str]] = []
    for index in range(len(raw_rows) - 1):
        today = raw_rows[index]
        tomorrow = raw_rows[index + 1]

        precipitation_today = _to_float(today["precipitation_sum"])
        precipitation_tomorrow = _to_float(tomorrow["precipitation_sum"])
        forecast_available = tomorrow["date"] in forecast_by_date
        forecast_precipitation_tomorrow = forecast_by_date.get(tomorrow["date"])
        temperature_range = _to_float(today["temperature_2m_max"]) - _to_float(
            today["temperature_2m_min"]
        )
        current_date = date.fromisoformat(today["date"])

        feature_rows.append(
            {
                "date": today["date"],
                "target_date": tomorrow["date"],
                "month": str(current_date.month),
                "temperature_2m_mean": _format_float(today["temperature_2m_mean"]),
                "temperature_range": _format_float(temperature_range),
                "precipitation_sum": _format_float(precipitation_today),
                "rain_sum": _format_float(today["rain_sum"]),
                "precipitation_hours": _format_float(today["precipitation_hours"]),
                "wind_speed_10m_max": _format_float(today["wind_speed_10m_max"]),
                "wind_speed_10m_mean": _format_float(today["wind_speed_10m_mean"]),
                "relative_humidity_2m_mean": _format_float(
                    today["relative_humidity_2m_mean"]
                ),
                "rain_today": _format_binary(precipitation_today >= rain_threshold_mm),
                "forecast_available": _format_binary(forecast_available),
                "forecast_precipitation_tomorrow_mm": (
                    _format_float(forecast_precipitation_tomorrow)
                    if forecast_precipitation_tomorrow is not None
                    else ""
                ),
                "forecast_rain_tomorrow": (
                    _format_binary(forecast_precipitation_tomorrow >= rain_threshold_mm)
                    if forecast_precipitation_tomorrow is not None
                    else ""
                ),
                "target_precipitation_tomorrow_mm": _format_float(precipitation_tomorrow),
                "target_rain_tomorrow": _format_binary(
                    precipitation_tomorrow >= rain_threshold_mm
                ),
            }
        )

    return feature_rows


def write_feature_csv(rows: list[dict[str, str]], output_path: str | Path) -> None:
    """Grava a base de features em CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FEATURE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _to_float(value: str) -> float:
    return float(value.replace(",", "."))


def _format_float(value: str | float) -> str:
    numeric_value = _to_float(value) if isinstance(value, str) else value
    return f"{numeric_value:.3f}"


def _format_binary(value: bool) -> str:
    return "1" if value else "0"


def _forecast_by_date(forecast_rows: list[dict[str, str]]) -> dict[str, float]:
    forecasts: dict[str, float] = {}
    for row in forecast_rows:
        date_value = row.get("date", "")
        precipitation = row.get("forecast_precipitation_sum", "0")
        if date_value:
            forecasts[date_value] = _to_float(precipitation)
    return forecasts
