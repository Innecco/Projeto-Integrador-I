"""Modelo explicavel para previsao simples de chuva."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .pipeline import read_csv


@dataclass
class RainProbabilityModel:
    """Modelo por sazonalidade mensal e persistencia de chuva."""

    global_rate: float
    month_rates: dict[str, float]
    rain_today_rates: dict[str, float]
    threshold: float
    train_row_count: int

    def predict_proba(self, row: dict[str, str]) -> float:
        """Calcula a probabilidade estimada de chuva amanha."""
        month_rate = self.month_rates.get(str(row["month"]), self.global_rate)
        persistence_rate = self.rain_today_rates.get(str(row["rain_today"]), self.global_rate)
        return (month_rate + persistence_rate) / 2

    def predict(self, row: dict[str, str]) -> int:
        """Classifica se chovera amanha."""
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
        )


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
    model.threshold = choose_threshold(model, rows)
    return model


def choose_threshold(model: RainProbabilityModel, rows: list[dict[str, str]]) -> float:
    """Escolhe o limiar que maximiza F1 no treino."""
    probabilities = sorted({round(model.predict_proba(row), 6) for row in rows})
    candidates = sorted({0.5, *probabilities})

    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in candidates:
        candidate = RainProbabilityModel(
            global_rate=model.global_rate,
            month_rates=model.month_rates,
            rain_today_rates=model.rain_today_rates,
            threshold=threshold,
            train_row_count=model.train_row_count,
        )
        f1_score = evaluate_model(candidate, rows)["f1"]
        if f1_score > best_f1:
            best_threshold = threshold
            best_f1 = f1_score

    return best_threshold


def evaluate_model(model: RainProbabilityModel, rows: list[dict[str, str]]) -> dict[str, object]:
    """Calcula metricas de classificacao."""
    confusion = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}

    for row in rows:
        actual = int(row["target_rain_tomorrow"])
        predicted = model.predict(row)
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
        "predicted_rain_rate": round(_predicted_positive_rate(model, rows), 4) if rows else 0.0,
        "confusion_matrix": confusion,
    }


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
    report = {
        "model_name": "monthly_persistence_rain_probability",
        "target": "target_rain_tomorrow",
        "split_date": split_date,
        "train_metrics": evaluate_model(model, train_rows),
        "test_metrics": evaluate_model(model, test_rows),
        "model": model.to_dict(),
        "interpretation": {
            "global_rain_probability": round(model.global_rate, 4),
            "monthly_rain_probabilities": {
                month: round(rate, 4) for month, rate in sorted(model.month_rates.items())
            },
            "rain_persistence_probabilities": {
                key: round(rate, 4) for key, rate in sorted(model.rain_today_rates.items())
            },
            "decision_threshold": round(model.threshold, 4),
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


def write_predictions(
    model: RainProbabilityModel,
    input_path: str | Path,
    output_path: str | Path,
) -> dict[str, object]:
    """Gera predicoes para uma base de features."""
    rows = read_csv(input_path)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(rows[0].keys()) + ["predicted_probability", "predicted_rain_tomorrow"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            probability = model.predict_proba(row)
            output_row = dict(row)
            output_row["predicted_probability"] = f"{probability:.4f}"
            output_row["predicted_rain_tomorrow"] = str(model.predict(row))
            writer.writerow(output_row)

    return {"row_count": len(rows), "output_path": str(output_path)}


def _group_positive_rates(rows: Iterable[dict[str, str]], column: str) -> dict[str, float]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[str(row[column])].append(row)
    return {group: _positive_rate(group_rows) for group, group_rows in groups.items()}


def _positive_rate(rows: Iterable[dict[str, str]]) -> float:
    materialized_rows = list(rows)
    if not materialized_rows:
        return 0.0
    positives = sum(int(row["target_rain_tomorrow"]) for row in materialized_rows)
    return positives / len(materialized_rows)


def _predicted_positive_rate(model: RainProbabilityModel, rows: list[dict[str, str]]) -> float:
    return _safe_divide(sum(model.predict(row) for row in rows), len(rows))


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _period(rows: list[dict[str, str]]) -> dict[str, str | None]:
    if not rows:
        return {"start": None, "end": None}
    return {"start": rows[0]["date"], "end": rows[-1]["date"]}

