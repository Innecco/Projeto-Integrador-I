# Contribuicao e Manutencao

Este projeto foi organizado para manter rastreabilidade entre codigo, dados, testes, relatorios e automacao.

## Fluxo recomendado

1. Criar ou atualizar uma branch a partir de `main`.
2. Alterar apenas os arquivos relacionados ao objetivo da mudanca.
3. Executar os testes automatizados.
4. Executar o smoke test quando a mudanca afetar pipeline, relatorio, dados ou modelo.
5. Atualizar a documentacao sempre que a forma de execucao, arquitetura ou artefatos mudar.

## Comandos de validacao

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
powershell -ExecutionPolicy Bypass -File scripts/smoke_test_project.ps1
powershell -ExecutionPolicy Bypass -File scripts/github_release_check.ps1
```

## Padroes do projeto

- Manter codigo Python legivel, com funcoes pequenas e nomes descritivos.
- Evitar dependencias novas sem necessidade clara.
- Centralizar configuracoes operacionais em `.env.example`.
- Nao versionar `.env`, `.venv/`, caches, logs ou dados locais volumosos.
- Registrar metricas e artefatos em `outputs/reports/` quando forem relevantes para auditoria.

## Antes de abrir pull request

- Os testes devem passar.
- O README deve continuar coerente com o estado real do projeto.
- O DOCX final deve ser regenerado se houver mudanca relevante no relatorio.
- O workflow de CI deve permanecer verde apos o push.
