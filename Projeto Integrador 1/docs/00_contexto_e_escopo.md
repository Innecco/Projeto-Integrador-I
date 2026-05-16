# 00 - Contexto e Escopo

## Contextualizacao do problema

Brasilia possui sazonalidade climatica marcada por periodos secos e chuvosos. A ocorrencia de chuva no dia seguinte afeta decisoes operacionais de deslocamento, eventos, atividades externas, aulas praticas e uso de infraestrutura urbana.

O projeto propoe uma plataforma robusta de dados para estimar a ocorrencia de chuva no dia seguinte em Brasilia. Para contextualizar a cidade-alvo, a analise exploratoria compara Brasilia com Goiania e Sao Paulo.

## Justificativa

O tema permite demonstrar um ciclo completo de engenharia de dados e machine learning:

- ingestao por API;
- configuracao por `.env`;
- isolamento por `.venv`;
- validacao por contratos;
- armazenamento em camadas;
- analise exploratoria com graficos;
- comparacao regional;
- modelo explicavel;
- orquestracao diaria por Airflow;
- metricas auditaveis.

## Objetivo geral

Construir uma solucao robusta para previsao de ocorrencia de chuva no dia seguinte em Brasilia, usando dados meteorologicos historicos da Open-Meteo e comparacao exploratoria com Goiania e Sao Paulo.

## Objetivos especificos

1. coletar dados meteorologicos por API;
2. configurar URL, chave opcional, periodo e agendamento por `.env`;
3. validar dados por contrato;
4. construir base supervisionada para Brasilia;
5. gerar graficos de analise exploratoria comparativa;
6. treinar e avaliar modelo explicavel;
7. orquestrar atualizacao diaria as 05:00 por Airflow;
8. organizar anexos tecnicos para entrega.

## Fora do escopo

- substituir previsao meteorologica profissional;
- previsao horaria;
- aplicacao web produtiva;
- modelagem meteorologica fisica.
