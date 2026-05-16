# Projeto Integrador 1

Projeto: Predicao Chuvas Brasilia.

Este repositorio implementa uma solucao robusta de engenharia de dados e machine learning para estimar a ocorrencia de chuva no dia seguinte em Brasilia. A analise tambem compara Brasilia com Goiania e Sao Paulo para enriquecer a leitura exploratoria.

## Fonte de dados

Fonte: [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)

Observacao operacional: a Open-Meteo nao exige chave de API para uso nao comercial. Mesmo assim, o projeto possui `OPEN_METEO_API_KEY` no `.env` para suportar evolucao para plano comercial ou ambiente produtivo.

## Cidades

| Cidade | Papel no projeto |
| --- | --- |
| Brasilia | Cidade-alvo da predicao |
| Goiania | Cidade de comparacao regional |
| Sao Paulo | Cidade de comparacao climatica |

## Estrutura

```text
Projeto Integrador 1/
|-- .env
|-- .env.example
|-- airflow/
|   `-- dags/
|-- config/
|-- data/
|   |-- raw/
|   `-- processed/
|-- docs/
|-- modelo/
|-- outputs/
|   |-- figures/
|   |-- models/
|   `-- reports/
|-- scripts/
|-- src/
|   `-- projeto_integrador/
|-- tests/
|-- requirements-core.txt
`-- requirements-airflow.txt
```

## Ambiente virtual

Crie e prepare o `.venv` com:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_venv.ps1
```

Depois execute comandos com:

```powershell
.venv\Scripts\python.exe scripts\run_daily_pipeline.py
```

## Variaveis de ambiente

As configuracoes operacionais ficam no `.env`:

```text
OPEN_METEO_ARCHIVE_URL=https://archive-api.open-meteo.com/v1/archive
OPEN_METEO_API_KEY=
WEATHER_START_DATE=2021-01-01
WEATHER_END_DATE=yesterday
WEATHER_TIMEZONE=America/Sao_Paulo
RAIN_THRESHOLD_MM=1.0
PIPELINE_SPLIT_DATE=2025-01-01
MAIN_CITY_ID=brasilia
AIRFLOW_DAG_SCHEDULE=0 5 * * *
```

## Execucao operacional

Pipeline completo:

```powershell
python scripts/run_daily_pipeline.py
```

O pipeline executa:

1. coleta multi-cidade na Open-Meteo;
2. validacao dos dados brutos;
3. geracao de features de Brasilia;
4. validacao da base supervisionada;
5. treinamento e avaliacao temporal;
6. geracao de predicoes;
7. graficos de analise exploratoria;
8. relatorio operacional em JSON.

## Airflow

DAG: `airflow/dags/predicao_chuvas_brasilia_daily.py`

Guia passo a passo: `docs/GUIA_EXECUCAO_AIRFLOW_E_TESTES.md`

Docker Compose pronto: `docker-compose.airflow.yml`

Agenda:

```text
0 5 * * *
```

No Windows, recomenda-se executar Airflow por WSL ou Docker. O pipeline Python local permanece executavel pelo `.venv`.

Para subir com Docker:

```powershell
docker compose -f docker-compose.airflow.yml up
```

Depois acesse `http://localhost:8080` com usuario `admin` e senha `admin`.

## Teste ponta a ponta

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke_test_project.ps1
```

## Resultados da ultima execucao

Executado em 2026-05-16:

- dados multi-cidade: 5.883 registros;
- cidades: Brasilia, Goiania e Sao Paulo;
- dados brutos validados: zero erros;
- features de Brasilia: 1.960 exemplos;
- teste temporal: 2025-01-01 a 2026-05-14;
- acuracia: `0.7916`;
- precisao: `0.7318`;
- recall: `0.7816`;
- F1-score: `0.7559`;
- testes automatizados: 9 passaram.

## Artefatos principais

- `outputs/reports/Predicao_Chuvas_Brasilia_Enzo_Innecco.docx`
- `outputs/reports/daily_pipeline_run_report.json`
- `outputs/reports/weather_city_comparison_summary.csv`
- `outputs/reports/rain_model_backtest.json`
- `outputs/reports/rain_predictions.csv`
- `outputs/figures/*.png`
- `airflow/dags/predicao_chuvas_brasilia_daily.py`

## Anexos recomendados

Para a entrega academica, os anexos mais importantes sao:

- termo de abertura;
- arquitetura logica;
- contratos de dados;
- DAG Airflow;
- relatorio de execucao diaria;
- resumo comparativo das cidades;
- graficos de EDA;
- metricas do modelo;
- codigo-fonte.
