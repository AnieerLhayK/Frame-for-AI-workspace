$target = Join-Path $PSScriptRoot 'platform/setup_links.ps1'
& $target @args
exit $LASTEXITCODE
