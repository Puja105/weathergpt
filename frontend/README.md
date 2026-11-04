# WeatherGPT frontend (Vue 3 + Vite)

This is the Vue 3 starter frontend for WeatherGPT. It is intentionally kept separate from FastAPI so the frontend can be developed and deployed independently.

## Requirements

- Node.js 18+ (Node 20+ recommended)
- npm
- WeatherGPT FastAPI backend running

## Run locally

From this directory:

```bash
npm install
cp .env.example .env
npm run dev
```

On Windows PowerShell, copy the environment template with:

```powershell
Copy-Item .env.example .env
```

Open http://localhost:5173. The default API URL is `http://127.0.0.1:8000`.

## Configure the backend URL

Set `VITE_API_BASE_URL` in `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

For deployment, use the public HTTPS URL of the deployed FastAPI backend. Do not put API keys or database credentials in frontend environment variables; Vite variables are exposed to the browser.

## API contract used by this UI

`POST /chat`

```json
{
  "message": "Will it rain in Bengaluru tomorrow?",
  "history": [
    { "role": "user", "content": "What's the weather in Bengaluru?" },
    { "role": "assistant", "content": "..." }
  ]
}
```

The UI expects `{ "answer": "...", "sources": [{ "title": "...", "source": "...", "similarity": 0.7 }] }`.

`GET /health` is used for the small API connection indicator.

## Build for deployment

```bash
npm run build
npm run preview
```

The production files are generated in `dist/`. Deploy that directory using a static frontend host such as Vercel, Netlify, or Cloudflare Pages. Set `VITE_API_BASE_URL` in the host's environment-variable settings and rebuild.

The backend must allow the deployed frontend origin in its `FRONTEND_ORIGINS` environment variable. Example:

```env
FRONTEND_ORIGINS=http://localhost:5173,https://your-frontend-domain.example
```

## Project structure

```text
frontend/
├── src/
│   ├── assets/styles.css       # Global responsive styling
│   ├── components/
│   │   └── ChatMessage.vue     # User/assistant message and sources
│   ├── App.vue                 # Chat screen, API calls, conversation state
│   └── main.js                 # Vue application entry point
├── .env.example
├── index.html
├── package.json
└── vite.config.js
```

## Suggested next frontend tasks

- Add forecast cards using the existing `/weather/summary/{city}` and `/forecast/{city}` endpoints.
- Add hourly/daily charts.
- Add language selection and voice input/output.
- Add a map view for supported locations.
- Add proper markdown rendering if the backend is updated to return formatted answers safely.
