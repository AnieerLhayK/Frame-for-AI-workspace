$ErrorActionPreference = "Stop"

try {
    [Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
}
catch {
    # Encoding setup must never break a Claude Code hook.
}

function Get-StateDir {
    return (Join-Path $env:TEMP "claude-code-notifications")
}

function Write-HookLog([string]$Message) {
    try {
        $stateDir = Get-StateDir
        New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
        $timestamp = (Get-Date).ToUniversalTime().ToString("o")
        Add-Content -LiteralPath (Join-Path $stateDir "hook-events.log") -Encoding UTF8 -Value "$timestamp start $Message"
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

function Read-ExistingState([string]$StatePath) {
    if (-not (Test-Path -LiteralPath $StatePath)) {
        return $null
    }
    try {
        $stateText = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8
        return ConvertFrom-Json -InputObject $stateText -ErrorAction Stop
    }
    catch {
        Write-HookLog ("existing-state-invalid path={0} error={1}" -f $StatePath, $_.Exception.Message)
        return $null
    }
}

$hookInput = Get-HookInput
$payload = $hookInput.payload
$rawPayload = [string]$hookInput.raw
$sessionId = Get-SessionId $payload $rawPayload
$stateDir = Get-StateDir
$statePath = Join-Path $stateDir ("task-{0}.json" -f (ConvertTo-SafeFileName $sessionId))

New-Item -ItemType Directory -Path $stateDir -Force | Out-Null

$existingState = Read-ExistingState $statePath
if ($existingState -and $existingState.started_at) {
    try {
        $existingStart = [datetime]::Parse([string]$existingState.started_at).ToUniversalTime()
        $existingAge = ((Get-Date).ToUniversalTime() - $existingStart).TotalHours
        if ($existingAge -lt 24) {
            Write-HookLog ("state-preserved session={0} path={1} age_hours={2:n2}" -f $sessionId, $statePath, $existingAge)
            exit 0
        }
        Write-HookLog ("state-overwrite-stale session={0} path={1} age_hours={2:n2}" -f $sessionId, $statePath, $existingAge)
    }
    catch {
        Write-HookLog ("state-overwrite-unparseable-start session={0} path={1}" -f $sessionId, $statePath)
    }
}

$state = [ordered]@{
    session_id = $sessionId
    started_at = (Get-Date).ToUniversalTime().ToString("o")
    cwd = if ($payload -and $payload.cwd) { [string]$payload.cwd } else { Get-JsonStringField $rawPayload "cwd" }
    transcript_path = if ($payload -and $payload.transcript_path) { [string]$payload.transcript_path } else { Get-JsonStringField $rawPayload "transcript_path" }
}

$state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statePath -Encoding UTF8
Write-HookLog ("state-written session={0} path={1}" -f $sessionId, $statePath)
