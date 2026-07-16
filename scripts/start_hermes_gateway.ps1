$target = Join-Path $PSScriptRoot 'platform/start_hermes_gateway.ps1'
& $target @args
exit $LASTEXITCODE
