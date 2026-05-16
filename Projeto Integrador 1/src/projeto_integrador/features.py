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
    "target_precipitation_tomorrow_mm",
    "target_rain_tomorrow",
]


def build_rain_features(
    input_path: str | Path,
    output_path: str | Path,
    rain_threshold_mm: float = 1.0,
) -> dict[str, object]:
    """Cria uma base supervisionada para prever chuva no dia seguinte."""
    raw_rows = sorted(read_csv(input_path), key=lambda row: row["date"])
    feature_rows = create_feature_rows(raw_rows, rain_threshold_mm)
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
) -> list[dict[str, str]]:
    """Converte linhas diarias em exemplos com alvo do dia seguinte."""
    feature_rows: list[dict[str, str]] = []
    for index in range(len(raw_rows) - 1):
        today = raw_rows[index]
        tomorrow = raw_rows[index + 1]

        precipitation_today = _to_float(today["precipitation_sum"])
        precipitation_tomorrow = _to_float(tomorrow["precipitation_sum"])
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

