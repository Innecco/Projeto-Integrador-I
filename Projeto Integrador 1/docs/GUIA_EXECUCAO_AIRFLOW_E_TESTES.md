# Guia de Execucao, Airflow e Testes

Este guia foi escrito para uma pessoa sem familiaridade tecnica conseguir subir, testar e verificar o projeto.

## 1. O que este projeto faz

O projeto coleta dados meteorologicos da Open-Meteo, compara Brasilia com Goiania e Sao Paulo, gera graficos de analise exploratoria, treina um modelo de previsao de chuva para Brasilia e cria relatorios para entrega academica.

## 2. Arquivos mais importantes

| Arquivo ou pasta | Para que serve |
| --- | --- |
| `.env` | Guarda URL da API, chave opcional, datas, cidade principal e horario do Airflow |
| `.venv` | Ambiente Python isolado do projeto |
| `scripts/run_daily_pipeline.py` | Executa coleta, validacao, EDA, modelo e predicoes |
| `scripts/smoke_test_project.ps1` | Testa tudo de ponta a ponta no Windows |
| `airflow/dags/predicao_chuvas_brasilia_daily.py` | DAG que roda o pipeline todo dia as 05:00 |
| `docker-compose.airflow.yml` | Sobe o Airflow com Docker |
| `outputs/reports/Predicao_Chuvas_Brasilia_Enzo_Innecco.docx` | Relatorio final |

## 3. Teste rapido no Windows sem Airflow

Abra o PowerShell na pasta do projeto:

```powershell
cd "C:\Users\enzoi\OneDrive\Documentos\Projeto Integrador 1"
```

Execute:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke_test_project.ps1
```

O teste esta correto quando aparecer:

```text
Smoke test concluido com sucesso.
```

Esse comando prepara o `.venv` se necessario, roda os testes, executa o pipeline, regenera o DOCX e verifica se o documento possui os conteudos obrigatorios.

Mesmo quando o Docker ainda nao pode ser iniciado, os testes automatizados validam o contrato operacional do Airflow:

- arquivo da DAG em Python valido;
- agenda configurada para 05:00;
- chamada para `scripts/run_daily_pipeline.py`;
- configuracao principal do `docker-compose.airflow.yml`.

Os testes tambem validam o comportamento de contingencia da API: se a Open-Meteo retornar limite temporario de requisicoes e ja houver CSV bruto local, o pipeline reaproveita os dados existentes e continua a execucao.

## 4. Subir o Airflow com Docker

Requisitos:

- Docker Desktop instalado;
- Docker Compose disponivel;
- WSL2 operacional no Windows;
- virtualizacao habilitada na BIOS/UEFI;
- internet ativa para baixar a imagem do Airflow na primeira execucao.

Se o Docker Desktop ainda nao estiver instalado, instale pelo site oficial:

```text
https://www.docker.com/products/docker-desktop/
```

Ou, em um PowerShell com permissao adequada:

```powershell
winget install --id Docker.DockerDesktop --source winget --accept-source-agreements --accept-package-agreements
```

Depois da instalacao, reinicie o computador se o instalador solicitar, abra o Docker Desktop e so entao rode o preflight:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/preflight_airflow.ps1
```

Se o preflight indicar que nao existe distribuicao WSL, instale Ubuntu:

```powershell
wsl --install -d Ubuntu-24.04
```

Se o preflight indicar virtualizacao desativada, habilite Intel VT-x/Virtualization Technology na BIOS/UEFI e reinicie o computador.

Na pasta do projeto, execute:

```powershell
docker compose -f docker-compose.airflow.yml up
```

Depois abra no navegador:

```text
http://localhost:8080
```

Login:

```text
usuario: admin
senha: admin
```

Procure a DAG:

```text
predicao_chuvas_brasilia_daily
```

Ela ja esta configurada para rodar todos os dias as 05:00.

## 5. Rodar a DAG manualmente

No Airflow:

1. abra `predicao_chuvas_brasilia_daily`;
2. clique no botao de play;
3. escolha a opcao para disparar a DAG;
4. aguarde a tarefa ficar verde.

Se a tarefa ficar verde, o pipeline rodou.

## 6. Onde ver os resultados

| Resultado | Caminho |
| --- | --- |
| Relatorio final | `outputs/reports/Predicao_Chuvas_Brasilia_Enzo_Innecco.docx` |
| Relatorio da execucao diaria | `outputs/reports/daily_pipeline_run_report.json` |
| Metricas do modelo | `outputs/reports/rain_model_backtest.json` |
| Predicoes | `outputs/reports/rain_predictions.csv` |
| Resumo das cidades | `outputs/reports/weather_city_comparison_summary.csv` |
| Graficos | `outputs/figures/` |

## 7. Ainda existe modelo de previsao?

Sim.

| Item | Caminho |
| --- | --- |
| Codigo do modelo | `src/projeto_integrador/rain_model.py` |
| Modelo treinado | `outputs/models/rain_probability_model.json` |
| Metricas | `outputs/reports/rain_model_backtest.json` |
| Predicoes | `outputs/reports/rain_predictions.csv` |

O modelo estima se havera chuva no dia seguinte em Brasilia.

## 8. Como saber que esta tudo certo

Verifique estes sinais:

- os testes passam;
- o teste estatico do Airflow passa;
- o arquivo `daily_pipeline_run_report.json` foi atualizado;
- os arquivos PNG existem em `outputs/figures`;
- o arquivo `rain_predictions.csv` existe;
- o arquivo `rain_probability_model.json` existe;
- o DOCX final abre normalmente.

## 9. Problemas comuns

| Problema | Como resolver |
| --- | --- |
| Docker nao abre | Inicie o Docker Desktop |
| WSL2 nao inicia | Habilite virtualizacao na BIOS/UEFI e reinicie |
| WSL sem distribuicao | Instale Ubuntu com `wsl --install -d Ubuntu-24.04` |
| Porta 8080 ocupada | Feche outro servico na porta 8080 ou altere o mapeamento no compose |
| Airflow demora na primeira vez | Aguarde a instalacao das dependencias |
| DAG nao aparece | Confirme que `airflow/dags/predicao_chuvas_brasilia_daily.py` existe |
| Erro de internet | A API nao foi acessada; tente novamente com internet ativa |
| Erro 429 da Open-Meteo | Aguarde alguns minutos; se ja houver dados em `data/raw`, o pipeline usa o CSV local |
| `.venv` ausente | Rode `scripts/setup_venv.ps1` ou o smoke test |

## 10. Comandos essenciais

Preparar ambiente:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_venv.ps1
```

Rodar testes:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
```

Rodar pipeline:

```powershell
.venv\Scripts\python.exe scripts/run_daily_pipeline.py
```

Subir Airflow:

```powershell
docker compose -f docker-compose.airflow.yml up
```

Parar Airflow:

```powershell
docker compose -f docker-compose.airflow.yml down
```
