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

## CP3 Backend

Upload now triggers local ingestion in `BackgroundTasks`: checksum, document status, page/block extraction with bounding boxes, section fallback, structured chunks, lexical search, dense embeddings, cached summaries, conversations, and bounded `/api/v2/chat` orchestration.

Key endpoints:

- `GET /api/documents/{id}/status`
- `POST /api/documents/{id}/reindex`
- `GET /api/documents/{id}/search?q=rag&top_k=6`
- `GET /api/documents/{id}/summary?type=short`
- `POST /api/v2/chat`
- `GET /api/conversations/{id}`
- `DELETE /api/conversations/{id}`

Runtime storage is ignored by git: `app/storage/index/vlearn.db`, `app/storage/model-cache`, and `app/storage/page-cache`. The old `/api/chat` endpoint remains available.

```powershell
python -m compileall app
pytest -q
python ..\eval\run_eval.py
```

No OCR engine is included yet. Visual-only pages are marked for vision fallback; production OCR is backlog.
