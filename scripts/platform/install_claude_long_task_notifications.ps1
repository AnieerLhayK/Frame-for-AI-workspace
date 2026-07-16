param(
    [switch]$Apply,
    [string]$ClaudeHome = (Join-Path $env:USERPROFILE ".claude"),
    [string]$Target = "qqbot"
)

$ErrorActionPreference = "Stop"

$sourceDir = Join-Path $PSScriptRoot "claude_long_task_notifications"
$settingsPath = Join-Path $ClaudeHome "settings.json"
$hooksDir = Join-Path $ClaudeHome "hooks"

$scripts = @(
    "start-notification-timer.ps1",
    "stop-notification.ps1",
    "show-notification.ps1",
    "hermes-mcp-client.js"
)

function Get-NormalizedTextOrEmpty([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }
    $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    return (($text -replace "`r`n", "`n") -replace "`r", "`n")
}

function Test-TextFileCurrent([string]$SourcePath, [string]$TargetPath) {
    $sourceText = Get-NormalizedTextOrEmpty $SourcePath
    $targetText = Get-NormalizedTextOrEmpty $TargetPath
    return ($sourceText -and $sourceText -eq $targetText)
}

function Get-InstallStatus([string]$TargetName) {
    $scriptStatuses = @()
    foreach ($script in $scripts) {
        $source = Join-Path $sourceDir $script
        $targetPath = Join-Path $hooksDir $script
        $scriptStatuses += [pscustomobject]@{
            script = $script
            installed = (Test-Path -LiteralPath $targetPath)
            current = Test-TextFileCurrent $source $targetPath
        }
    }

    $settingsCurrent = $false
    if (Test-Path -LiteralPath $settingsPath) {
        try {
            $settings = Get-Content -LiteralPath $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $commands = @()
            foreach ($eventName in @("UserPromptSubmit", "Stop")) {
                if ($settings.hooks -and ($settings.hooks.PSObject.Properties.Name -contains $eventName)) {
                    foreach ($entry in @($settings.hooks.$eventName)) {
                        foreach ($hook in @($entry.hooks)) {
                            if ($hook.command) {
                                $commands += [string]$hook.command
                            }
                        }
                    }
                }
            }
            $joinedCommands = $commands -join "`n"
            $settingsCurrent = (
                $joinedCommands -match [regex]::Escape("start-notification-timer.ps1") -and
                $joinedCommands -match [regex]::Escape("stop-notification.ps1") -and
                $joinedCommands -match ("(?i)-Target\s+[`"']?" + [regex]::Escape($TargetName) + "[`"']?")
            )
        }
        catch {
            $settingsCurrent = $false
        }
    }

    return [pscustomobject]@{
        scripts_current = -not ($scriptStatuses | Where-Object { -not $_.current })
        settings_current = $settingsCurrent
        scripts = $scriptStatuses
    }
}

function Write-InstallStatus($Status) {
    Write-Host "Current install status:"
    Write-Host ("  Scripts current: {0}" -f $Status.scripts_current)
    Write-Host ("  Settings current: {0}" -f $Status.settings_current)
    foreach ($script in $Status.scripts) {
        Write-Host ("  - {0}: installed={1}, current={2}" -f $script.script, $script.installed, $script.current)
    }
}

function New-HookEntry([string]$Command, [int]$TimeoutSeconds) {
    [pscustomobject]@{
        matcher = ""
        hooks = @(
            [pscustomobject]@{
                type = "command"
                command = $Command
                timeout = $TimeoutSeconds
            }
        )
    }
}

function Remove-NotificationHookEntries($Entries, [string[]]$ScriptNames) {
    $kept = @()
    foreach ($entry in @($Entries)) {
        $commands = @()
        if ($entry.hooks) {
            foreach ($hook in @($entry.hooks)) {
                if ($hook.command) {
                    $commands += [string]$hook.command
                }
            }
        }
        $isNotificationEntry = $false
        foreach ($scriptName in $ScriptNames) {
            if (($commands -join "`n") -match [regex]::Escape($scriptName)) {
                $isNotificationEntry = $true
                break
            }
        }
        if (-not $isNotificationEntry) {
            $kept += $entry
        }
    }
    return $kept
}

function Set-HookEvent($Settings, [string]$EventName, [string]$Command, [string[]]$ScriptNames, [int]$TimeoutSeconds) {
    if (-not ($Settings.PSObject.Properties.Name -contains "hooks") -or $null -eq $Settings.hooks) {
        $Settings | Add-Member -MemberType NoteProperty -Name hooks -Value ([pscustomobject]@{}) -Force
    }

    $existing = @()
    if ($Settings.hooks.PSObject.Properties.Name -contains $EventName) {
        $existing = @($Settings.hooks.$EventName)
    }

    $updated = @(Remove-NotificationHookEntries $existing $ScriptNames)
    $updated += New-HookEntry $Command $TimeoutSeconds
    $Settings.hooks | Add-Member -MemberType NoteProperty -Name $EventName -Value $updated -Force
}

if (-not (Test-Path -LiteralPath $sourceDir)) {
    throw "Template directory not found: $sourceDir"
}

if (-not $Apply) {
    Write-Host "Dry run only. Re-run with -Apply to install Claude Code long-task notifications."
    Write-Host "Claude home: $ClaudeHome"
    Write-Host "Settings file: $settingsPath"
    Write-Host "Hook target directory: $hooksDir"
    Write-Host "Hermes message target: $Target"
    Write-InstallStatus (Get-InstallStatus $Target)
    foreach ($script in $scripts) {
        Write-Host "Would copy: $script"
    }
    exit 0
}

New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null

foreach ($script in $scripts) {
    Copy-Item -LiteralPath (Join-Path $sourceDir $script) -Destination (Join-Path $hooksDir $script) -Force
}

if (Test-Path -LiteralPath $settingsPath) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    Copy-Item -LiteralPath $settingsPath -Destination "$settingsPath.$timestamp.bak" -Force
    $settings = Get-Content -LiteralPath $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
}
else {
    New-Item -ItemType Directory -Path $ClaudeHome -Force | Out-Null
    $settings = [pscustomobject]@{}
}

$startScript = Join-Path $hooksDir "start-notification-timer.ps1"
$stopScript = Join-Path $hooksDir "stop-notification.ps1"
$startCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$startScript`""
$stopCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$stopScript`" -Target `"$Target`""

Set-HookEvent $settings "UserPromptSubmit" $startCommand @("start-notification-timer.ps1") 10
Set-HookEvent $settings "Stop" $stopCommand @("stop-notification.ps1") 120

$settings | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $settingsPath -Encoding UTF8

Write-Host "Installed Claude Code long-task notification hooks."
Write-Host "Updated: $settingsPath"
Write-Host "Copied scripts to: $hooksDir"
Write-InstallStatus (Get-InstallStatus $Target)
