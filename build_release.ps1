Write-Host "[1/6] Killing running barkoder instance..."
Get-Process -Name barkoder -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "[2/6] Building with PyInstaller..."
uv run pyinstaller barkoder.spec
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller failed (exit $LASTEXITCODE). Aborting." -ForegroundColor Red
    exit 1
}

Push-Location dist

Write-Host "[3/6] Preparing staging folder..."
if (Test-Path .\Barkoder) { Remove-Item -Recurse -Force .\Barkoder }
New-Item -ItemType Directory -Path .\Barkoder | Out-Null

Write-Host "[4/6] Copying exe..."
Copy-Item barkoder.exe .\Barkoder\

Write-Host "[5/6] Creating Barkoder.zip..."
& "C:\Program Files\7-Zip\7z.exe" a Barkoder.zip .\Barkoder\
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Host "ERROR: 7-Zip failed (exit $LASTEXITCODE). Aborting." -ForegroundColor Red
    exit 1
}

Write-Host "[6/6] Cleaning up staging folder..."
Remove-Item -Recurse -Force .\Barkoder

Pop-Location

Write-Host "Build complete. Launching barkoder..." -ForegroundColor Green
Start-Process "dist\barkoder.exe"
