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

  $workspaceRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
  $scriptDefault = Join-Path $workspaceRoot "workspace_manifest.yaml"
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
    return $null
  }

  if ($Item.Target -is [array]) {
    return ($Item.Target | Select-Object -First 1)
  }

  return [string]$Item.Target
}

function New-WorkspaceLink {
  param(
    [Parameter(Mandatory = $true)][string]$LinkPath,
    [Parameter(Mandatory = $true)][string]$Target
  )

  try {
    New-Item -ItemType SymbolicLink -Path $LinkPath -Target $Target -Force | Out-Null
    return "SymbolicLink"
  } catch {
    New-Item -ItemType Junction -Path $LinkPath -Target $Target -Force | Out-Null
    return "Junction"
  }
}

function Remove-WorkspaceLink {
  param([Parameter(Mandatory = $true)][string]$LinkPath)

  $item = Get-Item -LiteralPath $LinkPath -Force
  if ($item.LinkType -eq "SymbolicLink" -or $item.LinkType -eq "Junction") {
    [System.IO.Directory]::Delete($LinkPath)
    return
  }

  throw "Refusing to remove non-link item: $LinkPath"
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
    Write-Output "  Target: $($row.Target)"

    $note = Get-ObjectValue -InputObject $row -Name "Note"
    if (-not [string]::IsNullOrWhiteSpace($note)) {
      Write-Output "  Note: $note"
    }

    Write-Output ""
  }
}

$ManifestPath = Resolve-ManifestPath -RequestedPath $ManifestPath
$manifest = Read-WorkspaceManifest -Path $ManifestPath
$workspaceRoot = [string]$manifest.workspace.source_of_truth

foreach ($root in $manifest.platform_roots.PSObject.Properties.Value) {
  New-Item -ItemType Directory -Force -Path ([string]$root) | Out-Null
}

$results = foreach ($projection in $manifest.projections) {
  $linkPath = Resolve-WorkspacePath -WorkspaceRoot $workspaceRoot -Path ([string]$projection.link_path)
  $target = Resolve-WorkspacePath -WorkspaceRoot $workspaceRoot -Path ([string]$projection.target_path)

  if (-not (Test-Path -LiteralPath $target -PathType Container)) {
    [pscustomobject]@{
      Name = $projection.name
      Status = "MISSING_TARGET"
      LinkPath = $linkPath
      Target = $target
      LinkType = ""
      Note = "Create the manifest-declared source directory first."
    }
    continue
  }

  if (Test-Path -LiteralPath $linkPath) {
    $item = Get-Item -LiteralPath $linkPath -Force
    $isLink = ($item.LinkType -eq "SymbolicLink" -or $item.LinkType -eq "Junction")

    if (-not $isLink) {
      [pscustomobject]@{
        Name = $projection.name
        Status = "BLOCKED_REAL_ITEM"
        LinkPath = $linkPath
        Target = $target
        LinkType = ""
        Note = "Existing real file or directory was preserved. Move it manually before linking."
      }
      continue
    }

    $currentTarget = Get-LinkTarget -Item $item
    if ((Get-NormalizedPath $currentTarget) -eq (Get-NormalizedPath $target)) {
      [pscustomobject]@{
        Name = $projection.name
        Status = "OK"
        LinkPath = $linkPath
        Target = $target
        LinkType = $item.LinkType
        Note = "Already correct."
      }
      continue
    }

    Remove-WorkspaceLink -LinkPath $linkPath
    $createdType = New-WorkspaceLink -LinkPath $linkPath -Target $target
    [pscustomobject]@{
      Name = $projection.name
      Status = "RELINKED"
      LinkPath = $linkPath
      Target = $target
      LinkType = $createdType
      Note = "Incorrect projection was replaced from manifest."
    }
    continue
  }

  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $linkPath) | Out-Null
  $newType = New-WorkspaceLink -LinkPath $linkPath -Target $target
  [pscustomobject]@{
    Name = $projection.name
    Status = "CREATED"
    LinkPath = $linkPath
    Target = $target
    LinkType = $newType
    Note = "Projection created from manifest."
  }
}

Write-ProjectionResults -Rows @($results)

if ($results.Status -contains "BLOCKED_REAL_ITEM" -or $results.Status -contains "MISSING_TARGET") {
  exit 1
}
