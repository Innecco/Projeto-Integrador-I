# 02 - Fontes de Dados e Integracao

## Inventario de fontes

| Fonte | Tipo | Formato | Periodicidade | Responsavel | Status |
| --- | --- | --- | --- | --- | --- |
| Open-Meteo Historical Weather API | API publica meteorologica | JSON convertido para CSV | Sob demanda | Open-Meteo | Integrada |

## Criterios minimos de aceite

| Criterio | Status |
| --- | --- |
| Origem identificada | Atendido |
| Documentacao publica | Atendido |
| Formato estruturado | Atendido |
| Volume compativel com ambiente local | Atendido |
| Criterios de qualidade definidos | Atendido por contrato JSON |
| Possibilidade de reproducao | Atendido por configuracao versionada |

## Estrategia de integracao

1. extrair dados historicos diarios via API;
2. armazenar copia em `data/raw`;
3. validar colunas obrigatorias, duplicidade e tipos;
4. registrar falhas de qualidade;
5. gerar features em `data/processed`;
6. produzir relatorio de execucao em `outputs/reports`.

## Variaveis coletadas

| Campo | Descricao |
| --- | --- |
| `date` | Data da observacao |
| `temperature_2m_mean` | Temperatura media diaria |
| `temperature_2m_max` | Temperatura maxima diaria |
| `temperature_2m_min` | Temperatura minima diaria |
| `precipitation_sum` | Precipitacao total diaria em milimetros |
| `rain_sum` | Chuva total diaria em milimetros |
| `precipitation_hours` | Quantidade de horas com precipitacao |
| `wind_speed_10m_max` | Velocidade maxima do vento a 10 metros |
| `wind_speed_10m_mean` | Velocidade media do vento a 10 metros |
| `relative_humidity_2m_mean` | Umidade relativa media a 2 metros |
