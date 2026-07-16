$ErrorActionPreference = "Stop"

$hermesHome = "${DATA_ROOT}/hermes"
$pythonw = "${DATA_ROOT}/hermes\hermes-agent\venv\Scripts\pythonw.exe"
$logDir = Join-Path $hermesHome "logs"
$launchLog = Join-Path $logDir "manual-gateway-launch.log"

function Write-LaunchLog {
    param([string]$Message)
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -LiteralPath $launchLog -Value "$stamp $Message" -Encoding UTF8
}

function Get-HermesGatewayProcess {
    @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match "hermes_cli\.main\s+gateway\s+run"
        })
}

New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$running = Get-HermesGatewayProcess
if ($running.Count -gt 0) {
    Write-LaunchLog "already_running pid=$(($running.ProcessId -join ','))"
    exit 0
}

if (-not (Test-Path -LiteralPath $pythonw)) {
    Write-LaunchLog "start_failed missing_pythonw=$pythonw"
    throw "Hermes Python runtime not found: $pythonw"
}

$env:HERMES_HOME = $hermesHome
$env:PYTHONIOENCODING = "utf-8"
$env:HERMES_GATEWAY_DETACHED = "1"
$env:VIRTUAL_ENV = "${DATA_ROOT}/hermes\hermes-agent\venv"

Start-Process `
    -FilePath $pythonw `
    -ArgumentList @("-m", "hermes_cli.main", "gateway", "run") `
    -WorkingDirectory $hermesHome `
    -WindowStyle Hidden

Start-Sleep -Seconds 4
$started = Get-HermesGatewayProcess
if ($started.Count -gt 0) {
    Write-LaunchLog "started pid=$(($started.ProcessId -join ','))"
    exit 0
}

Write-LaunchLog "start_failed process_not_detected"
exit 1
