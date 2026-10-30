[CmdletBinding()]
param([switch]$CheckOnly)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$source = '${DATA_ROOT}/codex\cache\tiktoken'
$target = '${DATA_ROOT}\cache\tiktoken'
$stage = '${DATA_ROOT}/codex\cache\staging\tiktoken-relocation-20261030-001'
$basePython = 'D:\CODER\python\anaconda\envs\ai\python.exe'
$probe = Join-Path $PSScriptRoot 'verify_cache.py'
$planPath = Join-Path $PSScriptRoot 'plan.json'
$receipt = Join-Path $PSScriptRoot 'apply-result.json'
$cacheName = 'fb374d419588a4632f3f557e76b4b70aebbca790'
$expectedHash = '446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d'
$oldUser = [Environment]::GetEnvironmentVariable('TIKTOKEN_CACHE_DIR', 'User')
$oldProcess = [Environment]::GetEnvironmentVariable('TIKTOKEN_CACHE_DIR', 'Process')
$settingChanged = $false
$result = [ordered]@{
    schema_version = '1.0'; report_type = 'apply'; report_id = 'tiktoken-apply-20261030-001'
    source_report_id = 'tiktoken-plan-20261030-001'; mode = 'apply'; status = 'NOT_RUN'
    operator = 'user'; target_root = $target; checks = @(); cleanup = 'not_executed'
    warnings = @('Previously running applications require restart to inherit the new setting.')
    errors = @()
}

function Invoke-CheckedNative {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Native command failed: $([IO.Path]::GetFileName($Program))" }
}

function Invoke-JsonProbe {
    param([string]$Python, [string]$Mode)
    $payload = & $Python -X utf8 $probe $Mode
    if ($LASTEXITCODE -ne 0) { throw "Verification failed: $Mode" }
    $value = ($payload -join "`n") | ConvertFrom-Json
    if ($value.status -ne 'PASS') { throw "Verification failed: $Mode" }
    return $value
}

function Assert-PlainDirectory {
    param([string]$Path)
    $item = Get-Item -LiteralPath $Path -Force
    if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Expected a real directory: $Path"
    }
}

try {
    $plan = Get-Content -LiteralPath $planPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($plan.report_id -ne 'tiktoken-plan-20261030-001' -or
        @($plan.actions | Where-Object { -not $_.approved }).Count -gt 0 -or
        @($plan.actions).Count -ne 3) { throw 'Exact plan approval is missing' }
    if (-not (Test-Path -LiteralPath $basePython -PathType Leaf)) { throw 'Verification Python is missing' }
    Assert-PlainDirectory $source
    Assert-PlainDirectory '${DATA_ROOT}\cache'
    Assert-PlainDirectory '${DATA_ROOT}/codex\cache\staging'
    if ($oldUser -ne $source) { throw 'User setting changed since audit; stop for review' }
    if ((Test-Path -LiteralPath $target) -or (Test-Path -LiteralPath $stage)) {
        throw 'Target or staging already exists; do not merge or overwrite'
    }
    $result.checks += Invoke-JsonProbe $basePython 'snapshot'
    $actualHash = (Get-FileHash -LiteralPath (Join-Path $source $cacheName) -Algorithm SHA256).Hash
    if ($actualHash -ine $expectedHash) { throw 'Source word table hash does not match upstream' }
    if ($CheckOnly) {
        Write-Output 'Preflight PASS. No filesystem or environment changes performed.'
        return
    }

    Write-Output '[1/5] Creating an isolated verification environment...'
    New-Item -ItemType Directory -Path $stage | Out-Null
    $venv = Join-Path $stage 'venv'
    Invoke-CheckedNative $basePython @('-m', 'venv', $venv)
    $python = Join-Path $venv 'Scripts\python.exe'
    Invoke-CheckedNative $python @('-m', 'pip', '--isolated', 'install', '--disable-pip-version-check', '--no-input', '--no-cache-dir', '--index-url', 'https://pypi.org/simple', 'tiktoken==0.12.0')

    Write-Output '[2/5] Copying the verified word table; preserving the original...'
    $result.checks += Invoke-JsonProbe $basePython 'snapshot'
    New-Item -ItemType Directory -Path $target | Out-Null
    Copy-Item -LiteralPath (Join-Path $source $cacheName) -Destination (Join-Path $target $cacheName) -ErrorAction Stop
    if ((Get-FileHash -LiteralPath (Join-Path $target $cacheName) -Algorithm SHA256).Hash -ine $expectedHash) {
        throw 'Copied word table hash mismatch'
    }
    [Environment]::SetEnvironmentVariable('TIKTOKEN_CACHE_DIR', $target, 'Process')
    $result.checks += Invoke-JsonProbe $python 'warm'

    Write-Output '[3/5] Updating only the current-user cache setting...'
    $settingChanged = $true
    [Environment]::SetEnvironmentVariable('TIKTOKEN_CACHE_DIR', $target, 'User')
    $configured = [Environment]::GetEnvironmentVariable('TIKTOKEN_CACHE_DIR', 'User')
    if ($configured -ne $target) { throw 'User cache setting readback failed' }
    [Environment]::SetEnvironmentVariable('TIKTOKEN_CACHE_DIR', $configured, 'Process')

    Write-Output '[4/5] Testing real downloads and fresh-process offline loading...'
    $result.checks += Invoke-JsonProbe $python 'cold'
    $result.checks += Invoke-JsonProbe $python 'offline-both'
    $result.checks += Invoke-JsonProbe $basePython 'snapshot'

    Write-Output '[5/5] Recording verification; original and staging remain intact...'
    $result.status = 'PASS'
    $result.user_setting = $configured
    $result.source_state = 'unchanged'
    $result.residual_write_state = 'new probes use target; earlier application processes may retain old environment'
    $result.retained_stage = $stage
    $result.generated_at = [DateTimeOffset]::Now.ToString('o')
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $receipt -Encoding UTF8
    Write-Output "PASS: cache relocated to $target"
    Write-Output 'Restart previously running Codex/terminals to inherit the new setting.'
    Write-Output "Receipt: $receipt"
} catch {
    $failure = $_.Exception.Message
    if (-not $CheckOnly) {
        if ($settingChanged) {
            try {
                [Environment]::SetEnvironmentVariable('TIKTOKEN_CACHE_DIR', $oldUser, 'User')
                $result.rollback = 'previous_user_setting_restored'
            } catch {
                $result.rollback = 'FAILED; inspect user TIKTOKEN_CACHE_DIR before continuing'
            }
        }
        [Environment]::SetEnvironmentVariable('TIKTOKEN_CACHE_DIR', $oldProcess, 'Process')
        $result.status = 'FAIL'
        $result.errors = @($failure)
        $result.generated_at = [DateTimeOffset]::Now.ToString('o')
        $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $receipt -Encoding UTF8
    }
    Write-Error "Stopped: $failure. Originals were not modified; retained targets are not automatically removed."
    exit 1
}
