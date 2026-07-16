$target = Join-Path $PSScriptRoot 'platform/install_claude_long_task_notifications.ps1'
& $target @args
exit $LASTEXITCODE
