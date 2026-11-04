# WeatherGPT API Documentation

Base URL for local development: `http://127.0.0.1:8000`

Interactive Swagger documentation: `http://127.0.0.1:8000/docs`

## Health

### `GET /`

Returns a simple service message.

### `GET /health`

Lightweight health check used by the Vue frontend.

Example response:

```json
{
  "status": "ok",
  "service": "WeatherGPT API"
}
```

## Locations

### `GET /locations`

Returns location records, including coordinates.

### `GET /cities`

Returns the supported cities and their count. Current project locations include Bengaluru, Mumbai, Delhi, Chennai, and Hyderabad, depending on the database contents.

## Current weather

### `GET /weather/current/{city}`

Returns the latest stored current-weather record for a city.

Example: `GET /weather/current/Bengaluru`

Fields include city, state, country, recorded time, temperature, humidity, apparent temperature, precipitation, rain, weather code, cloud cover, wind speed, and wind direction.

## Forecasts

### `GET /forecast/hourly/{city}?hours=24`

Returns hourly forecast records. The backend validates the requested range; the documented maximum is 168 hours.

### `GET /forecast/daily/{city}?days=7`

Returns daily forecast records. The documented maximum is 7 days.

### `GET /forecast/{city}`

Returns combined hourly and daily forecast data.

### `GET /weather/summary/{city}`

Returns the latest current-weather record and the first available daily forecast record for the city.

## Chatbot

### `POST /chat`

The chatbot extracts the requested city/date/forecast type/language, retrieves weather data from PostgreSQL, optionally retrieves relevant reference chunks from pgvector, and generates a grounded answer through OpenRouter.

Request:

```json
{
  "message": "Will it rain in Bengaluru tomorrow?",
  "history": [
    { "role": "user", "content": "What's the weather in Bengaluru?" },
    { "role": "assistant", "content": "..." }
  ]
}
```

- `message`: required, 1–2,000 characters.
- `history`: optional; up to 12 previous messages, each with `role` (`user` or `assistant`) and `content`.

Response:

```json
{
  "answer": "The generated weather answer...",
  "sources": [
    {
      "title": "India weather guidance",
      "source": "knowledge_base/india_weather_warnings.md",
      "similarity": 0.72
    }
  ]
}
```

`similarity` is the vector-search similarity score for a retrieved reference chunk. Sources are omitted when no sufficiently relevant reference chunks are found. Weather facts continue to come from the weather tables, not from the reference documents.

## RAG setup

Configure `DATABASE_URL`, `OPENROUTER_API_KEY`, and (optionally) `OPENROUTER_EMBEDDING_MODEL` in the backend environment. Then run from the repository root:

```bash
python -m backend.setup_rag
python -m backend.ingest_documents --path knowledge_base
```

`RAG_MIN_SIMILARITY` controls the minimum cosine-similarity score returned to the chatbot; its default is `0.25`. Tune it based on observed retrieval quality for the selected embedding model. Re-ingest documents if the embedding model or vector dimensions change.

## Frontend integration

The Vue 3 + Vite frontend is located in `frontend/` and runs independently on `http://localhost:5173` during development. It calls:

- `GET /health` for the connection indicator.
- `POST /chat` for chatbot messages.

Set `VITE_API_BASE_URL` in `frontend/.env` to the backend base URL. Add the frontend's origin to the backend `FRONTEND_ORIGINS` environment variable. The frontend is not served by FastAPI; deploy its Vite `dist/` directory to a static hosting provider.

## Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL/Neon connection string |
| `OPENROUTER_API_KEY` | OpenRouter chat and embedding API key |
| `OPENROUTER_MODEL` | Chat model; defaults to `openrouter/free` |
| `OPENROUTER_EMBEDDING_MODEL` | Embedding model used for RAG |
| `RAG_MIN_SIMILARITY` | Minimum RAG similarity; defaults to `0.25` |
| `FRONTEND_ORIGINS` | Comma-separated allowed frontend origins |
| `VITE_API_BASE_URL` | Frontend-only backend URL; set in `frontend/.env` |

Never put database credentials or the OpenRouter API key in frontend variables.
