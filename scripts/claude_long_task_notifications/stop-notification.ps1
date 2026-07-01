param(
    [double]$ToastThresholdMinutes = 5,
    [double]$HermesThresholdMinutes = 10,
    [string]$Target = "qqbot"
)

$ErrorActionPreference = "Stop"

function Get-StateDir {
    return (Join-Path $env:TEMP "claude-code-notifications")
}

function Write-HookLog([string]$Message) {
    try {
        $stateDir = Get-StateDir
        New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
        $timestamp = (Get-Date).ToUniversalTime().ToString("o")
        Add-Content -LiteralPath (Join-Path $stateDir "hook-events.log") -Encoding UTF8 -Value "$timestamp stop $Message"
    }
    catch {
        # Logging must never break a Claude Code hook.
    }
}

function Get-JsonStringField([string]$Raw, [string]$Name) {
    if ([string]::IsNullOrWhiteSpace($Raw)) {
        return ""
    }
    $pattern = '"' + [regex]::Escape($Name) + '"\s*:\s*"((?:\\.|[^"\\])*)"'
    $match = [regex]::Match($Raw, $pattern)
    if (-not $match.Success) {
        return ""
    }
    try {
        return [regex]::Unescape($match.Groups[1].Value)
    }
    catch {
        return [string]$match.Groups[1].Value
    }
}

function Get-HookInput {
    $raw = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return [pscustomobject]@{ payload = $null; raw = "" }
    }
    try {
        return [pscustomobject]@{
            payload = ConvertFrom-Json -InputObject $raw -ErrorAction Stop
            raw = $raw
        }
    }
    catch {
        Write-HookLog ("payload-json-failed length={0} error={1}" -f $raw.Length, $_.Exception.Message)
        return [pscustomobject]@{ payload = $null; raw = $raw }
    }
}

function Get-SessionId($Payload, [string]$Raw) {
    if ($Payload -and $Payload.session_id) {
        return [string]$Payload.session_id
    }
    if ($env:CLAUDE_CODE_SESSION_ID) {
        return [string]$env:CLAUDE_CODE_SESSION_ID
    }
    $rawSessionId = Get-JsonStringField $Raw "session_id"
    if (-not [string]::IsNullOrWhiteSpace($rawSessionId)) {
        return $rawSessionId
    }
    return "default"
}

function ConvertTo-SafeFileName([string]$Value) {
    $safe = $Value -replace '[^A-Za-z0-9_.-]', '_'
    if ([string]::IsNullOrWhiteSpace($safe)) {
        return "default"
    }
    return $safe
}

function Get-CollectionCount($Value) {
    if ($null -eq $Value) {
        return 0
    }
    if ($Value -is [System.Array]) {
        return $Value.Count
    }
    return @($Value).Count
}

function Read-TaskState([string]$StatePath) {
    if (Test-Path -LiteralPath $StatePath) {
        $stateText = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8
        return ConvertFrom-Json -InputObject $stateText -ErrorAction Stop
    }

    $legacyPath = Join-Path $env:TEMP "claude-code-start-time.txt"
    if (Test-Path -LiteralPath $legacyPath) {
        $startedAt = (Get-Content -LiteralPath $legacyPath -Raw -Encoding UTF8).Trim()
        return [pscustomobject]@{
            session_id = "legacy"
            started_at = $startedAt
            cwd = ""
            transcript_path = ""
            legacy_path = $legacyPath
        }
    }

    return $null
}

$hookInput = Get-HookInput
$payload = $hookInput.payload
$rawPayload = [string]$hookInput.raw

# Claude Code v2.1.145+ includes these fields. If work is still in flight,
# keep the state file so a later Stop event can notify on true completion.
if ($payload) {
    $backgroundCount = Get-CollectionCount $payload.background_tasks
    $cronCount = Get-CollectionCount $payload.session_crons
    Write-HookLog ("payload session={0} background_tasks={1} session_crons={2}" -f $payload.session_id, $backgroundCount, $cronCount)
    if ($backgroundCount -gt 0) {
        Write-HookLog "skip background-tasks-present"
        exit 0
    }
}
else {
    Write-HookLog "payload unavailable; using fallback session lookup"
}

$sessionId = Get-SessionId $payload $rawPayload
$stateDir = Get-StateDir
$statePath = Join-Path $stateDir ("task-{0}.json" -f (ConvertTo-SafeFileName $sessionId))
$statePathToRemove = $statePath
$state = $null

try {
    $state = Read-TaskState $statePath
    if ($null -eq $state -and $sessionId -ne "default") {
        $defaultStatePath = Join-Path $stateDir "task-default.json"
        $state = Read-TaskState $defaultStatePath
        if ($state) {
            $statePathToRemove = $defaultStatePath
            Write-HookLog ("using-default-state requested_session={0}" -f $sessionId)
        }
    }
    if ($null -eq $state -or -not $state.started_at) {
        Write-HookLog ("skip missing-state session={0} path={1}" -f $sessionId, $statePath)
        exit 0
    }

    $startTime = [datetime]::Parse([string]$state.started_at).ToUniversalTime()
    $duration = (Get-Date).ToUniversalTime() - $startTime
    $minutes = [math]::Round($duration.TotalMinutes, 1)
    Write-HookLog ("duration session={0} minutes={1}" -f $sessionId, $minutes)

    if ($duration.TotalMinutes -lt $ToastThresholdMinutes) {
        Write-HookLog ("skip below-toast-threshold threshold={0}" -f $ToastThresholdMinutes)
        exit 0
    }

    $message = "Claude Code task completed in $minutes minute(s)."
    if ($state.cwd) {
        $message = "$message`nProject: $($state.cwd)"
    }

    $notifierScript = Join-Path $PSScriptRoot "show-notification.ps1"
    if (Test-Path -LiteralPath $notifierScript) {
        try {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $notifierScript -Minutes $minutes -Body $message | Out-Null
            Write-HookLog "toast-sent"
        }
        catch {
            Write-HookLog ("toast-failed error={0}" -f $_.Exception.Message)
            # Desktop notification failure should not block Claude Code.
        }
    }

    if ($duration.TotalMinutes -ge $HermesThresholdMinutes) {
        $nodeScript = Join-Path $PSScriptRoot "hermes-mcp-client.js"
        $nodePath = (Get-Command "node.exe" -ErrorAction SilentlyContinue).Source
        if ($nodePath -and (Test-Path -LiteralPath $nodeScript)) {
            try {
                & $nodePath $nodeScript --minutes $minutes --target $Target --message $message | Out-Null
                Write-HookLog ("hermes-finished target={0} exit={1}" -f $Target, $LASTEXITCODE)
            }
            catch {
                Write-HookLog ("hermes-failed target={0} error={1}" -f $Target, $_.Exception.Message)
                # Hermes notification failure is logged by the Node client.
            }
        }
        else {
            Write-HookLog ("hermes-skip node={0} script_exists={1}" -f $nodePath, (Test-Path -LiteralPath $nodeScript))
        }
    }
    else {
        Write-HookLog ("skip below-hermes-threshold threshold={0}" -f $HermesThresholdMinutes)
    }
}
catch {
    Write-HookLog ("fatal error={0}" -f $_.Exception.Message)
    # Hook failures should never interrupt the Claude Code turn.
}
finally {
    if (Test-Path -LiteralPath $statePathToRemove) {
        Remove-Item -LiteralPath $statePathToRemove -Force -ErrorAction SilentlyContinue
    }
    if ($state -and $state.legacy_path -and (Test-Path -LiteralPath $state.legacy_path)) {
        Remove-Item -LiteralPath $state.legacy_path -Force -ErrorAction SilentlyContinue
    }
}
