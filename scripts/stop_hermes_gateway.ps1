$target = Join-Path $PSScriptRoot 'platform/stop_hermes_gateway.ps1'
& $target @args
exit $LASTEXITCODE
