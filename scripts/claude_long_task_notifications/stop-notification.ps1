$target = Join-Path $PSScriptRoot '..\platform\claude_long_task_notifications\stop-notification.ps1'
& $target @args
exit $LASTEXITCODE
