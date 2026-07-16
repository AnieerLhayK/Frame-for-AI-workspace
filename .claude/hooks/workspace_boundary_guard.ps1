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

function Require-ActiveTaskRecord([string]$ProjectRoot) {
    $recordId = [string]$env:WORKSPACE_TASK_RECORD
    if ([string]::IsNullOrWhiteSpace($recordId)) {
        Deny "Blocked: set WORKSPACE_TASK_RECORD to an active workspace record before mutating this workspace."
    }
    & python (Join-Path $ProjectRoot "scripts\task_records.py") require $recordId --operation workspace_write | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Deny "Blocked: WORKSPACE_TASK_RECORD is not active or is not registered for workspace writes."
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
    }
}

if ($toolName -eq "Bash") {
    $command = [string]$toolInput.command
    $mutating = "(?i)(?:^|[;&|]\s*)(?:mkdir|md|rmdir|rm|del|erase|copy|cp|move|mv|new-item|remove-item|move-item|copy-item|set-content|add-content|out-file)\b|\b(?:set-content|add-content|out-file|writealltext|appendalltext)\b"
    if ($command -match $mutating) {
        Require-ActiveTaskRecord $projectRoot
        foreach ($match in [regex]::Matches($command, "(?i)(?<path>[A-Z]:[\\/][^\s`"';&|]+)")) {
            $target = Resolve-GuardPath $match.Groups["path"].Value $cwd
            if (-not (Test-WorkspaceTarget $target $projectRoot $policy)) {
                Deny-WrongProject "Blocked: a wrapped shell command would mutate an external or unregistered path: $target" $projectRoot
            }
        }
        $operandMatch = [regex]::Match($command, "(?i)(?:mkdir|md|new-item)\s+(?:-[^\s]+\s+)*[`"']?([^`"';&|\s]+)")
        if ($operandMatch.Success) {
            $target = Resolve-GuardPath $operandMatch.Groups[1].Value $cwd
            if (-not (Test-WorkspaceTarget $target $projectRoot $policy)) {
                Deny "Blocked: command would create an unregistered workspace path."
            }
        }
    }
}

exit 0
