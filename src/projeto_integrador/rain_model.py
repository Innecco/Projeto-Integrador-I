"""Modelo explicavel para previsao de chuva em Brasilia."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

from .pipeline import read_csv


FORECAST_PRECIPITATION_COLUMN = "forecast_precipitation_tomorrow_mm"


@dataclass
class RainProbabilityModel:
    """Modelo que calibra a previsao operacional para o contexto de Brasilia."""

    global_rate: float
    month_rates: dict[str, float]
    rain_today_rates: dict[str, float]
    threshold: float
    train_row_count: int
    forecast_threshold_mm: float = 1.0
    forecast_signal_rates: dict[str, float] | None = None
    model_name: str = "calibrated_forecast_threshold"

    def predict_proba(self, row: dict[str, str]) -> float:
        """Calcula probabilidade estimada de chuva amanha."""
        if _has_forecast_precipitation(row):
            signal = self._forecast_signal(row)
            rates = self.forecast_signal_rates or {}
            return rates.get(signal, self.global_rate)

        month_rate = self.month_rates.get(str(row["month"]), self.global_rate)
        persistence_rate = self.rain_today_rates.get(str(row["rain_today"]), self.global_rate)
        return (month_rate + persistence_rate) / 2

    def predict(self, row: dict[str, str]) -> int:
        """Classifica se chovera amanha."""
        if _has_forecast_precipitation(row):
            return int(_to_float(row[FORECAST_PRECIPITATION_COLUMN]) >= self.forecast_threshold_mm)
        return int(self.predict_proba(row) >= self.threshold)

    def to_dict(self) -> dict[str, object]:
        """Serializa o modelo."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "RainProbabilityModel":
        """Reconstrui o modelo a partir de JSON."""
        return cls(
            global_rate=float(data["global_rate"]),
            month_rates={str(key): float(value) for key, value in data["month_rates"].items()},
            rain_today_rates={
                str(key): float(value) for key, value in data["rain_today_rates"].items()
            },
            threshold=float(data["threshold"]),
            train_row_count=int(data["train_row_count"]),
            forecast_threshold_mm=float(data.get("forecast_threshold_mm", 1.0)),
            forecast_signal_rates={
                str(key): float(value)
                for key, value in (data.get("forecast_signal_rates") or {}).items()
            },
            model_name=str(data.get("model_name", "calibrated_forecast_threshold")),
        )

    def _forecast_signal(self, row: dict[str, str]) -> str:
        return "1" if _to_float(row[FORECAST_PRECIPITATION_COLUMN]) >= self.forecast_threshold_mm else "0"


def fit_rain_probability_model(rows: list[dict[str, str]]) -> RainProbabilityModel:
    """Treina o modelo explicavel."""
    if not rows:
        raise ValueError("Nao ha linhas para treinar o modelo.")

    global_rate = _positive_rate(rows)
    month_rates = _group_positive_rates(rows, "month")
    rain_today_rates = _group_positive_rates(rows, "rain_today")

    model = RainProbabilityModel(
        global_rate=global_rate,
        month_rates=month_rates,
        rain_today_rates=rain_today_rates,
        threshold=0.5,
        train_row_count=len(rows),
    )
    model.threshold = choose_probability_threshold(model, rows)

    if _rows_have_forecast(rows):
        model.forecast_threshold_mm = choose_forecast_threshold(rows, optimization_metric="accuracy")
        model.forecast_signal_rates = _forecast_signal_positive_rates(
            rows,
            model.forecast_threshold_mm,
        )

    return model


def choose_probability_threshold(model: RainProbabilityModel, rows: list[dict[str, str]]) -> float:
    """Escolhe limiar probabilistico para o fallback sazonal."""
    probabilities = sorted({round(_fallback_probability(model, row), 6) for row in rows})
    candidates = sorted({0.5, *probabilities})

    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in candidates:
        f1_score = evaluate_probability_threshold(model, rows, threshold)["f1"]
        if f1_score > best_f1:
            best_threshold = threshold
            best_f1 = f1_score
    return best_threshold


def choose_forecast_threshold(
    rows: list[dict[str, str]],
    optimization_metric: str = "accuracy",
) -> float:
    """Escolhe o limiar de precipitacao prevista que maximiza a metrica no treino."""
    candidates = sorted(
        {
            1.0,
            *{
                round(_to_float(row[FORECAST_PRECIPITATION_COLUMN]), 3)
                for row in rows
                if _has_forecast_precipitation(row)
            },
        }
    )

    best_threshold = 1.0
    best_score = -1.0
    best_f1 = -1.0
    for threshold in candidates:
        metrics = evaluate_forecast_threshold(rows, threshold)
        score = float(metrics[optimization_metric])
        f1_score = float(metrics["f1"])
        if score > best_score or (score == best_score and f1_score > best_f1):
            best_threshold = threshold
            best_score = score
            best_f1 = f1_score
    return best_threshold


def evaluate_probability_threshold(
    model: RainProbabilityModel,
    rows: list[dict[str, str]],
    threshold: float,
) -> dict[str, object]:
    """Avalia o fallback probabilistico sem usar previsao operacional."""
    return _evaluate_predictions(
        rows,
        lambda row: int(_fallback_probability(model, row) >= threshold),
    )


def evaluate_forecast_threshold(
    rows: list[dict[str, str]],
    threshold_mm: float,
) -> dict[str, object]:
    """Avalia a previsao operacional usando um limiar fixo de precipitacao."""
    forecast_rows = [row for row in rows if _has_forecast_precipitation(row)]
    return _evaluate_predictions(
        forecast_rows,
        lambda row: int(_to_float(row[FORECAST_PRECIPITATION_COLUMN]) >= threshold_mm),
    )


def evaluate_model(model: RainProbabilityModel, rows: list[dict[str, str]]) -> dict[str, object]:
    """Calcula metricas de classificacao."""
    return _evaluate_predictions(rows, model.predict)


def train_and_backtest(
    input_path: str | Path,
    split_date: str,
    report_path: str | Path,
    model_path: str | Path,
) -> dict[str, object]:
    """Treina o modelo e avalia em holdout temporal."""
    rows = sorted(read_csv(input_path), key=lambda row: row["date"])
    train_rows, test_rows = temporal_split(rows, split_date)

    model = fit_rain_probability_model(train_rows)
    operational_forecast_threshold_mm = 1.0
    report = {
        "model_name": model.model_name,
        "target": "target_rain_tomorrow",
        "split_date": split_date,
        "train_metrics": evaluate_model(model, train_rows),
        "test_metrics": evaluate_model(model, test_rows),
        "operational_forecast_baseline": {
            "name": "open_meteo_previous_day1_threshold_1mm",
            "source": "Open-Meteo Previous Runs API",
            "threshold_mm": operational_forecast_threshold_mm,
            "train_metrics": evaluate_forecast_threshold(
                train_rows,
                operational_forecast_threshold_mm,
            ),
            "test_metrics": evaluate_forecast_threshold(
                test_rows,
                operational_forecast_threshold_mm,
            ),
        },
        "model": model.to_dict(),
        "interpretation": {
            "global_rain_probability": round(model.global_rate, 4),
            "monthly_rain_probabilities": {
                month: round(rate, 4) for month, rate in sorted(model.month_rates.items())
            },
            "rain_persistence_probabilities": {
                key: round(rate, 4) for key, rate in sorted(model.rain_today_rates.items())
            },
            "operational_forecast_threshold_mm": operational_forecast_threshold_mm,
            "calibrated_forecast_threshold_mm": round(model.forecast_threshold_mm, 4),
            "decision_rule": (
                "prever chuva quando a precipitacao prevista para amanha for maior "
                "ou igual ao limiar calibrado para Brasilia"
            ),
        },
    }

    write_model(model, model_path)
    write_report(report, report_path)
    return report


def temporal_split(
    rows: list[dict[str, str]],
    split_date: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Separa treino e teste preservando a ordem temporal."""
    train_rows = [row for row in rows if row["date"] < split_date]
    test_rows = [row for row in rows if row["date"] >= split_date]

    if not train_rows:
        raise ValueError("A base de treino ficou vazia. Revise split_date.")
    if not test_rows:
        raise ValueError("A base de teste ficou vazia. Revise split_date.")

    return train_rows, test_rows


def write_model(model: RainProbabilityModel, output_path: str | Path) -> None:
    """Grava o modelo em JSON."""
    write_report(model.to_dict(), output_path)


def write_report(report: dict[str, object], output_path: str | Path) -> None:
    """Grava um relatorio JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write("\n")


def load_model(path: str | Path) -> RainProbabilityModel:
    """Carrega um modelo salvo em JSON."""
    with Path(path).open("r", encoding="utf-8") as file:
        return RainProbabilityModel.from_dict(json.load(file))


def build_prediction_rows(
    model: RainProbabilityModel,
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Gera predicoes em memoria para persistencia e exportacao."""
    prediction_rows: list[dict[str, str]] = []
    for row in rows:
        probability = model.predict_proba(row)
        output_row = dict(row)
        output_row["predicted_probability"] = f"{probability:.4f}"
        output_row["predicted_rain_tomorrow"] = str(model.predict(row))
        prediction_rows.append(output_row)
    return prediction_rows


def write_predictions(
    model: RainProbabilityModel,
    input_path: str | Path,
    output_path: str | Path,
) -> dict[str, object]:
    """Gera predicoes para uma base de features."""
    rows = read_csv(input_path)
    prediction_rows = build_prediction_rows(model, rows)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(prediction_rows[0].keys()) if prediction_rows else []
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(prediction_rows)

    return {
        "row_count": len(prediction_rows),
        "output_path": str(output_path),
        "rows": prediction_rows,
    }


def _group_positive_rates(rows: Iterable[dict[str, str]], column: str) -> dict[str, float]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[str(row[column])].append(row)
    return {group: _positive_rate(group_rows) for group, group_rows in groups.items()}


def _forecast_signal_positive_rates(
    rows: Iterable[dict[str, str]],
    threshold_mm: float,
) -> dict[str, float]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if not _has_forecast_precipitation(row):
            continue
        signal = "1" if _to_float(row[FORECAST_PRECIPITATION_COLUMN]) >= threshold_mm else "0"
        groups[signal].append(row)
    return {signal: _positive_rate(group_rows) for signal, group_rows in groups.items()}


def _positive_rate(rows: Iterable[dict[str, str]]) -> float:
    materialized_rows = list(rows)
    if not materialized_rows:
        return 0.0
    positives = sum(int(row["target_rain_tomorrow"]) for row in materialized_rows)
    return positives / len(materialized_rows)


def _evaluate_predictions(
    rows: list[dict[str, str]],
    predict: Callable[[dict[str, str]], int],
) -> dict[str, object]:
    confusion = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}

    for row in rows:
        actual = int(row["target_rain_tomorrow"])
        predicted = int(predict(row))
        if actual == 1 and predicted == 1:
            confusion["true_positive"] += 1
        elif actual == 0 and predicted == 0:
            confusion["true_negative"] += 1
        elif actual == 0 and predicted == 1:
            confusion["false_positive"] += 1
        else:
            confusion["false_negative"] += 1

    total = len(rows)
    tp = confusion["true_positive"]
    tn = confusion["true_negative"]
    fp = confusion["false_positive"]
    fn = confusion["false_negative"]

    precision = _safe_divide(tp, tp + fp)
    recall = _safe_divide(tp, tp + fn)
    f1_score = _safe_divide(2 * precision * recall, precision + recall)

    return {
        "row_count": total,
        "period": _period(rows),
        "accuracy": round(_safe_divide(tp + tn, total), 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1_score, 4),
        "rain_rate": round(_positive_rate(rows), 4) if rows else 0.0,
        "predicted_rain_rate": round(_safe_divide(tp + fp, total), 4) if rows else 0.0,
        "confusion_matrix": confusion,
    }


def _fallback_probability(model: RainProbabilityModel, row: dict[str, str]) -> float:
    month_rate = model.month_rates.get(str(row["month"]), model.global_rate)
    persistence_rate = model.rain_today_rates.get(str(row["rain_today"]), model.global_rate)
    return (month_rate + persistence_rate) / 2


def _rows_have_forecast(rows: list[dict[str, str]]) -> bool:
    return any(_has_forecast_precipitation(row) for row in rows)


def _has_forecast_precipitation(row: dict[str, str]) -> bool:
    value = row.get(FORECAST_PRECIPITATION_COLUMN, "").strip()
    if value == "":
        return False
    try:
        _to_float(value)
    except ValueError:
        return False
    return True


def _to_float(value: str) -> float:
    return float(value.replace(",", "."))


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _period(rows: list[dict[str, str]]) -> dict[str, str | None]:
    if not rows:
        return {"start": None, "end": None}
    return {"start": rows[0]["date"], "end": rows[-1]["date"]}
