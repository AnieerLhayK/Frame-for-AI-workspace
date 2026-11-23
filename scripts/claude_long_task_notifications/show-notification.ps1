$target = Join-Path $PSScriptRoot '..\platform\claude_long_task_notifications\show-notification.ps1'
& $target @args
exit $LASTEXITCODE
