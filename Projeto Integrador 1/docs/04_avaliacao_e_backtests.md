# 04 - Avaliacao e Backtests

## Objetivo dos backtests

Os backtests validam o comportamento tecnico do pipeline e o desempenho temporal do modelo de chuva para Brasilia.

## Resultado da execucao local

Executado em 2026-05-16:

| Verificacao | Resultado |
| --- | --- |
| Testes unitarios | 9 testes passaram |
| Dados brutos multi-cidade | 5.883 registros, zero erros |
| Features de Brasilia | 1.960 exemplos, zero erros |
| Cidades comparadas | Brasilia, Goiania e Sao Paulo |
| Graficos de EDA | 4 arquivos PNG gerados |
| Airflow | DAG criada para execucao diaria as 05:00 |

## Resultado do modelo

Recorte:

- treino: 2021-01-01 a 2024-12-31;
- teste temporal: 2025-01-01 a 2026-05-14;
- alvo: chuva no dia seguinte com precipitacao minima de 1 mm.

Metricas no teste temporal:

| Metrica | Valor |
| --- | ---: |
| Acuracia | 0.7916 |
| Precisao | 0.7318 |
| Recall | 0.7816 |
| F1-score | 0.7559 |

Matriz de confusao:

| Classe | Valor |
| --- | ---: |
| Verdadeiro positivo | 161 |
| Verdadeiro negativo | 234 |
| Falso positivo | 59 |
| Falso negativo | 45 |

## Comparacao exploratoria

Resumo geral do periodo coletado:

| Cidade | Dias | Dias com chuva | Taxa de chuva | Precipitacao total | Temperatura media |
| --- | ---: | ---: | ---: | ---: | ---: |
| Brasilia | 1.961 | 743 | 37,9% | 5.893,7 mm | 22,0 C |
| Goiania | 1.961 | 697 | 35,5% | 5.247,3 mm | 24,0 C |
| Sao Paulo | 1.961 | 865 | 44,1% | 7.257,6 mm | 19,7 C |

## Validacao do recorte

O recorte que deve ser validado na apresentacao e: Brasilia como cidade-alvo, Goiania e Sao Paulo como comparacao exploratoria, limiar de chuva em 1 mm, atualizacao diaria as 05:00 e corte temporal de avaliacao em 2025-01-01.
