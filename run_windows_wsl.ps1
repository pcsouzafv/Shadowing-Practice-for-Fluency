[CmdletBinding()]
param(
    [string]$Distro
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$installScript = Join-Path $scriptDir "install_windows_wsl.ps1"

if (-not (Test-Path $installScript)) {
    throw "Arquivo install_windows_wsl.ps1 nao encontrado em $scriptDir"
}

& powershell.exe -ExecutionPolicy Bypass -File $installScript -Distro $Distro -StartApp
if ($LASTEXITCODE -ne 0) {
    throw "Nao foi possivel iniciar a aplicacao via WSL."
}
