$target = Join-Path $PSScriptRoot '..\platform\claude_long_task_notifications\start-notification-timer.ps1'
& $target @args
exit $LASTEXITCODE
