$target = Join-Path $PSScriptRoot 'platform/remove_hermes_scheduled_tasks.ps1'
& $target @args
exit $LASTEXITCODE
