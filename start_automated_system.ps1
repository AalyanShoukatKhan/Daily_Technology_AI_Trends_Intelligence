$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found. Run the README setup steps first." -ForegroundColor Yellow
    exit 1
}
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
& $Python -m database
Start-Process powershell -ArgumentList @("-NoExit", "-Command", "Set-Location '$ProjectDir'; & '$Python' app.py")
Start-Process powershell -ArgumentList @("-NoExit", "-Command", "Set-Location '$ProjectDir'; & '$Python' run_scheduler.py")
Write-Host "Started the dashboard and background scheduler in separate windows. Keep both windows open." -ForegroundColor Green
Write-Host "Dashboard: http://127.0.0.1:5000"
