"""DAG Airflow para atualizar a analise de chuvas diariamente as 5h."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pendulum
from airflow.decorators import dag, task


PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "/opt/airflow/project"))
PYTHON_BIN = os.getenv("PROJECT_PYTHON_BIN", "python")
SCHEDULE = os.getenv("AIRFLOW_DAG_SCHEDULE", "0 5 * * *")


@dag(
    dag_id="predicao_chuvas_brasilia_daily",
    description="Coleta Open-Meteo, atualiza EDA, treina modelo e publica artefatos diariamente.",
    schedule=SCHEDULE,
    start_date=pendulum.datetime(2026, 5, 16, tz="America/Sao_Paulo"),
    catchup=False,
    tags=["projeto-integrador", "chuva", "open-meteo"],
)
def predicao_chuvas_brasilia_daily() -> None:
    """Executa o pipeline operacional completo."""

    @task()
    def run_daily_pipeline() -> str:
        script_path = PROJECT_ROOT / "scripts" / "run_daily_pipeline.py"
        subprocess.run(
            [PYTHON_BIN, str(script_path)],
            cwd=PROJECT_ROOT,
            check=True,
        )
        return str(PROJECT_ROOT / "outputs" / "reports" / "daily_pipeline_run_report.json")

    run_daily_pipeline()


predicao_chuvas_brasilia_daily()

