# fix_imports.ps1
# Run this from your medvol\ root folder:
#   powershell -ExecutionPolicy Bypass -File fix_imports.ps1
#
# What it does:
#   1. Fixes all old-style imports in every .py file under medvol\
#   2. Deletes stale __pycache__ folders so Python re-compiles cleanly

Write-Host "Fixing imports..." -ForegroundColor Cyan

Get-ChildItem -Recurse -Filter "*.py" -Path "medvol" |
  ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $fixed = $content `
      -replace 'from core\.', 'from medvol.core.' `
      -replace 'from ui\.slice_canvas', 'from medvol.ui.slice_canvas' `
      -replace 'from ui\.main_viewer', 'from medvol.ui.main_viewer' `
      -replace 'from utils\.', 'from medvol.utils.'
    if ($fixed -ne $content) {
        Set-Content -Path $_.FullName -Value $fixed -NoNewline
        Write-Host "  Fixed: $($_.FullName)" -ForegroundColor Green
    }
  }

Write-Host ""
Write-Host "Clearing __pycache__..." -ForegroundColor Cyan
Get-ChildItem -Recurse -Filter "__pycache__" -Directory |
  ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
    Write-Host "  Removed: $($_.FullName)" -ForegroundColor Yellow
  }

Write-Host ""
Write-Host "Done. Now run: python -m medvol" -ForegroundColor Cyan
