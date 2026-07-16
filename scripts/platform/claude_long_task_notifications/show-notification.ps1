param(
    [double]$Minutes = 0,
    [string]$Title = "Claude Code - Task done",
    [string]$Body = "",
    [int]$Seconds = 20
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Body)) {
    $Body = "Task completed in $Minutes minute(s)."
}

try {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $notify = New-Object System.Windows.Forms.NotifyIcon
    $notify.Icon = [System.Drawing.SystemIcons]::Information
    $notify.BalloonTipIcon = "Info"
    $notify.BalloonTipTitle = $Title
    $notify.BalloonTipText = $Body
    $notify.Visible = $true
    $notify.ShowBalloonTip([Math]::Max(1, $Seconds) * 1000)
    Start-Sleep -Seconds ([Math]::Max(1, $Seconds) + 2)
}
catch {
    exit 0
}
finally {
    if ($notify) {
        $notify.Dispose()
    }
}
