"""Interface de linha de comando do projeto."""

from __future__ import annotations

import argparse
import json

from .backtest import run_contract_backtest
from .eda import generate_weather_eda
from .features import build_rain_features
from .pipeline import validate_csv, write_json_report
from .rain_model import load_model, train_and_backtest, write_predictions
from .weather_api import fetch_multi_city_weather_to_csv, fetch_weather_to_csv


def build_parser() -> argparse.ArgumentParser:
    """Monta os comandos disponiveis."""
    parser = argparse.ArgumentParser(description="Ferramentas do Projeto Integrador 1.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Valida um CSV por contrato.")
    validate_parser.add_argument("--contract", required=True, help="Caminho do contrato JSON.")
    validate_parser.add_argument("--input", required=True, help="Caminho do CSV de entrada.")

    backtest_parser = subparsers.add_parser("backtest", help="Executa backtest por snapshots.")
    backtest_parser.add_argument("--contract", required=True, help="Caminho do contrato JSON.")
    backtest_parser.add_argument("--input-dir", required=True, help="Pasta com snapshots CSV.")
    backtest_parser.add_argument("--output", required=True, help="Relatorio JSON de saida.")

    fetch_weather_parser = subparsers.add_parser(
        "fetch-weather",
        help="Coleta dados diarios historicos da Open-Meteo.",
    )
    fetch_weather_parser.add_argument("--config", required=True, help="Configuracao JSON.")
    fetch_weather_parser.add_argument("--output", required=True, help="CSV bruto de saida.")

    fetch_multi_parser = subparsers.add_parser(
        "fetch-weather-multi-city",
        help="Coleta dados diarios historicos para varias cidades.",
    )
    fetch_multi_parser.add_argument("--config", required=True, help="Configuracao JSON.")
    fetch_multi_parser.add_argument("--output-dir", required=True, help="Pasta dos CSVs por cidade.")
    fetch_multi_parser.add_argument("--combined-output", required=True, help="CSV consolidado.")

    features_parser = subparsers.add_parser(
        "build-weather-features",
        help="Cria features para previsao de chuva no dia seguinte.",
    )
    features_parser.add_argument("--input", required=True, help="CSV diario bruto.")
    features_parser.add_argument("--output", required=True, help="CSV de features.")
    features_parser.add_argument(
        "--rain-threshold-mm",
        type=float,
        default=1.0,
        help="Precipitacao minima para considerar chuva.",
    )

    train_parser = subparsers.add_parser(
        "train-rain-model",
        help="Treina e avalia o modelo simples de chuva.",
    )
    train_parser.add_argument("--input", required=True, help="CSV de features.")
    train_parser.add_argument("--split-date", required=True, help="Data inicial do teste.")
    train_parser.add_argument("--report", required=True, help="Relatorio JSON de metricas.")
    train_parser.add_argument("--model", required=True, help="Modelo JSON de saida.")

    predict_parser = subparsers.add_parser(
        "predict-rain",
        help="Gera predicoes com um modelo ja treinado.",
    )
    predict_parser.add_argument("--model", required=True, help="Modelo JSON.")
    predict_parser.add_argument("--input", required=True, help="CSV de features.")
    predict_parser.add_argument("--output", required=True, help="CSV com predicoes.")

    eda_parser = subparsers.add_parser(
        "generate-weather-eda",
        help="Gera graficos e resumos de analise exploratoria.",
    )
    eda_parser.add_argument("--input", required=True, help="CSV consolidado multi-cidade.")
    eda_parser.add_argument("--output-dir", required=True, help="Pasta para graficos.")
    eda_parser.add_argument(
        "--rain-threshold-mm",
        type=float,
        default=1.0,
        help="Precipitacao minima para considerar chuva.",
    )

    return parser


def main() -> int:
    """Executa a CLI."""
    args = build_parser().parse_args()

    if args.command == "validate":
        result = validate_csv(args.input, args.contract).to_dict()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["is_valid"] else 1

    if args.command == "backtest":
        report = run_contract_backtest(args.input_dir, args.contract)
        write_json_report(report, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["is_valid"] else 1

    if args.command == "fetch-weather":
        report = fetch_weather_to_csv(args.config, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "fetch-weather-multi-city":
        report = fetch_multi_city_weather_to_csv(
            args.config,
            args.output_dir,
            args.combined_output,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "build-weather-features":
        report = build_rain_features(args.input, args.output, args.rain_threshold_mm)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "train-rain-model":
        report = train_and_backtest(args.input, args.split_date, args.report, args.model)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "predict-rain":
        model = load_model(args.model)
        report = write_predictions(model, args.input, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "generate-weather-eda":
        report = generate_weather_eda(args.input, args.output_dir, args.rain_threshold_mm)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
