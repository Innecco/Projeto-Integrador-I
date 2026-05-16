# Airflow

Esta pasta contem a DAG operacional do projeto.

## DAG

Arquivo: `airflow/dags/predicao_chuvas_brasilia_daily.py`

Agendamento:

```text
0 5 * * *
```

Ou seja: todos os dias as 05:00 no timezone `America/Sao_Paulo`.

## Variaveis esperadas

Configure no ambiente do Airflow:

```text
PROJECT_ROOT=/caminho/do/projeto
PROJECT_PYTHON_BIN=/caminho/do/projeto/.venv/bin/python
AIRFLOW_DAG_SCHEDULE=0 5 * * *
```

No Windows, a recomendacao operacional e executar o Airflow em WSL ou Docker e apontar `PROJECT_ROOT` para o diretorio montado do projeto.

