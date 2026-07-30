# VLearn Tutor Backend

FastAPI backend for the CP2 prototype. It stores uploaded PDFs locally, extracts text from one attached page, and calls OpenAI with Gemini fallback when API keys are configured.

## PowerShell

```powershell
cd be
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Bash/macOS/Linux

```bash
cd be
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Fill at least `OPENAI_API_KEY` or `GEMINI_API_KEY` in `.env` to enable chat. Do not commit `.env`.

Swagger: http://localhost:8000/docs
