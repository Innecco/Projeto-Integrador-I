# 05 - Relatorio CDML

Conteudo-base do relatorio final. O arquivo `.docx` final e gerado por `scripts/build_final_docx.py`.

## Projeto

Predicao Chuvas Brasilia.

## Estudante

Enzo Innecco - matricula 22253256.

## Resumo tecnico

O projeto implementa uma solucao robusta para estimar chuva no dia seguinte em Brasilia, com comparacao exploratoria entre Brasilia, Goiania e Sao Paulo.

## Componentes entregues

- `.env` e `.env.example`;
- ambiente `.venv` documentado;
- coletor Open-Meteo;
- contratos de dados;
- EDA com graficos PNG;
- comparacao regional;
- modelo explicavel;
- DAG Airflow diaria as 05:00;
- relatorio DOCX final;
- anexos tecnicos organizados.
- repositorio GitHub: https://github.com/Innecco/Projeto-Integrador-I/tree/main.

## Resultados

- dados multi-cidade: 5.883 registros;
- features de Brasilia: 1.960 exemplos;
- F1-score temporal: 0.7559;
- testes automatizados: 13 passaram;
- auditoria estrutural do DOCX: sem achados apos correcao.
