Write-Host "Starting RepSync Backend on http://localhost:8000 ..." -ForegroundColor Cyan
& .\.venv\Scripts\uvicorn.exe backend.app.main:app --host 0.0.0.0 --port 8000 --reload
