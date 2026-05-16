# Publicacao no GitHub

Este checklist organiza a publicacao do projeto no repositorio:

```text
https://github.com/Innecco/Projeto-Integrador-I/tree/main
```

## 1. Validar localmente

Na pasta do projeto:

```powershell
cd "C:\Users\enzoi\OneDrive\Documentos\Projeto Integrador 1"
powershell -ExecutionPolicy Bypass -File scripts/github_release_check.ps1
```

Esse comando verifica arquivos essenciais, executa testes, roda o smoke test e confirma que o README aponta para a branch `main`.

## 2. Conferir arquivos que nao devem ser versionados

Nao envie:

- `.env`;
- `.venv/`;
- `__pycache__/`;
- logs locais;
- dados brutos ou processados pesados, exceto quando houver decisao explicita de versionar um recorte.

O arquivo `.gitignore` ja esta configurado para proteger esses itens.

## 3. Conferir artefatos principais

Antes do push, confirme que estes arquivos existem:

| Artefato | Caminho |
| --- | --- |
| README principal | `README.md` |
| Guia operacional | `docs/GUIA_EXECUCAO_AIRFLOW_E_TESTES.md` |
| Relatorio final | `outputs/reports/Predicao_Chuvas_Brasilia_Enzo_Innecco.docx` |
| DAG Airflow | `airflow/dags/predicao_chuvas_brasilia_daily.py` |
| Compose Airflow | `docker-compose.airflow.yml` |
| Exemplo de ambiente | `.env.example` |
| Workflow CI | `.github/workflows/ci.yml` |

## 4. Comandos Git sugeridos

Se o Git ainda nao estiver instalado, instale-o primeiro:

```text
https://git-scm.com/download/win
```

Depois, na pasta do projeto:

```powershell
git init
git remote add origin https://github.com/Innecco/Projeto-Integrador-I.git
git branch -M main
git status
git add .
git commit -m "Publica projeto integrador de predicao de chuvas"
git push -u origin main
```

Se o repositorio ja existir localmente, use apenas:

```powershell
git status
git add .
git commit -m "Atualiza projeto para publicacao no GitHub"
git push origin main
```

## 5. Conferencia no GitHub

Apos o push:

1. abra o repositorio no navegador;
2. confira se o README renderiza corretamente;
3. confirme que `.env` e `.venv/` nao apareceram;
4. abra a aba `Actions` e verifique se o workflow `CI` executou;
5. confira se o DOCX final esta disponivel em `outputs/reports/`.
