$ErrorActionPreference = "Stop"

$FlashMarker = "Flash sufficient"
$ProMarker = "Recommend Pro"
$AssessmentMarkers = @($FlashMarker, $ProMarker)
$ContinueMarkers = @(
    "continue",
    "continue anyway",
    "use current model",
    "stay on current model",
    "ignore the recommendation",
    "already switched"
)

function Get-ProjectRoot() {
    if ($env:CLAUDE_PROJECT_DIR) {
        return [string]$env:CLAUDE_PROJECT_DIR
    }
    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
}

function Test-ModelAdviceEnabled() {
    $configPath = Join-Path (Get-ProjectRoot) ".claude\model-routing-advice.json"
    if (-not (Test-Path -LiteralPath $configPath)) {
        return $true
    }
    try {
        $config = Get-Content -LiteralPath $configPath -Encoding utf8 -Raw | ConvertFrom-Json
    } catch {
        return $true
    }
    if ($config.PSObject.Properties.Match("enabled").Count -eq 0) {
        return $true
    }
    return ([bool]$config.enabled)
}

function New-TextFromCodepoints([int[]]$Codepoints) {
    return -join ($Codepoints | ForEach-Object { [char]$_ })
}

$ContinueMarkers += @(
    (New-TextFromCodepoints @(0x7ee7, 0x7eed)),
    (New-TextFromCodepoints @(0x7ee7, 0x7eed, 0x5f53, 0x524d, 0x6a21, 0x578b)),
    (New-TextFromCodepoints @(0x7ee7, 0x7eed, 0x4f7f, 0x7528, 0x5f53, 0x524d, 0x6a21, 0x578b)),
    (New-TextFromCodepoints @(0x4f7f, 0x7528, 0x5f53, 0x524d, 0x6a21, 0x578b)),
    (New-TextFromCodepoints @(0x4e0d, 0x7528, 0x5207, 0x6362)),
    (New-TextFromCodepoints @(0x4e0d, 0x8981, 0x5207, 0x6362)),
    (New-TextFromCodepoints @(0x5ffd, 0x7565, 0x63d0, 0x9192)),
    (New-TextFromCodepoints @(0x5ffd, 0x7565, 0x5efa, 0x8bae)),
    (New-TextFromCodepoints @(0x5df2, 0x5207, 0x6362)),
    (New-TextFromCodepoints @(0x5207, 0x6362, 0x597d, 0x4e86)),
    (New-TextFromCodepoints @(0x5269, 0x4f59, 0x4e0d, 0x591a))
)

$AssessmentContext = @(
    'Before responding to this user request, output the workspace model-tier assessment visibly.'
    ''
    'Rules:'
    '- This applies to every new user task/request in this Claude Code session.'
    '- Output the assessment before any tool call, file read, search, Todo, Plan Mode, or subagent/Agent delegation.'
    '- Do not downgrade high-risk planning to Flash just because the user asks not to modify files first.'
    '- Guard/permission design, Git conflict handling, security/stability work, and cross-system diagnosis should recommend Pro even when the first step is read-only.'
    '- If the prompt mentions workspace guard, write permissions, or permission differences across Claude Code, Codex, OpenCode, and Hermes, classify it as Recommend Pro.'
    '- If the prompt mentions workspace health failures, workflow check out-of-scope, stale reports, or multi-cause diagnosis, classify it as Recommend Pro.'
    '- If the prompt mentions Git merge conflicts, conflict resolution, or merging long-lived branches, classify it as Recommend Pro.'
    '- Example: a long-lived branch merged into main with conflicts in task_ledger.md, todo.md, or prompt_registry.yaml is Recommend Pro, even if the first action is git status/read-only inspection.'
    '- Use the exact low-risk or high-risk First Response Format from shared/claude/policies/model-routing-policy.md.'
    '- Low-risk responses must contain: Flash sufficient.'
    '- High-risk responses must contain: Recommend Pro and then pause for the user to switch model or explicitly continue with the current model.'
    '- Do not start tools after Recommend Pro unless the user says to continue/current model/ignore the recommendation/already switched.'
    '- A model recommendation is advisory only and does not change permissions.'
) -join [Environment]::NewLine

function Get-MessageRole($Entry) {
    if ($Entry.message -and $Entry.message.role) {
        return [string]$Entry.message.role
    }
    if ($Entry.role) {
        return [string]$Entry.role
    }
    return ""
}

function Get-ContentText($Content) {
    if ($null -eq $Content) {
        return ""
    }
    if ($Content -is [string]) {
        return $Content
    }
    $parts = @()
    foreach ($block in @($Content)) {
        if ($block.text) {
            $parts += [string]$block.text
        }
        if ($block.content) {
            $parts += Get-ContentText $block.content
        }
    }
    return ($parts -join [Environment]::NewLine)
}

function Get-AssessmentKind($Content) {
    $text = Get-ContentText $Content
    if ($text.Contains($ProMarker)) {
        return "pro"
    }
    if ($text.Contains($FlashMarker)) {
        return "flash"
    }
    return ""
}

function Test-UserAllowsCurrentModel([string]$Text) {
    foreach ($marker in $ContinueMarkers) {
        if ($Text.IndexOf($marker, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            return $true
        }
    }
    return $false
}

function Get-ModelRoutingStateAfterLastUser([string]$TranscriptPath) {
    $state = @{
        assessment = ""
        user_allows_current_model = $false
    }
    if (-not $TranscriptPath -or -not (Test-Path -LiteralPath $TranscriptPath)) {
        return $state
    }
    $lines = Get-Content -LiteralPath $TranscriptPath -Encoding utf8
    for ($index = $lines.Count - 1; $index -ge 0; $index--) {
        $line = [string]$lines[$index]
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        try {
            $entry = $line | ConvertFrom-Json
        } catch {
            continue
        }
        $role = Get-MessageRole $entry
        if ($role -eq "user") {
            $message = if ($entry.message) { $entry.message } else { $entry }
            $state.user_allows_current_model = Test-UserAllowsCurrentModel (Get-ContentText $message.content)
            return $state
        }
        if ($role -eq "assistant") {
            $message = if ($entry.message) { $entry.message } else { $entry }
            $kind = Get-AssessmentKind $message.content
            if ($kind) {
                $state.assessment = $kind
            }
        }
    }
    return $state
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
    } catch {
        return [string]$match.Groups[1].Value
    }
}

function Get-HookPayloadFromText([string]$PayloadText) {
    try {
        return ConvertFrom-Json -InputObject $PayloadText -ErrorAction Stop
    } catch {
        $eventName = Get-JsonStringField $PayloadText "hook_event_name"
        if ([string]::IsNullOrWhiteSpace($eventName)) {
            return $null
        }
        return [pscustomobject]@{
            hook_event_name = $eventName
            transcript_path = Get-JsonStringField $PayloadText "transcript_path"
            tool_name = Get-JsonStringField $PayloadText "tool_name"
        }
    }
}

$payloadText = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($payloadText)) {
    exit 0
}

$payload = Get-HookPayloadFromText $payloadText
if ($null -eq $payload) {
    exit 0
}
$eventName = [string]$payload.hook_event_name

if (-not (Test-ModelAdviceEnabled)) {
    exit 0
}

if ($eventName -eq "UserPromptSubmit") {
    @{
        hookSpecificOutput = @{
            hookEventName = "UserPromptSubmit"
            additionalContext = $AssessmentContext
        }
    } | ConvertTo-Json -Depth 5 -Compress
    exit 0
}

if ($eventName -eq "PreToolUse") {
    $transcriptPath = [string]$payload.transcript_path
    $routingState = Get-ModelRoutingStateAfterLastUser $transcriptPath
    if ($routingState.user_allows_current_model) {
        exit 0
    }
    if ($routingState.assessment -eq "flash") {
        exit 0
    }
    $toolName = [string]$payload.tool_name
    if ($routingState.assessment -eq "pro") {
        [Console]::Error.WriteLine(
            "Blocked: Recommend Pro was issued. Pause and ask the user to switch model, say already switched, or explicitly continue with the current model before using tool '$toolName'."
        )
        exit 2
    }
    [Console]::Error.WriteLine(
        "Blocked: output a visible model-tier assessment before using tool '$toolName'. Include either 'Flash sufficient' or 'Recommend Pro'."
    )
    exit 2
}

exit 0
