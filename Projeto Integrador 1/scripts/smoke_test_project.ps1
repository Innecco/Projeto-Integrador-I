$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name falhou com codigo $LASTEXITCODE"
    }
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$TemplatePath = Join-Path $ProjectRoot "modelo\Modelo de Projeto CDML.docx"
$WorkingTemplatePath = Join-Path $ProjectRoot "outputs\reports\_template_working_copy.docx"
$DocxPath = Join-Path $ProjectRoot "outputs\reports\Predicao_Chuvas_Brasilia_Enzo_Innecco.docx"

Set-Location $ProjectRoot

if (-not (Test-Path $VenvPython)) {
    Invoke-Checked -Name "setup_venv" -Command {
        powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\setup_venv.ps1")
    }
}

Invoke-Checked -Name "unit_tests" -Command {
    & $VenvPython -m unittest discover -s tests
}

Invoke-Checked -Name "daily_pipeline" -Command {
    & $VenvPython scripts\run_daily_pipeline.py
}

if (Test-Path $TemplatePath) {
    Copy-Item -LiteralPath $TemplatePath -Destination $WorkingTemplatePath -Force
}

Invoke-Checked -Name "build_final_docx" -Command {
    & $VenvPython scripts\build_final_docx.py
}

Remove-Item -LiteralPath $WorkingTemplatePath -Force -ErrorAction SilentlyContinue

@"
from docx import Document
from pathlib import Path

path = Path(r"$DocxPath")
doc = Document(path)
all_text = "\n".join(
    [paragraph.text for paragraph in doc.paragraphs]
    + [cell.text for table in doc.tables for row in table.rows for cell in row.cells]
)

required = [
    "Enzo Innecco",
    "22253256",
    "Airflow",
    "Goi\u00e2nia",
    "S\u00e3o Paulo",
    "ANEXO II",
    "https://github.com/Innecco/Projeto-Integrador-I/tree/main",
]
missing = [item for item in required if item not in all_text]
forbidden = ["professor", "Professor", "orientador", "Orientador", "docente", "Docente"]
found_forbidden = [item for item in forbidden if item in all_text]

if missing:
    raise SystemExit(f"Conteudo obrigatorio ausente no DOCX: {missing}")
if found_forbidden:
    raise SystemExit(f"Termos proibidos encontrados no DOCX: {found_forbidden}")
if len(doc.inline_shapes) < 4:
    raise SystemExit("DOCX deveria conter pelo menos 4 graficos.")
if len(doc.tables) < 8:
    raise SystemExit("DOCX deveria conter pelo menos 8 tabelas.")

print("DOCX validado com sucesso.")
"@ | & $VenvPython -

if ($LASTEXITCODE -ne 0) {
    throw "docx_content_validation falhou com codigo $LASTEXITCODE"
}

Write-Host "Smoke test concluido com sucesso."
