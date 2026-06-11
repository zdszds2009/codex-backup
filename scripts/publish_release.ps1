param(
  [string]$RemoteUrl = "https://github.com/zdszds2009/codex-project-restore-packager.git",
  [string]$Tag = "v0.1.0"
)

$ErrorActionPreference = "Stop"

git remote remove origin 2>$null
git remote add origin $RemoteUrl
git push -u origin main
git tag -f $Tag
git push origin $Tag --force

Write-Host "Published main and tag $Tag to $RemoteUrl"
