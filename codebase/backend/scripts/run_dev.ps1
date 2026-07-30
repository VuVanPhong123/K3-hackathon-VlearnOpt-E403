$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $BackendDir

if (-not (Test-Path ".venv")) {
    & (Join-Path $ScriptDir "setup_venv.ps1")
}

.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
