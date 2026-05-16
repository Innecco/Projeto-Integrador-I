"""Executa o pipeline operacional diario do projeto."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.projeto_integrador.eda import generate_weather_eda
from src.projeto_integrador.env import load_project_env
from src.projeto_integrador.features import build_rain_features
from src.projeto_integrador.pipeline import validate_csv, write_json_report
from src.projeto_integrador.rain_model import load_model, train_and_backtest, write_predictions
from src.projeto_integrador.weather_api import fetch_multi_city_weather_to_csv


def main() -> None:
    load_project_env(ROOT / ".env")
    main_city_id = os.getenv("MAIN_CITY_ID", "brasilia")
    rain_threshold = float(os.getenv("RAIN_THRESHOLD_MM", "1.0"))
    split_date = os.getenv("PIPELINE_SPLIT_DATE", "2025-01-01")

    raw_dir = ROOT / "data" / "raw"
    processed_dir = ROOT / "data" / "processed"
    reports_dir = ROOT / "outputs" / "reports"
    figures_dir = ROOT / "outputs" / "figures"
    models_dir = ROOT / "outputs" / "models"

    multi_raw_path = raw_dir / "weather_multi_city_daily.csv"
    main_city_raw_path = raw_dir / f"weather_{main_city_id}_daily.csv"
    features_path = processed_dir / f"weather_{main_city_id}_features.csv"
    model_path = models_dir / "rain_probability_model.json"
    backtest_path = reports_dir / "rain_model_backtest.json"
    predictions_path = reports_dir / "rain_predictions.csv"
    run_report_path = reports_dir / "daily_pipeline_run_report.json"

    fetch_report = fetch_multi_city_weather_to_csv(
        ROOT / "config" / "weather_locations.json",
        raw_dir,
        multi_raw_path,
    )
    raw_validation = validate_csv(multi_raw_path, ROOT / "config" / "data_contract_weather_daily.json")
    if not raw_validation.is_valid:
        raise RuntimeError(f"Dados brutos invalidos: {raw_validation.errors}")

    feature_report = build_rain_features(main_city_raw_path, features_path, rain_threshold)
    feature_validation = validate_csv(features_path, ROOT / "config" / "data_contract_weather_features.json")
    if not feature_validation.is_valid:
        raise RuntimeError(f"Features invalidas: {feature_validation.errors}")

    model_report = train_and_backtest(features_path, split_date, backtest_path, model_path)
    prediction_report = write_predictions(load_model(model_path), features_path, predictions_path)
    eda_report = generate_weather_eda(multi_raw_path, figures_dir, rain_threshold)

    run_report = {
        "executed_at": datetime.now().isoformat(timespec="seconds"),
        "main_city_id": main_city_id,
        "rain_threshold_mm": rain_threshold,
        "split_date": split_date,
        "fetch": fetch_report,
        "raw_validation": raw_validation.to_dict(),
        "features": feature_report,
        "feature_validation": feature_validation.to_dict(),
        "model_test_metrics": model_report["test_metrics"],
        "predictions": prediction_report,
        "eda": eda_report,
    }
    write_json_report(run_report, run_report_path)
    print(json.dumps(run_report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
