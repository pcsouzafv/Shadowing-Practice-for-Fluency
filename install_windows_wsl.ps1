[CmdletBinding()]
param(
    [string]$Distro,
    [switch]$StartApp
)

$ErrorActionPreference = "Stop"

function Get-WslDistributions {
    $raw = & wsl.exe -l -q 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Nao foi possivel listar as distribuicoes do WSL. Verifique se o WSL esta instalado."
    }

    return @(
        $raw |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ -and $_ -notmatch '^docker-desktop' }
    )
}

function Resolve-WslDistribution {
    param([string]$PreferredDistro)

    $distros = Get-WslDistributions
    if (-not $distros -or $distros.Count -eq 0) {
        throw "Nenhuma distribuicao Linux foi encontrada no WSL. Rode 'wsl --install -d Ubuntu' em um terminal com permissao de administrador."
    }

    if ($PreferredDistro) {
        if ($distros -contains $PreferredDistro) {
            return $PreferredDistro
        }

        $available = ($distros -join ", ")
        throw "A distribuicao '$PreferredDistro' nao foi encontrada. Disponiveis: $available"
    }

    $ubuntu = $distros | Where-Object { $_ -match '^Ubuntu' } | Select-Object -First 1
    if ($ubuntu) {
        return $ubuntu
    }

    return $distros[0]
}

function Get-ProjectWslPath {
    param([string]$TargetDistro)

    $projectWindowsPath = (Resolve-Path $PSScriptRoot).Path
    $projectWslPath = (& wsl.exe -d $TargetDistro wslpath -a $projectWindowsPath).Trim()

    if ($LASTEXITCODE -ne 0 -or -not $projectWslPath) {
        throw "Nao foi possivel converter o caminho do projeto para o formato do WSL."
    }

    return $projectWslPath
}

function Invoke-WslProjectCommand {
    param(
        [string]$TargetDistro,
        [string]$ProjectWslPath,
        [string]$Command
    )

    & wsl.exe -d $TargetDistro bash -lc $Command bash $ProjectWslPath
    if ($LASTEXITCODE -ne 0) {
        throw "O comando dentro do WSL falhou."
    }
}

if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw "WSL nao encontrado. Instale com 'wsl --install -d Ubuntu' em um terminal com permissao de administrador."
}

$selectedDistro = Resolve-WslDistribution -PreferredDistro $Distro
$projectWslPath = Get-ProjectWslPath -TargetDistro $selectedDistro

Write-Host "Usando WSL distro: $selectedDistro"
Write-Host "Projeto no WSL: $projectWslPath"
Write-Host "Instalando dependencias no ambiente Linux..."

Invoke-WslProjectCommand `
    -TargetDistro $selectedDistro `
    -ProjectWslPath $projectWslPath `
    -Command 'cd "$1" && bash ./scripts/install_wsl.sh'

if ($StartApp) {
    Write-Host "Iniciando a aplicacao pelo WSL..."
    Invoke-WslProjectCommand `
        -TargetDistro $selectedDistro `
        -ProjectWslPath $projectWslPath `
        -Command 'cd "$1" && exec bash ./run.sh'
}
