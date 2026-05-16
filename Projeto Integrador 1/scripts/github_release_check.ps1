$ErrorActionPreference = "Stop"

function Assert-FileExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Arquivo obrigatorio ausente: $Description ($Path)"
    }
    Write-Host "[OK] $Description"
}

function Assert-TextContains {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Expected,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    $content = Get-Content -Raw -LiteralPath $Path
    if ($content -notlike "*$Expected*") {
        throw "Conteudo esperado ausente em ${Path}: $Description"
    }
    Write-Host "[OK] $Description"
}

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
    Write-Host "[OK] $Name"
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Set-Location $ProjectRoot
Write-Host "Validacao para publicacao no GitHub"
Write-Host "Projeto: $ProjectRoot"

Assert-FileExists -Path "README.md" -Description "README principal"
Assert-FileExists -Path ".gitignore" -Description ".gitignore"
Assert-FileExists -Path ".gitattributes" -Description ".gitattributes"
Assert-FileExists -Path ".dockerignore" -Description ".dockerignore"
Assert-FileExists -Path ".env.example" -Description ".env.example"
Assert-FileExists -Path ".github\workflows\ci.yml" -Description "Workflow CI"
Assert-FileExists -Path "CONTRIBUTING.md" -Description "Guia de contribuicao"
Assert-FileExists -Path "CHANGELOG.md" -Description "Changelog"
Assert-FileExists -Path "docker-compose.airflow.yml" -Description "Docker Compose Airflow"
Assert-FileExists -Path "airflow\dags\predicao_chuvas_brasilia_daily.py" -Description "DAG Airflow"
Assert-FileExists -Path "docs\GITHUB_PUBLICACAO.md" -Description "Checklist GitHub"
Assert-FileExists -Path "outputs\reports\Predicao_Chuvas_Brasilia_Enzo_Innecco.docx" -Description "DOCX final"

Assert-TextContains -Path ".gitignore" -Expected ".env" -Description ".env protegido no .gitignore"
Assert-TextContains -Path ".gitignore" -Expected ".venv/" -Description ".venv protegido no .gitignore"
Assert-TextContains -Path "README.md" -Expected "https://github.com/Innecco/Projeto-Integrador-I/tree/main" -Description "README aponta para branch main"
Assert-TextContains -Path "scripts\build_final_docx.py" -Expected "https://github.com/Innecco/Projeto-Integrador-I/tree/main" -Description "DOCX usa link main"

if (-not (Test-Path $VenvPython)) {
    Invoke-Checked -Name "setup_venv" -Command {
        powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\setup_venv.ps1")
    }
}

Invoke-Checked -Name "unit_tests" -Command {
    & $VenvPython -m unittest discover -s tests
}

Invoke-Checked -Name "smoke_test_project" -Command {
    powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\smoke_test_project.ps1")
}

$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    Write-Host "[OK] Git encontrado: $($git.Source)"
    git rev-parse --is-inside-work-tree | Out-Null
    if ($LASTEXITCODE -eq 0) {
        git check-ignore .env | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw ".env nao esta protegido pelo .gitignore."
        }
        git check-ignore .venv\pyvenv.cfg | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw ".venv nao esta protegido pelo .gitignore."
        }
        Write-Host "[OK] Git ignore validado"
    } else {
        Write-Host "[AVISO] Pasta ainda nao e um repositorio Git inicializado; validacao git check-ignore ignorada."
    }
} else {
    Write-Host "[AVISO] Git nao encontrado no PATH. Instale Git para publicar no repositorio remoto."
}

Write-Host "Projeto pronto para publicacao no GitHub."
