"""Analise exploratoria e comparacao climatica entre cidades."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean

from PIL import Image, ImageDraw, ImageFont

from .pipeline import read_csv


COLORS = {
    "brasilia": "#1F77B4",
    "goiania": "#2CA02C",
    "sao_paulo": "#D62728",
}


def generate_weather_eda(
    input_path: str | Path,
    output_dir: str | Path,
    rain_threshold_mm: float = 1.0,
) -> dict[str, object]:
    """Gera resumos e graficos de EDA para as cidades coletadas."""
    rows = read_csv(input_path)
    figures_dir = Path(output_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)

    monthly = build_monthly_summary(rows, rain_threshold_mm)
    annual = build_annual_summary(rows)
    city_summary = build_city_summary(rows, rain_threshold_mm)

    summary = {
        "rain_threshold_mm": rain_threshold_mm,
        "city_summary": city_summary,
        "monthly_summary": monthly,
        "annual_summary": annual,
    }

    json_path = figures_dir.parent / "reports" / "weather_city_comparison_summary.json"
    csv_path = figures_dir.parent / "reports" / "weather_city_comparison_summary.csv"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(summary, json_path)
    write_city_summary_csv(city_summary, csv_path)

    figures = [
        draw_line_chart(
            monthly,
            metric_key="rain_rate",
            title="Taxa mensal de dias com chuva por cidade",
            y_label="Taxa de chuva",
            output_path=figures_dir / "eda_taxa_chuva_mensal_por_cidade.png",
            y_format="percent",
        ),
        draw_line_chart(
            monthly,
            metric_key="avg_precipitation_mm",
            title="Precipitacao media diaria por mes",
            y_label="mm por dia",
            output_path=figures_dir / "eda_precipitacao_media_mensal_por_cidade.png",
            y_format="decimal",
        ),
        draw_line_chart(
            monthly,
            metric_key="avg_temperature_c",
            title="Temperatura media diaria por mes",
            y_label="graus C",
            output_path=figures_dir / "eda_temperatura_media_mensal_por_cidade.png",
            y_format="decimal",
        ),
        draw_grouped_bar_chart(
            annual,
            title="Precipitacao anual acumulada por cidade",
            y_label="mm por ano",
            output_path=figures_dir / "eda_precipitacao_anual_por_cidade.png",
        ),
    ]

    return {
        "input_path": str(input_path),
        "row_count": len(rows),
        "city_count": len(city_summary),
        "summary_json": str(json_path),
        "summary_csv": str(csv_path),
        "figures": [str(path) for path in figures],
    }


def build_monthly_summary(
    rows: list[dict[str, str]],
    rain_threshold_mm: float,
) -> list[dict[str, object]]:
    """Resume metricas por cidade e mes."""
    groups: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        month = date.fromisoformat(row["date"]).month
        groups[(row["city_id"], month)].append(row)

    summary: list[dict[str, object]] = []
    for (city_id, month), group_rows in sorted(groups.items()):
        precipitations = [_to_float(row["precipitation_sum"]) for row in group_rows]
        temperatures = [_to_float(row["temperature_2m_mean"]) for row in group_rows]
        rainy_days = sum(value >= rain_threshold_mm for value in precipitations)
        summary.append(
            {
                "city_id": city_id,
                "city_name": group_rows[0]["city_name"],
                "month": month,
                "day_count": len(group_rows),
                "rainy_days": rainy_days,
                "rain_rate": rainy_days / len(group_rows),
                "avg_precipitation_mm": mean(precipitations),
                "total_precipitation_mm": sum(precipitations),
                "avg_temperature_c": mean(temperatures),
            }
        )
    return summary


def build_annual_summary(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """Resume precipitacao acumulada por cidade e ano."""
    groups: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        year = date.fromisoformat(row["date"]).year
        groups[(row["city_id"], year)].append(row)

    summary: list[dict[str, object]] = []
    for (city_id, year), group_rows in sorted(groups.items()):
        precipitations = [_to_float(row["precipitation_sum"]) for row in group_rows]
        summary.append(
            {
                "city_id": city_id,
                "city_name": group_rows[0]["city_name"],
                "year": year,
                "day_count": len(group_rows),
                "total_precipitation_mm": sum(precipitations),
            }
        )
    return summary


def build_city_summary(
    rows: list[dict[str, str]],
    rain_threshold_mm: float,
) -> list[dict[str, object]]:
    """Resume estatisticas gerais por cidade."""
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["city_id"]].append(row)

    summary: list[dict[str, object]] = []
    for city_id, group_rows in sorted(groups.items()):
        precipitations = [_to_float(row["precipitation_sum"]) for row in group_rows]
        temperatures = [_to_float(row["temperature_2m_mean"]) for row in group_rows]
        rainy_days = sum(value >= rain_threshold_mm for value in precipitations)
        summary.append(
            {
                "city_id": city_id,
                "city_name": group_rows[0]["city_name"],
                "state": group_rows[0]["state"],
                "day_count": len(group_rows),
                "rainy_days": rainy_days,
                "rain_rate": rainy_days / len(group_rows),
                "total_precipitation_mm": sum(precipitations),
                "avg_daily_precipitation_mm": mean(precipitations),
                "avg_temperature_c": mean(temperatures),
            }
        )
    return summary


def draw_line_chart(
    monthly: list[dict[str, object]],
    metric_key: str,
    title: str,
    y_label: str,
    output_path: Path,
    y_format: str,
) -> Path:
    """Desenha grafico de linhas mensal por cidade."""
    width, height = 1200, 720
    margin_left, margin_right, margin_top, margin_bottom = 110, 60, 90, 95
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font_title, font_body, font_small = load_fonts()

    draw.text((margin_left, 28), title, fill="#111111", font=font_title)
    draw.text((margin_left, 58), y_label, fill="#555555", font=font_small)

    city_ids = sorted({str(row["city_id"]) for row in monthly})
    values = [float(row[metric_key]) for row in monthly]
    y_max = max(values) if values else 1.0
    if y_format == "percent":
        y_max = max(1.0, y_max)
    else:
        y_max *= 1.12

    plot_left = margin_left
    plot_right = width - margin_right
    plot_top = margin_top
    plot_bottom = height - margin_bottom

    draw_axes(draw, plot_left, plot_top, plot_right, plot_bottom)
    draw_y_ticks(draw, plot_left, plot_top, plot_bottom, y_max, y_format, font_small)
    draw_x_month_ticks(draw, plot_left, plot_right, plot_bottom, font_small)

    for city_id in city_ids:
        city_rows = sorted(
            [row for row in monthly if row["city_id"] == city_id],
            key=lambda row: int(row["month"]),
        )
        points = []
        for row in city_rows:
            x = plot_left + (int(row["month"]) - 1) * (plot_right - plot_left) / 11
            y = plot_bottom - (float(row[metric_key]) / y_max) * (plot_bottom - plot_top)
            points.append((x, y))
        color = COLORS.get(city_id, "#555555")
        if len(points) > 1:
            draw.line(points, fill=color, width=4)
        for x, y in points:
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)

    draw_legend(draw, city_ids, monthly, width - 340, 36, font_small)
    image.save(output_path)
    return output_path


def draw_grouped_bar_chart(
    annual: list[dict[str, object]],
    title: str,
    y_label: str,
    output_path: Path,
) -> Path:
    """Desenha grafico de barras agrupadas por ano e cidade."""
    width, height = 1200, 720
    margin_left, margin_right, margin_top, margin_bottom = 110, 60, 90, 95
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font_title, font_body, font_small = load_fonts()

    draw.text((margin_left, 28), title, fill="#111111", font=font_title)
    draw.text((margin_left, 58), y_label, fill="#555555", font=font_small)

    city_ids = sorted({str(row["city_id"]) for row in annual})
    years = sorted({int(row["year"]) for row in annual})
    partial_years = {
        int(row["year"])
        for row in annual
        if int(row["day_count"]) < expected_days_in_year(int(row["year"]))
    }
    max_value = max(float(row["total_precipitation_mm"]) for row in annual) * 1.12

    plot_left = margin_left
    plot_right = width - margin_right
    plot_top = margin_top
    plot_bottom = height - margin_bottom

    draw_axes(draw, plot_left, plot_top, plot_right, plot_bottom)
    draw_y_ticks(draw, plot_left, plot_top, plot_bottom, max_value, "decimal", font_small)

    year_slot = (plot_right - plot_left) / len(years)
    bar_width = year_slot / (len(city_ids) + 1)
    lookup = {(row["city_id"], int(row["year"])): row for row in annual}

    for year_index, year in enumerate(years):
        x_start = plot_left + year_index * year_slot
        label = f"{year}*" if year in partial_years else str(year)
        draw.text((x_start + year_slot * 0.32, plot_bottom + 22), label, fill="#333333", font=font_small)
        for city_index, city_id in enumerate(city_ids):
            row = lookup[(city_id, year)]
            value = float(row["total_precipitation_mm"])
            x0 = x_start + 12 + city_index * bar_width
            x1 = x0 + bar_width * 0.76
            y0 = plot_bottom - (value / max_value) * (plot_bottom - plot_top)
            draw.rectangle((x0, y0, x1, plot_bottom), fill=COLORS.get(city_id, "#555555"))

    draw_legend(draw, city_ids, annual, width - 340, 36, font_small)
    if partial_years:
        draw.text((margin_left, height - 42), "* ano parcial conforme ultimo dia coletado", fill="#555555", font=font_small)
    image.save(output_path)
    return output_path


def draw_axes(draw: ImageDraw.ImageDraw, left: int, top: int, right: int, bottom: int) -> None:
    """Desenha eixos e grade leve."""
    draw.line((left, bottom, right, bottom), fill="#333333", width=2)
    draw.line((left, top, left, bottom), fill="#333333", width=2)
    for index in range(1, 5):
        y = bottom - index * (bottom - top) / 5
        draw.line((left, y, right, y), fill="#E5E7EB", width=1)


def draw_y_ticks(
    draw: ImageDraw.ImageDraw,
    left: int,
    top: int,
    bottom: int,
    y_max: float,
    y_format: str,
    font: ImageFont.ImageFont,
) -> None:
    """Desenha rotulos do eixo Y."""
    for index in range(0, 6):
        value = y_max * index / 5
        y = bottom - index * (bottom - top) / 5
        if y_format == "percent":
            label = f"{value * 100:.0f}%"
        else:
            label = f"{value:.0f}"
        draw.text((left - 72, y - 8), label, fill="#444444", font=font)


def draw_x_month_ticks(
    draw: ImageDraw.ImageDraw,
    left: int,
    right: int,
    bottom: int,
    font: ImageFont.ImageFont,
) -> None:
    """Desenha meses no eixo X."""
    labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    for index, label in enumerate(labels):
        x = left + index * (right - left) / 11
        draw.text((x - 16, bottom + 22), label, fill="#333333", font=font)


def draw_legend(
    draw: ImageDraw.ImageDraw,
    city_ids: list[str],
    rows: list[dict[str, object]],
    x: int,
    y: int,
    font: ImageFont.ImageFont,
) -> None:
    """Desenha legenda."""
    names = {str(row["city_id"]): str(row["city_name"]) for row in rows}
    for index, city_id in enumerate(city_ids):
        y_position = y + index * 24
        color = COLORS.get(city_id, "#555555")
        draw.rectangle((x, y_position + 4, x + 16, y_position + 20), fill=color)
        draw.text((x + 24, y_position + 1), names.get(city_id, city_id), fill="#222222", font=font)


def load_fonts() -> tuple[ImageFont.ImageFont, ImageFont.ImageFont, ImageFont.ImageFont]:
    """Carrega fontes seguras para os graficos."""
    try:
        return (
            ImageFont.truetype("arial.ttf", 30),
            ImageFont.truetype("arial.ttf", 22),
            ImageFont.truetype("arial.ttf", 18),
        )
    except OSError:
        default = ImageFont.load_default()
        return default, default, default


def write_json(data: dict[str, object], output_path: Path) -> None:
    """Grava JSON indentado."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_city_summary_csv(summary: list[dict[str, object]], output_path: Path) -> None:
    """Grava resumo geral por cidade."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "city_id",
        "city_name",
        "state",
        "day_count",
        "rainy_days",
        "rain_rate",
        "total_precipitation_mm",
        "avg_daily_precipitation_mm",
        "avg_temperature_c",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary:
            writer.writerow(row)


def _to_float(value: str) -> float:
    return float(value.replace(",", "."))


def expected_days_in_year(year: int) -> int:
    """Retorna 365 ou 366 dias."""
    return 366 if (year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)) else 365
