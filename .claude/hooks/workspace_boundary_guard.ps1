$ErrorActionPreference = "Stop"

function Deny([string]$Reason) {
    [Console]::Error.WriteLine($Reason)
    exit 2
}

function Deny-WrongProject([string]$Reason, [string]$ProjectRoot) {
    $guidance = @(
        $Reason
        "This Claude session is rooted at: $ProjectRoot"
        "Start a new Claude session from the target Git root with: cd <target-root>; claude"
        "Or use: claude-project <alias>"
        "Do not bypass this guard with PowerShell, Python, shell redirection, or whole-file string replacement."
    ) -join [Environment]::NewLine
    Deny $guidance
}

function Resolve-GuardPath([string]$RawPath, [string]$Cwd) {
    if ([System.IO.Path]::IsPathRooted($RawPath)) {
        return [System.IO.Path]::GetFullPath($RawPath)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $Cwd $RawPath))
}

function Test-Within([string]$Path, [string]$Root) {
    $fullPath = [System.IO.Path]::GetFullPath($Path).TrimEnd("\", "/")
    $fullRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd("\", "/")
    return $fullPath.Equals($fullRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
        $fullPath.StartsWith($fullRoot + "\", [System.StringComparison]::OrdinalIgnoreCase)
}

function Test-WorkspaceTarget([string]$Path, [string]$Root, $Policy) {
    if (-not (Test-Within $Path $Root)) {
        return $false
    }
    $fullPath = [System.IO.Path]::GetFullPath($Path).TrimEnd("\", "/")
    $fullRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd("\", "/")
    $relative = $fullPath.Substring($fullRoot.Length).TrimStart("\", "/")
    if ($relative -eq ".") {
        return $true
    }
    $parts = $relative -split "[\\/]"
    if ($parts.Count -eq 1) {
        return $Policy.allowed_root_files -contains $parts[0]
    }
    return $Policy.allowed_top_level -contains $parts[0]
}

$payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
$projectRoot = [System.IO.Path]::GetFullPath($env:CLAUDE_PROJECT_DIR)
$policyPath = Join-Path $projectRoot ".claude\project-boundary.json"
$policy = Get-Content -LiteralPath $policyPath -Raw -Encoding utf8 | ConvertFrom-Json
$cwd = [System.IO.Path]::GetFullPath([string]$payload.cwd)
$toolName = [string]$payload.tool_name
$toolInput = $payload.tool_input

if (-not (Test-Within $cwd $projectRoot)) {
    Deny-WrongProject "Blocked: Claude cwd is outside the governed workspace root: $cwd" $projectRoot
}

function Resolve-SessionTask([string]$ShellCommand = "") {
    $arguments = @("-m", "scripts.workspace.governance.claude_runtime")
    if ($payload.session_id) { $arguments += @("--session-id", [string]$payload.session_id) }
    if ($ShellCommand) {
        $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($ShellCommand))
        $arguments += @("--shell-command-base64", $encoded)
    }
    Push-Location $projectRoot
    try {
        $resolved = & python @arguments
        if ($LASTEXITCODE -ne 0) {
            Deny "Blocked: $resolved. Claude session: $($payload.session_id)"
        }
        $env:WORKSPACE_TASK_RECORD = [string]$resolved
    } finally { Pop-Location }
}

function Require-ActiveTaskRecord([string]$ProjectRoot) {
    Resolve-SessionTask
    $recordId = [string]$env:WORKSPACE_TASK_RECORD
    Push-Location $ProjectRoot
    try {
        & python -m scripts.workspace.task_records require $recordId --operation workspace_write --agent claude | Out-Null
    } finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) {
        Deny "Blocked: WORKSPACE_TASK_RECORD is not active or is not registered for workspace writes."
    }
}

function Require-TaskTarget([string]$Target) {
    if ($Target -match '(?i)[\\/]PROJECT_CONTEXT[\\/]tasks[\\/]records[\\/].*[\\/]TASK-[^\\/]+\.json$') {
        Deny "Blocked: update TASK records through workspace records commands; native edits cannot author approval fields."
    }
    Push-Location $projectRoot
    try {
        & python -m scripts.workspace.agent_governance check --agent claude --operation write --path $Target --record-id $env:WORKSPACE_TASK_RECORD
        if ($LASTEXITCODE -ne 0) {
            Deny "Blocked: Claude lacks task-scoped authority for this target. Ask Codex to perform governance changes."
        }
    } finally {
        Pop-Location
    }
}

if ($toolName -in @("Write", "Edit", "MultiEdit", "NotebookEdit")) {
    Require-ActiveTaskRecord $projectRoot
    $rawPath = if ($toolInput.file_path) { $toolInput.file_path } else { $toolInput.notebook_path }
    if ($rawPath) {
        $target = Resolve-GuardPath ([string]$rawPath) $cwd
        if (-not (Test-WorkspaceTarget $target $projectRoot $policy)) {
            Deny-WrongProject "Blocked: target is outside an allowed workspace layer: $target" $projectRoot
        }
        Require-TaskTarget $target
    }
}

if ($toolName -eq "Bash") {
    $command = [string]$toolInput.command
    if ($command -match '(?i)--(?:agent|owner-agent|governance-approver)\s+["'']?codex\b') {
        Deny "Blocked: Claude cannot act as Codex or issue a Codex approval."
    }
    # Shell execution can hide writes in interpreters. Require an owned TASK
    # except for simple read-only commands and bootstrapping that same identity.
    $simpleRead = $command -notmatch '[;&|<>`\r\n]' -and $command -match '^\s*(?:git\s+(?:status|diff|log|show|rev-parse|ls-files)\b|rg\b|pwd\s*$|Get-Content\b|Get-Item\b|Get-Location\s*$|workspace\s+(?:task\s+(?:list|resolve)|agent\s+(?:list|show|status|check)|records\s+(?:show|validate|summary)|plans\s+(?:show|list|validate))\b)'
    $startOwnTask = $command -notmatch '[;&|<>`\r\n]' -and $command -match '^\s*workspace\s+records\s+start\b' -and $command -match '--owner-agent\s+claude\b' -and $command -match '--owner-session\s+\S+'
    if (-not $simpleRead -and -not $startOwnTask) {
        Resolve-SessionTask $command
    }
    if ($command -match '(?i)\bgit(?:\s+-C\s+(?:"[^"]+"|''[^'']+''|\S+))?\s+(?:merge|push)\b') {
        Push-Location $projectRoot
        try {
            & python -m scripts.workspace.merge_safety main --head dev --agent claude --record-id $env:WORKSPACE_TASK_RECORD --for-push | Out-Null
            if ($LASTEXITCODE -ne 0) { Deny "Blocked: delivery preflight failed; obtain current review and governance approval when required." }
        } finally { Pop-Location }
    }
    $mutating = "(?i)(?:^|[;&|]\s*)(?:mkdir|md|rmdir|rm|del|erase|copy|cp|move|mv|new-item|remove-item|move-item|copy-item|set-content|add-content|out-file)\b|\b(?:set-content|add-content|out-file|writealltext|appendalltext)\b"
    if ($command -match $mutating) {
        Require-ActiveTaskRecord $projectRoot
        foreach ($match in [regex]::Matches($command, "(?i)(?<path>[A-Z]:[\\/][^\s`"';&|]+)")) {
            $target = Resolve-GuardPath $match.Groups["path"].Value $cwd
            if (-not (Test-WorkspaceTarget $target $projectRoot $policy)) {
                Deny-WrongProject "Blocked: a wrapped shell command would mutate an external or unregistered path: $target" $projectRoot
            }
            Require-TaskTarget $target
        }
        $operandMatch = [regex]::Match($command, "(?i)(?:mkdir|md|new-item)\s+(?:-[^\s]+\s+)*[`"']?([^`"';&|\s]+)")
        if ($operandMatch.Success) {
            $target = Resolve-GuardPath $operandMatch.Groups[1].Value $cwd
            if (-not (Test-WorkspaceTarget $target $projectRoot $policy)) {
                Deny "Blocked: command would create an unregistered workspace path."
            }
            Require-TaskTarget $target
        }
    }
}

exit 0
