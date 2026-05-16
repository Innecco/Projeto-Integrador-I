# Termo de Abertura do Projeto

## Nome do projeto

Predicao Chuvas Brasilia.

## Integrantes

| Matricula | Nome |
| --- | --- |
| 22253256 | Enzo Innecco |

## Problema

A ocorrencia de chuva no dia seguinte influencia decisoes operacionais em Brasilia. O projeto desenvolve uma solucao robusta para prever esse evento, com comparacao exploratoria entre Brasilia, Goiania e Sao Paulo.

## Objetivo

Construir pipeline, EDA, modelo e orquestracao diaria para previsao de chuva no dia seguinte em Brasilia.

## Escopo

- coleta de dados historicos via Open-Meteo;
- configuracao por `.env`;
- ambiente `.venv`;
- validacao de contrato;
- transformacao em features;
- EDA comparativa;
- modelo de classificacao explicavel;
- Airflow diario as 05:00;
- documentacao e anexos.

## Fora do escopo

- previsao horaria;
- substituicao de servicos meteorologicos profissionais;
- modelo meteorologico fisico;
- aplicacao web produtiva.

## Riscos e mitigacoes

| Risco | Impacto | Mitigacao |
| --- | --- | --- |
| API indisponivel | Impede atualizacao diaria | Manter ultima base coletada e relatorio de execucao |
| Mudanca no contrato da API | Quebra coleta ou validacao | Validar dados antes de processar |
| Airflow fora do Windows nativo | Dificulta execucao local | Usar WSL ou Docker para a DAG |
| Chave de API comercial futura | Exige segredo operacional | Campo `OPEN_METEO_API_KEY` preparado no `.env` |
