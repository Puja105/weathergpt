# WeatherGPT

WeatherGPT is a FastAPI weather-data service and multilingual weather assistant.
It combines live/forecast weather stored in PostgreSQL, an existing heavy-rain
classifier, and retrieval-augmented generation (RAG) over reference documents.

## 1. Requirements

- Python 3.10+
- Neon PostgreSQL project
- OpenAI API key (chat + embeddings)
- Existing weather tables populated by the project's ingestion scripts

## 2. Local setup

From the repository root:

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
# On macOS/Linux use: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:
- `DATABASE_URL`: Neon connection string. Include `sslmode=require`.
- `OPENAI_API_KEY`: your OpenAI API key.
- `OPENAI_MODEL`: defaults to `gpt-4o-mini`.
- `OPENAI_EMBEDDING_MODEL`: defaults to `text-embedding-3-small`.
- `FRONTEND_ORIGINS`: comma-separated frontend origins.

Never commit `.env`.

## 3. Prepare Neon RAG storage

Run once:

```bash
python -m backend.setup_rag
```

This enables the `vector` extension and creates `weather_documents` with
1536-dimensional embeddings and a cosine-similarity index. If your Neon role
cannot create the extension, enable `vector` from the Neon SQL Editor and rerun.

## 4. Add and ingest knowledge

Add trusted `.md`, `.txt`, or `.csv` reference documents to `knowledge_base/`.
Good sources include official IMD weather-warning guidance, NDMA preparedness
guides, and project-specific FAQs. Keep source URLs and document dates in the
document text.

Ingest:

```bash
python -m backend.ingest_documents --path knowledge_base
```

Re-running ingestion updates each source's chunks rather than duplicating them.
The initial `knowledge_base/README.md` is only an instruction file; add actual
reference documents for useful RAG results.

## 5. Start the API

```bash
uvicorn backend.main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive API docs: http://127.0.0.1:8000/docs
- Chat interface: http://127.0.0.1:8000/app
- Chat interface: http://127.0.0.1:8000/app

## 6. Chat API

`POST /chat`

Request:

```json
{
  "message": "Will it rain in Bengaluru tomorrow?",
  "history": []
}
```

Response:

```json
{
  "answer": "The answer generated from retrieved weather data and reference documents.",
  "sources": [
    {
      "title": "Example weather guidance",
      "source": "knowledge_base/example.md",
      "similarity": 0.72
    }
  ]
}
```

`history` is optional and accepts up to 12 prior `{ "role": "user" | "assistant",
"content": "..." }` messages. Send the latest user message in `message`.
The chatbot uses history to understand follow-up questions.

The chatbot:
1. Extracts city, date, forecast type, and response language.
2. Retrieves the matching current/hourly/daily weather from PostgreSQL.
3. Retrieves up to five semantically relevant knowledge chunks from Neon pgvector.
4. Generates an answer grounded in the retrieved weather data and reference docs.
5. Returns the document sources used.

If the RAG table is not yet set up, chat falls back to weather-data-only answers.
RAG retrieval starts working after steps 3 and 4 above.

## 7. Other existing endpoints

- `GET /`
- `GET /cities`
- `GET /locations`
- `GET /weather/current/{city}`
- `GET /forecast/hourly/{city}?hours=24`
- `GET /forecast/daily/{city}?days=7`
- `GET /forecast/{city}`
- `GET /weather/summary/{city}`
- `POST /chat`

## 8. Run tests

```bash
python -m unittest discover -s backend -p "test_*.py" -v
```

Tests that access live Neon/OpenAI services should use valid environment variables;
unit tests should mock external calls.

## Notes

- Weather facts must come from the project's weather tables/API, not RAG documents.
- RAG is for explanatory/reference knowledge (warnings, preparedness, weather-code
  explanations, and FAQs), not for making a live forecast.
- The heavy-rain model in `sahana/models/heavy_rain_model.pkl` is a current-risk
  estimate only; it must not be described as a future forecast or a calibrated
  probability.
- A responsive chat interface is included in `frontend/` and served at
  `http://127.0.0.1:8000/app` by FastAPI.
