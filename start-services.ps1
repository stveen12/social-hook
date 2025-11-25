

Write-Host "🚀 Starting Social Hook Services..." -ForegroundColor Green

if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "   Virtual environment not found. Please create it first:" -ForegroundColor Red
    Write-Host "   python -m venv venv" -ForegroundColor Yellow
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "   pip install -r requirement.txt" -ForegroundColor Yellow
    exit 1
}

function Start-Service {
    param(
        [string]$ServiceName,
        [string]$ScriptPath,
        [int]$Port
    )
    
    Write-Host "Starting $ServiceName on port $Port..." -ForegroundColor Cyan
    
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$PWD'; .\venv\Scripts\Activate.ps1; python $ScriptPath"
    ) -WindowStyle Normal
    
    Start-Sleep -Seconds 2
}

Start-Service -ServiceName "GitHub Scraper" -ScriptPath "github.py" -Port 5000
Start-Service -ServiceName "Instagram Scraper" -ScriptPath "instagram.py" -Port 5001
Start-Service -ServiceName "Twitter Scraper" -ScriptPath "xtwitter.py" -Port 5003
Start-Service -ServiceName "Handler" -ScriptPath "handler.py" -Port 8000

Write-Host ""
Write-Host "✅ All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "Services running on:" -ForegroundColor Yellow
Write-Host "  📦 GitHub:    http://localhost:5000" -ForegroundColor White
Write-Host "  📷 Instagram: http://localhost:5001" -ForegroundColor White
Write-Host "  🐦 Twitter:   http://localhost:5003" -ForegroundColor White
Write-Host "  🎯 Handler:   http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "Check health: curl http://localhost:8000/sanity" -ForegroundColor Cyan
Write-Host ""
