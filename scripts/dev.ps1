# ==========================================
# Global News Intelligence - Local Dev Starter
# ==========================================

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host " Starting Global News Intelligence (GNI) Dev Stack" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 1. Activate venv
$VenvPython = Join-Path $PSScriptRoot "..\venv\Scripts\python.exe"
$VenvAlembic = Join-Path $PSScriptRoot "..\venv\Scripts\alembic.exe"
$VenvUvicorn = Join-Path $PSScriptRoot "..\venv\Scripts\uvicorn.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Python venv not found. Creating..." -ForegroundColor Yellow
    python -m venv (Join-Path $PSScriptRoot "..\venv")
    & (Join-Path $PSScriptRoot "..\venv\Scripts\pip.exe") install -r (Join-Path $PSScriptRoot "..\apps\api\requirements.txt")
}

# 2. Run Database Migrations
Write-Host "`n--> Running database migrations..." -ForegroundColor Green
Push-Location (Join-Path $PSScriptRoot "..")
& $VenvAlembic upgrade head
Pop-Location

# 3. Start Backend API
Write-Host "`n--> Launching FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
$BackendProcess = Start-Process -FilePath $VenvUvicorn -ArgumentList "apps.api.app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory (Join-Path $PSScriptRoot "..") -PassThru

# 4. Start Next.js Frontend
Write-Host "`n--> Launching Next.js Frontend on http://localhost:3000..." -ForegroundColor Green
$FrontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" -WorkingDirectory (Join-Path $PSScriptRoot "..\apps\web") -PassThru

Write-Host "`n[SUCCESS] GNI Stack is running!" -ForegroundColor Cyan
Write-Host "API Health:  http://localhost:8000/health" -ForegroundColor White
Write-Host "API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "Web Console: http://localhost:3000" -ForegroundColor White
Write-Host "`nPress Ctrl+C or stop processes to exit." -ForegroundColor Yellow

try {
    Wait-Process -Id $BackendProcess.Id, $FrontendProcess.Id
} finally {
    Stop-Process -Id $BackendProcess.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $FrontendProcess.Id -ErrorAction SilentlyContinue
}
