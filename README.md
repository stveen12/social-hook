# Social Hook - PowerShell Scripts Usage

## Start All Services

Run all scraper services in separate windows:

```powershell
.\start-services.ps1
```

This will start:
- GitHub Scraper (port 5000)
- Instagram Scraper (port 5001)
- Twitter Scraper (port 5003)
- Handler (port 8000)

Each service runs in its own PowerShell window, making it easy to monitor logs individually.

## Prerequisites

1. Virtual environment must be created:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirement.txt
   ```

2. Credentials files must be in `credentials/` directory (Call /login on each service to login)

## Health Check

After starting services, verify they're running:

```powershell
curl http://localhost:8000/sanity
```

## Individual Service Management

To run a single service manually:

```powershell
.\venv\Scripts\Activate.ps1
python github.py      # or instagram.py, linkedin.py, xtwitter.py, handler.py
```
