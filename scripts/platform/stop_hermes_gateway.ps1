$ErrorActionPreference = "Stop"

$hermesHome = "${DATA_ROOT}/hermes"
$hermesExe = "${DATA_ROOT}/hermes\hermes-agent\venv\Scripts\hermes.exe"
$logDir = Join-Path $hermesHome "logs"
$launchLog = Join-Path $logDir "manual-gateway-launch.log"

New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$env:HERMES_HOME = $hermesHome
$env:PYTHONIOENCODING = "utf-8"

& $hermesExe gateway stop *> $null
$exitCode = $LASTEXITCODE

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -LiteralPath $launchLog -Value "$stamp stop_requested exit_code=$exitCode" -Encoding UTF8
exit $exitCode
