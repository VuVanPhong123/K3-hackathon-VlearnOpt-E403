# VLearn Tutor Frontend

React/Vite frontend for the CP2 prototype.

## PowerShell

```powershell
cd fe
npm install
Copy-Item .env.example .env
npm run dev
```

## Bash/macOS/Linux

```bash
cd fe
npm install
cp .env.example .env
npm run dev
```

The frontend expects the backend at `VITE_API_BASE_URL`, defaulting to `http://localhost:8000`.

## CP3 Frontend

The chat panel now sends `/api/v2/chat` payloads with active page, dropped page attachment, selected text, drawn visual region, document-only/general-knowledge answer mode, conversation id, and citation chips that scroll back to cited pages.

`VITE_ENABLE_DEBUG_PANEL=true` enables a collapsible developer panel with intent, pages used, provider/model, latency and trace id. It does not display secrets or internal prompts.

```powershell
npm install
npm run build
npm test -- --run
```
