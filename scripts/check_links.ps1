param(
  [string]$ManifestPath = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Find-WorkspaceManifest {
  param(
    [Parameter(Mandatory = $true)][string]$StartPath,
    [int]$MaxParentDepth = 5,
    [string]$ManifestFilename = "workspace_manifest.yaml"
  )

  $current = [System.IO.Path]::GetFullPath($StartPath)
  if (Test-Path -LiteralPath $current -PathType Leaf) {
    $current = Split-Path -Parent $current
  }

  $attempts = @()
  for ($depth = 0; $depth -le $MaxParentDepth; $depth++) {
    $candidate = Join-Path $current $ManifestFilename
    $attempts += $candidate
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
      return [pscustomobject]@{ Found = $true; Path = [System.IO.Path]::GetFullPath($candidate); Attempts = $attempts }
    }

    $parent = Split-Path -Parent $current
    if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $current) { break }
    $current = $parent
  }

  return [pscustomobject]@{ Found = $false; Path = ""; Attempts = $attempts }
}

function Resolve-ManifestPath {
  param([string]$RequestedPath)

  if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
    if (Test-Path -LiteralPath $RequestedPath -PathType Leaf) {
      return [System.IO.Path]::GetFullPath($RequestedPath)
    }
    throw "[ERROR] Missing required resource: workspace_manifest.yaml`nExpected:`n$RequestedPath`nAction:`nrestore the manifest or pass a valid -ManifestPath."
  }

  $scriptDefault = Join-Path (Split-Path -Parent $PSScriptRoot) "workspace_manifest.yaml"
  if (Test-Path -LiteralPath $scriptDefault -PathType Leaf) {
    return [System.IO.Path]::GetFullPath($scriptDefault)
  }

  $discovery = Find-WorkspaceManifest -StartPath (Get-Location).Path -MaxParentDepth 5
  if ($discovery.Found) {
    return $discovery.Path
  }

  throw "[ERROR] Missing required resource: workspace_manifest.yaml`nDiscovery attempts:`n- $($discovery.Attempts -join "`n- ")`nAction:`nrun from inside the workspace, restore the manifest, or pass -ManifestPath."
}

function Read-WorkspaceManifest {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    throw "[ERROR] Missing required resource: workspace_manifest.yaml`nExpected:`n$Path`nAction:`nrestore the manifest or pass -ManifestPath."
  }

  $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
  return $raw | ConvertFrom-Json
}

function Get-NormalizedPath {
  param([Parameter(Mandatory = $true)][string]$Path)
  return [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
}

function Resolve-WorkspacePath {
  param(
    [Parameter(Mandatory = $true)][string]$WorkspaceRoot,
    [Parameter(Mandatory = $true)][string]$Path
  )

  if ([System.IO.Path]::IsPathRooted($Path)) {
    return [System.IO.Path]::GetFullPath($Path)
  }

  return [System.IO.Path]::GetFullPath((Join-Path $WorkspaceRoot ($Path -replace '/', '\')))
}

function Get-LinkTarget {
  param([Parameter(Mandatory = $true)]$Item)

  if ($null -eq $Item.Target) {
    return ""
  }

  if ($Item.Target -is [array]) {
    return ($Item.Target | Select-Object -First 1)
  }

  return [string]$Item.Target
}

function Get-ProjectionStatus {
  param(
    [Parameter(Mandatory = $true)]$Projection,
    [Parameter(Mandatory = $true)][string]$WorkspaceRoot
  )

  $linkPath = Resolve-WorkspacePath -WorkspaceRoot $WorkspaceRoot -Path ([string]$Projection.link_path)
  $expectedTarget = Resolve-WorkspacePath -WorkspaceRoot $WorkspaceRoot -Path ([string]$Projection.target_path)

  if (-not (Test-Path -LiteralPath $linkPath)) {
    return [pscustomobject]@{ Name = $Projection.name; Status = "MISSING_LINK"; LinkType = ""; LinkPath = $linkPath; ExpectedTarget = $expectedTarget; ActualTarget = ""; TargetExists = (Test-Path -LiteralPath $expectedTarget -PathType Container) }
  }

  $item = Get-Item -LiteralPath $linkPath -Force
  $isLink = ($item.LinkType -eq "SymbolicLink" -or $item.LinkType -eq "Junction")
  if (-not $isLink) {
    return [pscustomobject]@{ Name = $Projection.name; Status = "REAL_ITEM"; LinkType = ""; LinkPath = $linkPath; ExpectedTarget = $expectedTarget; ActualTarget = ""; TargetExists = (Test-Path -LiteralPath $expectedTarget -PathType Container) }
  }

  $actualTarget = Get-LinkTarget -Item $item
  $targetExists = Test-Path -LiteralPath $expectedTarget -PathType Container
  $status = if (-not $targetExists) {
    "MISSING_TARGET"
  } elseif ((Get-NormalizedPath $actualTarget) -eq (Get-NormalizedPath $expectedTarget)) {
    "OK"
  } else {
    "WRONG_TARGET"
  }

  [pscustomobject]@{
    Name = $Projection.name
    Status = $status
    LinkType = $item.LinkType
    LinkPath = $linkPath
    ExpectedTarget = $expectedTarget
    ActualTarget = $actualTarget
    TargetExists = $targetExists
  }
}

function Get-ObjectValue {
  param(
    [Parameter(Mandatory = $true)]$InputObject,
    [Parameter(Mandatory = $true)][string]$Name
  )

  $property = $InputObject.PSObject.Properties[$Name]
  if ($null -eq $property -or $null -eq $property.Value) {
    return ""
  }

  return [string]$property.Value
}

function Write-ProjectionResults {
  param([Parameter(Mandatory = $true)][object[]]$Rows)

  $count = @($Rows).Count
  $index = 0
  foreach ($row in $Rows) {
    $index += 1
    $linkType = Get-ObjectValue -InputObject $row -Name "LinkType"
    $line = "[$index/$count] $($row.Name) - $($row.Status)"
    if (-not [string]::IsNullOrWhiteSpace($linkType)) {
      $line = "$line ($linkType)"
    }

    Write-Output $line
    Write-Output "  LinkPath: $($row.LinkPath)"
    Write-Output "  ExpectedTarget: $($row.ExpectedTarget)"

    $actualTarget = Get-ObjectValue -InputObject $row -Name "ActualTarget"
    if (-not [string]::IsNullOrWhiteSpace($actualTarget)) {
      Write-Output "  ActualTarget: $actualTarget"
    }

    Write-Output "  TargetExists: $($row.TargetExists)"
    Write-Output ""
  }
}

$ManifestPath = Resolve-ManifestPath -RequestedPath $ManifestPath
$manifest = Read-WorkspaceManifest -Path $ManifestPath
$workspaceRoot = [string]$manifest.workspace.source_of_truth
$results = $manifest.projections | ForEach-Object { Get-ProjectionStatus -Projection $_ -WorkspaceRoot $workspaceRoot }

Write-ProjectionResults -Rows @($results)

$sharedExpected = Get-NormalizedPath (Resolve-WorkspacePath -WorkspaceRoot $workspaceRoot -Path ([string]$manifest.shared.source_path))
$sharedProjectionResults = $results | Where-Object { $_.ExpectedTarget -and ((Get-NormalizedPath $_.ExpectedTarget) -eq $sharedExpected) }
$sharedBad = @($sharedProjectionResults | Where-Object { $_.Status -ne "OK" })

if ($sharedBad) {
  Write-Host ""
  Write-Host "Shared uniqueness check failed: one or more shared projections do not target the manifest shared source." -ForegroundColor Red
}

$bad = @($results | Where-Object { $_.Status -ne "OK" })
if ($bad -or $sharedBad) {
  Write-Host ""
  Write-Host "Link check failed: $($bad.Count) projection issue(s)." -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "All manifest projections are correct, and shared projections are unique." -ForegroundColor Green
