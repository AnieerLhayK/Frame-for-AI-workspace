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

function Get-SkillFileStatus {
  param(
    [Parameter(Mandatory = $true)]$Skill,
    [Parameter(Mandatory = $true)][string]$WorkspaceRoot,
    [Parameter(Mandatory = $true)][string]$Kind
  )

  $skillRoot = Resolve-WorkspacePath -WorkspaceRoot $WorkspaceRoot -Path ([string]$Skill.source_path)
  $files = if ($Kind -eq "required") { $Skill.required_files } else { $Skill.optional_files }

  foreach ($file in $files) {
    $path = Resolve-WorkspacePath -WorkspaceRoot $skillRoot -Path ([string]$file)
    [pscustomobject]@{
      Skill = $Skill.id
      Kind = $Kind
      RelativePath = $file
      Expected = $path
      Exists = Test-Path -LiteralPath $path
    }
  }
}

function Get-ProtocolStatus {
  param(
    [Parameter(Mandatory = $true)]$Protocol,
    [Parameter(Mandatory = $true)][string]$WorkspaceRoot
  )

  $path = Resolve-WorkspacePath -WorkspaceRoot $WorkspaceRoot -Path ([string]$Protocol.path)
  [pscustomobject]@{
    Protocol = $Protocol.id
    Required = [bool]$Protocol.required
    Path = $path
    Exists = Test-Path -LiteralPath $path -PathType Leaf
  }
}

function Get-RuntimeLoopStatus {
  param([Parameter(Mandatory = $true)][string]$WorkspaceRoot)

  $paths = @(
    @{ Component = "runtime-loop-directory"; RelativePath = "packages/character-system/reports/runtime-loop"; PathType = "Container" },
    @{ Component = "runtime-loop-policy"; RelativePath = "packages/character-system/shared/runtime_loop_policy.md"; PathType = "Leaf" },
    @{ Component = "diagnosis-ledger"; RelativePath = "packages/character-system/reports/runtime-loop/ledgers/diagnosis_ledger.md"; PathType = "Leaf" },
    @{ Component = "patch-ledger"; RelativePath = "packages/character-system/reports/runtime-loop/ledgers/patch_ledger.md"; PathType = "Leaf" },
    @{ Component = "generalization-ledger"; RelativePath = "packages/character-system/reports/runtime-loop/ledgers/generalization_ledger.md"; PathType = "Leaf" },
    @{ Component = "diagnosis-template"; RelativePath = "packages/character-system/shared/templates/diagnosis_packet.template.md"; PathType = "Leaf" },
    @{ Component = "handoff-template"; RelativePath = "packages/character-system/shared/templates/handoff_packet.template.md"; PathType = "Leaf" },
    @{ Component = "patch-template"; RelativePath = "packages/character-system/shared/templates/patch_note.template.md"; PathType = "Leaf" },
    @{ Component = "validation-template"; RelativePath = "packages/character-system/shared/templates/validation_note.template.md"; PathType = "Leaf" },
    @{ Component = "generalization-template"; RelativePath = "packages/character-system/shared/templates/generalization_note.template.md"; PathType = "Leaf" }
  )

  foreach ($entry in $paths) {
    $path = Resolve-WorkspacePath -WorkspaceRoot $WorkspaceRoot -Path $entry.RelativePath
    [pscustomobject]@{
      Component = $entry.Component
      RelativePath = $entry.RelativePath
      Path = $path
      Exists = Test-Path -LiteralPath $path -PathType $entry.PathType
    }
  }
}

function Get-ProtocolValidationStatus {
  param([Parameter(Mandatory = $true)][string]$WorkspaceRoot)

  $paths = @(
    @{ Component = "protocol-manifest"; RelativePath = "packages/character-system/shared/protocol_manifest.json"; PathType = "Leaf" },
    @{ Component = "protocol-validator"; RelativePath = "scripts/validate_protocols.py"; PathType = "Leaf" },
    @{ Component = "protocol-validation-report"; RelativePath = "reports/protocol_validation_report.md"; PathType = "Leaf" }
  )

  foreach ($entry in $paths) {
    $path = Resolve-WorkspacePath -WorkspaceRoot $WorkspaceRoot -Path $entry.RelativePath
    [pscustomobject]@{
      Component = $entry.Component
      RelativePath = $entry.RelativePath
      Path = $path
      Exists = Test-Path -LiteralPath $path -PathType $entry.PathType
    }
  }
}

function Get-ManifestPortabilityStatus {
  param([Parameter(Mandatory = $true)][string]$WorkspaceRoot)

  $paths = @(
    @{ Component = "manifest-portability-policy"; RelativePath = "shared/manifest_portability_policy.md"; PathType = "Leaf" },
    @{ Component = "bootstrap-workspace"; RelativePath = "scripts/bootstrap_workspace.py"; PathType = "Leaf" },
    @{ Component = "manifest-validator"; RelativePath = "scripts/validate_manifest.py"; PathType = "Leaf" },
    @{ Component = "migration-dry-run"; RelativePath = "scripts/migration_dry_run.py"; PathType = "Leaf" },
    @{ Component = "manifest-validation-report"; RelativePath = "reports/manifest_validation_report.md"; PathType = "Leaf" },
    @{ Component = "migration-dry-run-report"; RelativePath = "reports/migration_dry_run_report.md"; PathType = "Leaf" },
    @{ Component = "manifest-portability-report"; RelativePath = "reports/manifest_portability_report.md"; PathType = "Leaf" }
  )

  foreach ($entry in $paths) {
    $path = Resolve-WorkspacePath -WorkspaceRoot $WorkspaceRoot -Path $entry.RelativePath
    [pscustomobject]@{
      Component = $entry.Component
      RelativePath = $entry.RelativePath
      Path = $path
      Exists = Test-Path -LiteralPath $path -PathType $entry.PathType
    }
  }
}

function Get-HardcodedPathFindings {
  param(
    [Parameter(Mandatory = $true)][string]$WorkspaceRoot,
    [Parameter(Mandatory = $true)]$Manifest
  )

  $rootTokens = @()
  $rootTokens += [string]$Manifest.workspace.source_of_truth
  foreach ($root in $Manifest.platform_roots.PSObject.Properties.Value) {
    $rootTokens += [string]$root
  }
  $tokens = @()
  foreach ($token in ($rootTokens | Sort-Object -Unique)) {
    $tokens += $token
    $tokens += ($token -replace '\\', '\\')
  }
  $tokens = $tokens | Sort-Object -Unique

  $textExtensions = @(
    ".cfg", ".css", ".csv", ".html", ".ini", ".js", ".json", ".md",
    ".ps1", ".py", ".toml", ".ts", ".txt", ".xml", ".yaml", ".yml"
  )
  $gitFiles = @(& git -C $WorkspaceRoot ls-files --cached --others --exclude-standard 2>$null)
  if ($LASTEXITCODE -eq 0) {
    $files = $gitFiles |
      ForEach-Object { Join-Path $WorkspaceRoot $_ } |
      Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
      ForEach-Object { Get-Item -LiteralPath $_ -Force } |
      Where-Object {
        $_.Length -le 2MB -and
        $textExtensions -contains $_.Extension.ToLowerInvariant()
      }
  } else {
    $files = Get-ChildItem -LiteralPath $WorkspaceRoot -Recurse -Force -File -ErrorAction SilentlyContinue |
      Where-Object {
        $_.FullName -notmatch '\\.git\\' -and
        $_.FullName -notmatch '\\__pycache__\\' -and
        $_.Length -le 2MB -and
        $textExtensions -contains $_.Extension.ToLowerInvariant()
      }
  }

  foreach ($file in $files) {
    $content = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ($null -eq $content) { continue }
    foreach ($token in $tokens) {
      if ($content.Contains($token)) {
        $normalizedRoot = (Get-NormalizedPath $WorkspaceRoot)
        $normalizedFile = [System.IO.Path]::GetFullPath($file.FullName)
        $relative = if ($normalizedFile.StartsWith($normalizedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
          $normalizedFile.Substring($normalizedRoot.Length).TrimStart('\')
        } else {
          $normalizedFile
        }
        $category = if ($relative -eq "workspace_manifest.yaml") {
          "manifest-source-of-truth"
        } elseif ($relative -like "reports/*" -or $relative -like "reports\*") {
          "generated-report"
        } elseif ($relative -like "scripts/*" -or $relative -like "scripts\*") {
          "script"
        } elseif ($relative -like "shared/*" -or $relative -like "shared\*") {
          "shared-doc"
        } elseif ($relative -like "skills/*" -or $relative -like "skills\*" -or $relative -like "packages/*" -or $relative -like "packages\*") {
          "skill-doc-or-source"
        } else {
          "other"
        }
        [pscustomobject]@{
          File = $relative
          Token = $token
          Category = $category
        }
      }
    }
  }
}

function Get-GitBoundaryStatus {
  param(
    [Parameter(Mandatory = $true)][string]$WorkspaceRoot,
    [Parameter(Mandatory = $true)]$Manifest
  )

  $paths = @($WorkspaceRoot)
  foreach ($root in $Manifest.platform_roots.PSObject.Properties.Value) {
    $paths += [string]$root
  }

  $paths | Sort-Object -Unique | ForEach-Object {
    $gitPath = Join-Path $_ ".git"
    [pscustomobject]@{
      Path = $_
      HasGit = Test-Path -LiteralPath $gitPath
      BoundaryRole = if ((Get-NormalizedPath $_) -eq (Get-NormalizedPath $WorkspaceRoot)) { "source-of-truth" } else { "platform-projection" }
    }
  }
}

function Add-Table {
  param(
    $Lines,
    [Parameter(Mandatory = $true)][array]$Rows,
    [Parameter(Mandatory = $true)][string[]]$Headers
  )

  [void]$Lines.Add("| " + ($Headers -join " | ") + " |")
  [void]$Lines.Add("| " + (($Headers | ForEach-Object { "---" }) -join " | ") + " |")
  foreach ($row in $Rows) {
    $values = foreach ($header in $Headers) {
      $value = $row.$header
      if ($null -eq $value) { "" } else { [string]$value }
    }
    [void]$Lines.Add("| " + ($values -join " | ") + " |")
  }
}

function Get-SkillExposureSummary {
  param(
    [Parameter(Mandatory = $true)]$Skill,
    [Parameter(Mandatory = $true)]$Manifest
  )

  $items = @()
  foreach ($exposure in @($Skill.exposures)) {
    $projection = $Manifest.projections |
      Where-Object { [string]$_.id -eq [string]$exposure.projection_id } |
      Select-Object -First 1
    $path = if ($null -ne $projection) { [string]$projection.link_path } else { "<missing projection>" }
    $items += "$([string]$exposure.platform):$([string]$exposure.projection_id) -> $path"
  }

  if ($items.Count -eq 0) {
    return "$([string]$Skill.platform) (legacy) -> $([string]$Skill.projection_path)"
  }
  return $items -join "<br>"
}

function Get-SourceCommit {
  param([Parameter(Mandatory = $true)][string]$WorkspaceRoot)

  try {
    $commit = git -C $WorkspaceRoot rev-parse --short HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $commit) {
      return [string]$commit
    }
  } catch {
    return "unknown"
  }

  return "unknown"
}

function Add-ReportHeader {
  param(
    $Lines,
    [Parameter(Mandatory = $true)][string]$ReportName,
    [Parameter(Mandatory = $true)][string]$GeneratedAt,
    [Parameter(Mandatory = $true)][string]$GeneratedBy,
    [Parameter(Mandatory = $true)][string]$SourceRoot,
    [Parameter(Mandatory = $true)][string]$ManifestPath,
    [Parameter(Mandatory = $true)][string]$ManifestVersion,
    [Parameter(Mandatory = $true)][string]$ManifestLastModified,
    [Parameter(Mandatory = $true)][string]$SourceCommit,
    [Parameter(Mandatory = $true)][string]$ReportScope
  )

  [void]$Lines.Add("---")
  [void]$Lines.Add("report_name: $ReportName")
  [void]$Lines.Add("generated_at: $GeneratedAt")
  [void]$Lines.Add("generated_by: $GeneratedBy")
  [void]$Lines.Add("source_root: $SourceRoot")
  [void]$Lines.Add("manifest_path: $ManifestPath")
  [void]$Lines.Add("manifest_version: $ManifestVersion")
  [void]$Lines.Add("manifest_last_modified: $ManifestLastModified")
  [void]$Lines.Add("source_commit: $SourceCommit")
  [void]$Lines.Add("report_scope: $ReportScope")
  [void]$Lines.Add("report_is_snapshot: true")
  [void]$Lines.Add("truth_source:")
  [void]$Lines.Add("  - workspace_manifest.yaml")
  [void]$Lines.Add("  - shared/")
  [void]$Lines.Add("  - current git commit")
  [void]$Lines.Add("staleness_policy: Regenerate after manifest, shared policy, projection, Git baseline, or report script changes.")
  [void]$Lines.Add("---")
  [void]$Lines.Add("")
  [void]$Lines.Add("Report is a snapshot. Manifest is the source of truth. If this report conflicts with the manifest, trust the manifest and regenerate the report.")
  [void]$Lines.Add("")
}

$ManifestPath = Resolve-ManifestPath -RequestedPath $ManifestPath
$manifest = Read-WorkspaceManifest -Path $ManifestPath
$workspaceRoot = [string]$manifest.workspace.source_of_truth
$reportRoot = Join-Path $workspaceRoot "reports"
New-Item -ItemType Directory -Force -Path $reportRoot | Out-Null
$resolvedManifestPath = [System.IO.Path]::GetFullPath($ManifestPath)
$manifestLastModified = (Get-Item -LiteralPath $resolvedManifestPath).LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss zzz")
$sourceCommit = Get-SourceCommit -WorkspaceRoot $workspaceRoot

$manifestStatus = [pscustomobject]@{
  Exists = Test-Path -LiteralPath $ManifestPath -PathType Leaf
  Path = $resolvedManifestPath
  WorkspaceName = $manifest.workspace.workspace_name
  Version = $manifest.workspace.workspace_version
  SourceOfTruth = $workspaceRoot
}

$projectionStatuses = $manifest.projections | ForEach-Object { Get-ProjectionStatus -Projection $_ -WorkspaceRoot $workspaceRoot }
$requiredStatuses = foreach ($skill in $manifest.skills) { Get-SkillFileStatus -Skill $skill -WorkspaceRoot $workspaceRoot -Kind "required" }
$optionalStatuses = foreach ($skill in $manifest.skills) { Get-SkillFileStatus -Skill $skill -WorkspaceRoot $workspaceRoot -Kind "optional" }
$protocolStatuses = $manifest.protocols | ForEach-Object { Get-ProtocolStatus -Protocol $_ -WorkspaceRoot $workspaceRoot }
$runtimeLoopStatuses = Get-RuntimeLoopStatus -WorkspaceRoot $workspaceRoot
$protocolValidationStatuses = Get-ProtocolValidationStatus -WorkspaceRoot $workspaceRoot
$manifestPortabilityStatuses = Get-ManifestPortabilityStatus -WorkspaceRoot $workspaceRoot
$hardcodedFindings = Get-HardcodedPathFindings -WorkspaceRoot $workspaceRoot -Manifest $manifest
$gitBoundaries = Get-GitBoundaryStatus -WorkspaceRoot $workspaceRoot -Manifest $manifest

$missingRequired = @($requiredStatuses | Where-Object { -not $_.Exists })
$missingProtocols = @($protocolStatuses | Where-Object { $_.Required -and -not $_.Exists })
$missingRuntimeLoop = @($runtimeLoopStatuses | Where-Object { -not $_.Exists })
$missingProtocolValidation = @($protocolValidationStatuses | Where-Object { -not $_.Exists })
$missingManifestPortability = @($manifestPortabilityStatuses | Where-Object { -not $_.Exists })
$missingOptional = @($optionalStatuses | Where-Object { -not $_.Exists })
$projectionDrift = @($projectionStatuses | Where-Object { $_.Status -ne "OK" })
$sharedExpected = Get-NormalizedPath (Resolve-WorkspacePath -WorkspaceRoot $workspaceRoot -Path ([string]$manifest.shared.source_path))
$sharedProjectionStatuses = @($projectionStatuses | Where-Object { (Get-NormalizedPath $_.ExpectedTarget) -eq $sharedExpected })
$sharedProjectionDrift = @($sharedProjectionStatuses | Where-Object { $_.Status -ne "OK" })
$sharedUniquenessStatus = if ($sharedProjectionDrift.Count -eq 0) { "OK" } else { "FAILED" }
$unsafeHardcoded = @($hardcodedFindings | Where-Object { $_.Category -notin @("manifest-source-of-truth", "generated-report") })

$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

$setupLines = [System.Collections.ArrayList]@()
Add-ReportHeader -Lines $setupLines -ReportName "workspace_setup_report" -GeneratedAt $now -GeneratedBy "scripts/sync_report.ps1" -SourceRoot $workspaceRoot -ManifestPath $resolvedManifestPath -ManifestVersion ([string]$manifest.workspace.workspace_version) -ManifestLastModified $manifestLastModified -SourceCommit $sourceCommit -ReportScope "workspace setup, skill registry, and projection status"
[void]$setupLines.Add("# Workspace Setup Report")
[void]$setupLines.Add("")
[void]$setupLines.Add("Generated: $now")
[void]$setupLines.Add("")
[void]$setupLines.Add("## Workspace")
[void]$setupLines.Add("")
[void]$setupLines.Add("- Workspace name: ``$($manifest.workspace.workspace_name)``")
[void]$setupLines.Add("- Workspace version: ``$($manifest.workspace.workspace_version)``")
[void]$setupLines.Add("- Source of truth: manifest field ``workspace.source_of_truth``")
[void]$setupLines.Add("- Policy: platform skill directories are projection surfaces only.")
[void]$setupLines.Add("")
[void]$setupLines.Add("## Skills")
[void]$setupLines.Add("")
Add-Table -Lines $setupLines -Rows ($manifest.skills | ForEach-Object {
  [pscustomobject]@{
    Skill = $_.id
    Role = $_.role
    Authority = $_.authority.default
    Execution = $_.execution_modes.default
    Package = if ($_.PSObject.Properties.Name -contains "package_id") { $_.package_id } else { "" }
    Source = $_.source_path
    Exposures = Get-SkillExposureSummary -Skill $_ -Manifest $manifest
    LegacyPlatform = $_.platform
    LegacyProjection = $_.projection_path
    Protocols = ($_.protocol_dependencies -join ", ")
  }
}) -Headers @("Skill", "Package", "Role", "Authority", "Execution", "Source", "Exposures", "LegacyPlatform", "LegacyProjection", "Protocols")
[void]$setupLines.Add("")
[void]$setupLines.Add("## Link Status")
[void]$setupLines.Add("")
Add-Table -Lines $setupLines -Rows ($projectionStatuses | ForEach-Object {
  [pscustomobject]@{
    Link = $_.Name
    Status = $_.Status
    Type = $_.LinkType
    Path = $_.LinkPath
    Target = $_.ExpectedTarget
  }
}) -Headers @("Link", "Status", "Type", "Path", "Target")
[void]$setupLines.Add("")
[void]$setupLines.Add("## Next Steps")
[void]$setupLines.Add("")
[void]$setupLines.Add("- Run ``scripts/check_links.ps1`` after any platform or workspace path change.")
[void]$setupLines.Add("- Keep source edits inside manifest-declared skill source paths.")
[void]$setupLines.Add("- Update ``workspace_manifest.yaml`` before changing projections or shared protocol locations.")

$healthLines = [System.Collections.ArrayList]@()
Add-ReportHeader -Lines $healthLines -ReportName "workspace_health_report" -GeneratedAt $now -GeneratedBy "scripts/sync_report.ps1" -SourceRoot $workspaceRoot -ManifestPath $resolvedManifestPath -ManifestVersion ([string]$manifest.workspace.workspace_version) -ManifestLastModified $manifestLastModified -SourceCommit $sourceCommit -ReportScope "manifest status, link status, missing files, hardcoded paths, protocol consistency, drift, shared uniqueness, and Git boundaries"
[void]$healthLines.Add("# Workspace Health Report")
[void]$healthLines.Add("")
[void]$healthLines.Add("Generated: $now")
[void]$healthLines.Add("")
[void]$healthLines.Add("## Manifest Status")
[void]$healthLines.Add("")
Add-Table -Lines $healthLines -Rows @($manifestStatus) -Headers @("Exists", "Path", "WorkspaceName", "Version", "SourceOfTruth")
[void]$healthLines.Add("")
[void]$healthLines.Add("## Link Status")
[void]$healthLines.Add("")
Add-Table -Lines $healthLines -Rows ($projectionStatuses | ForEach-Object {
  [pscustomobject]@{
    Name = $_.Name
    Status = $_.Status
    LinkType = $_.LinkType
    TargetExists = $_.TargetExists
    LinkPath = $_.LinkPath
    ExpectedTarget = $_.ExpectedTarget
    ActualTarget = $_.ActualTarget
  }
}) -Headers @("Name", "Status", "LinkType", "TargetExists", "LinkPath", "ExpectedTarget", "ActualTarget")
[void]$healthLines.Add("")
[void]$healthLines.Add("## Missing Required Files")
[void]$healthLines.Add("")
if ($missingRequired.Count -eq 0 -and $missingProtocols.Count -eq 0) {
  [void]$healthLines.Add("- None.")
} else {
  Add-Table -Lines $healthLines -Rows ($missingRequired + ($missingProtocols | ForEach-Object {
    [pscustomobject]@{ Skill = "shared-protocol"; Kind = "required"; RelativePath = $_.Protocol; Expected = $_.Path; Exists = $_.Exists }
  })) -Headers @("Skill", "Kind", "RelativePath", "Expected", "Exists")
}
[void]$healthLines.Add("")
[void]$healthLines.Add("## Missing Optional Files")
[void]$healthLines.Add("")
if ($missingOptional.Count -eq 0) {
  [void]$healthLines.Add("- None.")
} else {
  Add-Table -Lines $healthLines -Rows $missingOptional -Headers @("Skill", "Kind", "RelativePath", "Expected", "Exists")
}
[void]$healthLines.Add("")
[void]$healthLines.Add("## Hardcoded Paths Remaining")
[void]$healthLines.Add("")
if ($hardcodedFindings.Count -eq 0) {
  [void]$healthLines.Add("- None.")
} else {
  Add-Table -Lines $healthLines -Rows $hardcodedFindings -Headers @("File", "Token", "Category")
}
[void]$healthLines.Add("")
[void]$healthLines.Add("Unsafe hardcoded path references outside manifest/generated reports: ``$($unsafeHardcoded.Count)``.")
[void]$healthLines.Add("")
[void]$healthLines.Add("## Protocol Consistency")
[void]$healthLines.Add("")
Add-Table -Lines $healthLines -Rows $protocolStatuses -Headers @("Protocol", "Required", "Path", "Exists")
[void]$healthLines.Add("")
[void]$healthLines.Add("## Runtime Loop Status")
[void]$healthLines.Add("")
Add-Table -Lines $healthLines -Rows $runtimeLoopStatuses -Headers @("Component", "RelativePath", "Path", "Exists")
[void]$healthLines.Add("")
[void]$healthLines.Add("## Protocol Validation Status")
[void]$healthLines.Add("")
Add-Table -Lines $healthLines -Rows $protocolValidationStatuses -Headers @("Component", "RelativePath", "Path", "Exists")
[void]$healthLines.Add("")
[void]$healthLines.Add("## Manifest Portability Status")
[void]$healthLines.Add("")
Add-Table -Lines $healthLines -Rows $manifestPortabilityStatuses -Headers @("Component", "RelativePath", "Path", "Exists")
[void]$healthLines.Add("")
[void]$healthLines.Add("## Projection Drift")
[void]$healthLines.Add("")
if ($projectionDrift.Count -eq 0) {
  [void]$healthLines.Add("- None.")
} else {
  Add-Table -Lines $healthLines -Rows $projectionDrift -Headers @("Name", "Status", "LinkPath", "ExpectedTarget", "ActualTarget")
}
[void]$healthLines.Add("")
[void]$healthLines.Add("## Shared Uniqueness")
[void]$healthLines.Add("")
[void]$healthLines.Add("- Expected shared source: ``shared`` resolved from manifest.")
[void]$healthLines.Add("- Status: ``$sharedUniquenessStatus``")
[void]$healthLines.Add("")
[void]$healthLines.Add("## Git Boundaries")
[void]$healthLines.Add("")
Add-Table -Lines $healthLines -Rows $gitBoundaries -Headers @("Path", "HasGit", "BoundaryRole")
[void]$healthLines.Add("")
[void]$healthLines.Add("## Overall Status")
[void]$healthLines.Add("")
$overall = if ($missingRequired.Count -eq 0 -and $missingProtocols.Count -eq 0 -and $missingRuntimeLoop.Count -eq 0 -and $missingProtocolValidation.Count -eq 0 -and $missingManifestPortability.Count -eq 0 -and $projectionDrift.Count -eq 0 -and $unsafeHardcoded.Count -eq 0 -and $sharedUniquenessStatus -eq "OK") { "HEALTHY" } else { "NEEDS_ATTENTION" }
[void]$healthLines.Add("- Status: ``$overall``")
[void]$healthLines.Add("- Required missing count: ``$($missingRequired.Count + $missingProtocols.Count)``")
[void]$healthLines.Add("- Runtime loop missing count: ``$($missingRuntimeLoop.Count)``")
[void]$healthLines.Add("- Protocol validation missing count: ``$($missingProtocolValidation.Count)``")
[void]$healthLines.Add("- Manifest portability missing count: ``$($missingManifestPortability.Count)``")
[void]$healthLines.Add("- Optional missing count: ``$($missingOptional.Count)``")
[void]$healthLines.Add("- Projection drift count: ``$($projectionDrift.Count)``")
[void]$healthLines.Add("- Unsafe hardcoded path count: ``$($unsafeHardcoded.Count)``")

Set-Content -LiteralPath (Join-Path $reportRoot "workspace_setup_report.md") -Value $setupLines -Encoding UTF8
Set-Content -LiteralPath (Join-Path $reportRoot "workspace_health_report.md") -Value $healthLines -Encoding UTF8

Write-Host "Wrote reports/workspace_setup_report.md"
Write-Host "Wrote reports/workspace_health_report.md"
