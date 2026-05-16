$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "Preflight Airflow/Docker"
Write-Host "Projeto: $ProjectRoot"

$processor = Get-CimInstance Win32_Processor | Select-Object -First 1
if ($processor) {
    Write-Host "Virtualizacao no firmware: $($processor.VirtualizationFirmwareEnabled)"
    if ($processor.VirtualizationFirmwareEnabled -eq $false) {
        Write-Host "[AVISO] A virtualizacao esta desativada no firmware/BIOS."
        Write-Host "WSL2 e Docker Desktop dependem dessa configuracao para rodar corretamente."
    }
}

$wsl = Get-Command wsl -ErrorAction SilentlyContinue
if (-not $wsl) {
    Write-Host "[AVISO] WSL nao encontrado."
} else {
    Write-Host "[OK] WSL encontrado: $($wsl.Source)"
    wsl --status
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[AVISO] WSL retornou erro no status."
    }
    wsl -l -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[AVISO] Nenhuma distribuicao WSL operacional foi encontrada."
        Write-Host "Instale uma distribuicao, por exemplo: wsl --install -d Ubuntu-24.04"
    }
}

$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Host "[ERRO] Docker CLI nao encontrado no PATH."
    Write-Host "Instale Docker Desktop e reinicie o terminal."
    Write-Host "Download: https://www.docker.com/products/docker-desktop/"
    exit 1
}

Write-Host "[OK] Docker CLI encontrado: $($docker.Source)"

docker --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Docker CLI retornou erro."
    exit 1
}

docker compose version
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Docker Compose nao esta disponivel."
    exit 1
}

docker info | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Docker Desktop nao parece estar em execucao."
    Write-Host "Abra o Docker Desktop e tente novamente."
    exit 1
}

docker compose -f docker-compose.airflow.yml config | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] docker-compose.airflow.yml invalido."
    exit 1
}

Write-Host "[OK] Docker, Compose e arquivo Airflow prontos."
Write-Host "Para subir: docker compose -f docker-compose.airflow.yml up -d"
