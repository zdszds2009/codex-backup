# Auto Demo Script for Codex Backup
# Demonstrates one complete export-and-restore cycle
# Run this in a terminal while recording with ScreenToGif or OBS

param(
    [string]$OutDir = "$env:USERPROFILE\Desktop\codex-demo-output"
)

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Codex Backup - Demo Script" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Step 1/5: Navigate to project" -ForegroundColor Yellow
Set-Location C:\Users\sunya\Documents\skills\codex-backup
Write-Host "  -> " (Get-Location)
Write-Host ""

Write-Host "Step 2/5: Create output directory" -ForegroundColor Yellow
if (Test-Path $OutDir) { Remove-Item -Recurse -Force $OutDir }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Write-Host "  -> $OutDir"
Write-Host ""

Write-Host "Step 3/5: Build restore package from Codex data" -ForegroundColor Yellow
Write-Host "  Running: python scripts/build_restore_package.py --out `"$OutDir`""
Write-Host ""
$buildResult = python scripts/build_restore_package.py --out "$OutDir" 2>&1
$buildResult | ForEach-Object { Write-Host "  $_" }
Write-Host ""

Write-Host "Step 4/5: Inspect the generated package" -ForegroundColor Yellow
$pkgDir = Get-ChildItem -Path $OutDir -Directory | Select-Object -First 1
if ($pkgDir) {
    Write-Host "  Package: $($pkgDir.FullName)"
    Write-Host "  Contents:"
    Get-ChildItem -Path $pkgDir.FullName -Recurse -File | ForEach-Object {
        $s = [math]::Round($_.Length / 1KB, 1)
        Write-Host "    $($_.Name) ($s KB)"
    }
    Write-Host ""
    Write-Host "  Running: python scripts/inspect_package.py `"$($pkgDir.FullName)`""
    Write-Host ""
    $r = python scripts/inspect_package.py "$($pkgDir.FullName)" 2>&1
    $r | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
    $m = Join-Path $pkgDir.FullName "manifest.json"
    if (Test-Path $m) {
        $j = Get-Content $m -Raw | ConvertFrom-Json
        Write-Host "  Summary:" -ForegroundColor Green
        Write-Host "    Project : $($j.project_name)"
        Write-Host "    Version : $($j.codex_version)"
        Write-Host "    Sessions: $($j.session_count)"
        Write-Host "    Created : $($j.created_at)"
    }
}
Write-Host ""

Write-Host "Step 5/5: Verify package integrity" -ForegroundColor Yellow
$zipFile = Get-ChildItem -Path $OutDir -Filter "*.zip" | Select-Object -First 1
if ($zipFile) {
    $sz = [math]::Round($zipFile.Length / 1MB, 2)
    Write-Host "  Package: $($zipFile.Name) ($sz MB)" -ForegroundColor Green
}
Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Demo Complete! Output: $OutDir" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "Next: python scripts/restore_package.py --package <zip>" -ForegroundColor Yellow
