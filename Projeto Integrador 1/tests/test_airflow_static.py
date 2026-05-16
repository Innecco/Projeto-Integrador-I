import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DAG_PATH = PROJECT_ROOT / "airflow" / "dags" / "predicao_chuvas_brasilia_daily.py"
COMPOSE_PATH = PROJECT_ROOT / "docker-compose.airflow.yml"


class AirflowStaticTest(unittest.TestCase):
    def test_dag_file_is_valid_python(self) -> None:
        source = DAG_PATH.read_text(encoding="utf-8")

        ast.parse(source)

    def test_dag_has_expected_operational_contract(self) -> None:
        source = DAG_PATH.read_text(encoding="utf-8")

        self.assertIn('dag_id="predicao_chuvas_brasilia_daily"', source)
        self.assertIn('SCHEDULE = os.getenv("AIRFLOW_DAG_SCHEDULE", "0 5 * * *")', source)
        self.assertIn('tz="America/Sao_Paulo"', source)
        self.assertIn('script_path = PROJECT_ROOT / "scripts" / "run_daily_pipeline.py"', source)
        self.assertIn("subprocess.run(", source)
        self.assertIn("check=True", source)
        self.assertIn("catchup=False", source)

    def test_compose_file_exposes_airflow_with_daily_schedule(self) -> None:
        compose = COMPOSE_PATH.read_text(encoding="utf-8")

        self.assertIn("apache/airflow:2.10.5-python3.12", compose)
        self.assertIn('"8080:8080"', compose)
        self.assertIn('AIRFLOW_DAG_SCHEDULE: "0 5 * * *"', compose)
        self.assertIn("PROJECT_ROOT: /opt/airflow/project", compose)
        self.assertIn("./airflow/dags:/opt/airflow/dags", compose)
        self.assertIn("airflow db migrate", compose)
        self.assertIn("airflow scheduler", compose)
        self.assertIn("exec airflow webserver", compose)


if __name__ == "__main__":
    unittest.main()
