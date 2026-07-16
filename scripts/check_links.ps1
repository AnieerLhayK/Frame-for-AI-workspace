$target = Join-Path $PSScriptRoot 'validation/check_links.ps1'
& $target @args
exit $LASTEXITCODE
