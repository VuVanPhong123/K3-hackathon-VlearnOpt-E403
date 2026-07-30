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
