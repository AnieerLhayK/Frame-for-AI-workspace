$ErrorActionPreference = "Stop"

$taskNames = @(
    "Hermes_Gateway",
    "Hermes_Gateway_Watchdog"
)

foreach ($taskName in $taskNames) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if (-not $task) {
        continue
    }

    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$cleanupShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "一次性移除 Hermes 自动启动.lnk"
if (Test-Path -LiteralPath $cleanupShortcut) {
    Remove-Item -LiteralPath $cleanupShortcut -Force
}
