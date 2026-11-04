# WeatherGPT

WeatherGPT is an AI-powered weather assistant that combines live/project weather data, a language model, document retrieval (RAG), and a machine-learning rainfall-risk model to answer weather-related questions.

It is built with **FastAPI + PostgreSQL/Neon** on the backend and **Vue 3 + Vite** on the frontend. The language model is accessed through **OpenRouter**.

> **Project status:** The local Vue frontend has been connected successfully to the FastAPI `/chat` endpoint. This README explains how to install, configure, run, test, and hand over the project.

---

## Contents

- [Features](#features)
- [How WeatherGPT works](#how-weathergpt-works)
- [Technology stack](#technology-stack)
- [Project structure](#project-structure)
- [Prerequisites and downloads](#prerequisites-and-downloads)
- [Configuration](#configuration)
- [Backend setup and run](#backend-setup-and-run)
- [Frontend setup and run](#frontend-setup-and-run)
- [Using the API](#using-the-api)
- [Example questions and test cases](#example-questions-and-test-cases)
- [Weather data, RAG, and the ML model](#weather-data-rag-and-the-ml-model)
- [Troubleshooting](#troubleshooting)
- [Deployment handoff](#deployment-handoff)
- [Security notes](#security-notes)

---

## Features

### Weather questions and forecasts

WeatherGPT supports weather-related questions such as:

- Current weather for a supported city.
- Daily forecasts, including expected rainfall.
- Hourly forecasts.
- Questions about more than one city.
- Rainfall and precipitation comparisons across cities when the required daily data is available.
- General weather explanations, such as why cyclones form.
- Weather safety and preparedness questions.

The assistant uses weather records from the project's database for current conditions and forecasts. It should not invent weather values when data is unavailable.

### Weather explanations and safety guidance

- Retrieves relevant material from the project's weather knowledge base.
- Uses retrieved documents to support explanations about weather warnings and safety.
- Can return source references with an answer.
- Restricts the assistant to weather-related topics.

### Rainfall comparison

For supported multi-city daily forecast questions, WeatherGPT can calculate:

- Highest rainfall amount.
- Lowest rainfall amount (including ties).
- Average rainfall across cities with available data.
- Number of cities included in the comparison.

If some requested cities do not have usable data, the comparison may be incomplete. A comparison based on only one available city cannot establish a meaningful highest-versus-lowest comparison.

### Heavy-rain risk estimation

The backend includes a Random Forest model for estimating current heavy-rain risk. Its input features include:

- Temperature
- Humidity
- Cloud cover
- Wind speed
- Previous-rain indicator
- Month
- Hour

The model is used by the backend when the request asks for heavy-rain risk and the required current weather inputs are available. Its output is a model estimate, **not a calibrated probability or an official weather warning**.

### Chat interface

The Vue frontend provides:

- Chat-style user and assistant messages.
- Conversation history sent with follow-up questions.
- Suggested questions.
- Loading and error states.
- Retrieved source display.
- A new-chat action.
- A backend availability indicator.

---

## How WeatherGPT works

At a high level:

1. The user enters a weather question in the Vue interface.
2. Vue sends the question and recent conversation history to the FastAPI `POST /chat` endpoint.
3. The backend uses the language model through OpenRouter to understand the request.
4. For weather-data questions, the backend retrieves the relevant city and forecast/current-weather records from PostgreSQL.
5. For explanatory or safety questions, the backend retrieves relevant knowledge-base passages using embeddings and pgvector.
6. If requested and applicable, the backend calls the Random Forest heavy-rain model.
7. The language model generates a response using the available weather context and relevant retrieved material.
8. FastAPI returns the answer and source references to the frontend.

**Important distinction:** OpenRouter provides language-model and embedding access. It is not the source of the project's measured weather records, and it does not replace the Random Forest model.

---

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | Vue 3, Vite, JavaScript, HTML, CSS |
| Backend/API | Python, FastAPI, Uvicorn |
| Database | PostgreSQL / Neon |
| Language model | OpenRouter |
| Retrieval | Embeddings, pgvector, cosine-similarity search |
| Machine learning | scikit-learn, Random Forest |
| API communication | HTTP, JSON, Fetch API |

---

## Project structure

The repository contains the following main areas (some supporting files may differ as the project evolves):

```text
weathergpt/
├── backend/                 # FastAPI routes and backend logic
│   ├── main.py              # FastAPI application and CORS configuration
│   ├── chatbot.py           # Chat endpoint, intent handling and response generation
│   ├── database.py          # Database connection
│   ├── rag.py               # Document retrieval
│   ├── rain_risk.py         # Heavy-rain risk model integration
│   ├── setup_rag.py         # RAG database setup
│   └── ingest_documents.py  # Knowledge-base ingestion
├── frontend/                # Vue 3 + Vite application
│   ├── src/
│   │   ├── components/
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── assets/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── knowledge_base/          # Weather safety and reference documents
├── data/                    # Project data and/or model assets
├── sql/                     # Database SQL scripts, if present
├── requirements.txt         # Python dependencies
├── API_DOCUMENTATION.md     # API reference
└── README.md
```

The trained model file (for example, `heavy_rain_model.pkl`) must remain at the path expected by `backend/rain_risk.py`. Do not rename or move it without updating the loading path.

---

## Prerequisites and downloads

Install these tools before setting up the project:

1. **Python 3.10 or later**  
   Download: https://www.python.org/downloads/  
   During Windows installation, enable **Add Python to PATH**.

2. **Node.js LTS (includes npm)**  
   Download: https://nodejs.org/  
   Verify installation:
   ```bash
   node --version
   npm --version
   ```

3. **Git**  
   Download: https://git-scm.com/downloads  
   Verify:
   ```bash
   git --version
   ```

4. **Visual Studio Code (recommended)**  
   Download: https://code.visualstudio.com/

5. **PostgreSQL database**  
   The project has been configured to use PostgreSQL and can use a hosted Neon PostgreSQL database.  
   Neon: https://neon.tech/  
   Create a database/project and obtain its PostgreSQL connection string. Ensure the database has the extensions and schema required by the SQL setup scripts.

6. **OpenRouter account and API key**  
   Website: https://openrouter.ai/  
   Create an API key and select/configure the chat and embedding models used by the project.

You do not need to install PostgreSQL locally if you are using the configured hosted Neon database.

---

## Configuration

There are two separate environment files:

- Root `.env`: backend secrets and backend configuration.
- `frontend/.env`: public frontend configuration only.

Never put an OpenRouter API key or database password in the frontend environment file.

### 1. Backend environment

Create a file named `.env` in the **project root**, alongside `requirements.txt`.

Add the required variables (use the actual values for your project):

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require

OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openrouter/free
OPENROUTER_EMBEDDING_MODEL=nvidia/nemotron-3.5-embed-1b:free

FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Notes:

- `DATABASE_URL` must be the actual PostgreSQL/Neon connection string. Do not leave placeholder values such as `HOST`, `USER`, or `PASSWORD`.
- `OPENROUTER_API_KEY` is secret. Keep it only on the backend.
- `OPENROUTER_MODEL` selects the chat model. The default shown here is `openrouter/free`; change it only if the backend configuration and your OpenRouter account require a different model.
- `OPENROUTER_EMBEDDING_MODEL` selects the embedding model used for document ingestion and retrieval. Use the same embedding model for ingestion and later queries.
- `FRONTEND_ORIGINS` is a comma-separated list of frontend origins allowed by FastAPI CORS. Add the exact deployed frontend origin when deploying.

If the project already has a working root `.env`, preserve its actual values. Do not overwrite it with this example.

### 2. Frontend environment

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

This is the base URL of the FastAPI server. It is not a secret.

If the frontend is opened using a different host (for example, a LAN IP such as `http://192.168.x.x:5173`), configure the API URL and backend CORS origins to match that setup. For a normal same-computer local setup, use the localhost configuration above.

Restart the Vite development server after changing frontend environment variables.

---

## Backend setup and run

Run these commands from the **project root** (the outer `weathergpt` directory).

### 1. Open the project

```bash
cd path/to/weathergpt
```

### 2. Create a Python virtual environment

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If the project already has a virtual environment, activate that one instead of creating another.

### 3. Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure the database

- Make sure the root `.env` contains the valid `DATABASE_URL`.
- Ensure the database schema required by the backend has been created using the SQL scripts supplied in the repository.
- Confirm that the weather tables contain data for the cities you want to test.
- Confirm that the database connection works before debugging chatbot or frontend behavior.

The exact weather-data ingestion/scheduling process depends on the ingestion scripts and automation configured in the repository. Do not assume that starting FastAPI automatically downloads or refreshes weather data.

### 5. Set up the RAG database objects

From the project root, with the virtual environment active:

```bash
python -m backend.setup_rag
```

This prepares the RAG database objects, including the document storage/vector-search setup used by the project.

### 6. Ingest knowledge-base documents

```bash
python -m backend.ingest_documents --path knowledge_base
```

The project's initial ingestion run stored four knowledge-base files as seven chunks with 1536-dimensional embeddings in Neon. The documents included:

- Flood Safety India
- IMD Warning Levels
- India Weather Warnings
- The knowledge-base README

Run ingestion again when you add or update knowledge-base documents. Avoid repeatedly ingesting unchanged files unless the ingestion script is designed to handle duplicates/upserts.

### 7. Start FastAPI

```bash
uvicorn backend.main:app --reload
```

The API should be available at:

- API base: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

Keep this terminal open while using the frontend.

If you need to access the development server from another device on your local network, start it with:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Only do this on a trusted network. Configure the frontend API URL and CORS origin for the actual LAN address.

---

## Frontend setup and run

Open a **second terminal**. The backend terminal should remain running.

### 1. Move into the frontend directory

```bash
cd frontend
```

### 2. Install JavaScript dependencies

```bash
npm install
```

### 3. Configure the frontend API URL

Create `frontend/.env` if it does not exist:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 4. Start the Vue development server

```bash
npm run dev
```

Vite prints a local URL, usually:

http://localhost:5173

Open that URL in your browser.

### 5. Run both servers during development

You need two terminals:

| Terminal | Directory | Command |
|---|---|---|
| Backend | Project root | `uvicorn backend.main:app --reload` |
| Frontend | `frontend/` | `npm run dev` |

To stop either server, press `Ctrl + C` in its terminal.

### 6. Build the frontend for production

From `frontend/`:

```bash
npm run build
```

Vite generates the production frontend in:

```text
frontend/dist/
```

Preview the production build locally with:

```bash
npm run preview
```

---

## Using the API

### Health check

```http
GET /health
```

Use this endpoint to check whether the API process is responding. A successful health check does not by itself prove that the database, OpenRouter, RAG retrieval, or `/chat` endpoint is working.

### Chat endpoint

```http
POST /chat
Content-Type: application/json
```

Example request:

```json
{
  "message": "What's the current weather in Bengaluru?",
  "history": []
}
```

Example response shape:

```json
{
  "answer": "The current weather in Bengaluru is ...",
  "sources": [
    {
      "title": "Example reference title",
      "source": "Example source",
      "similarity": 0.68
    }
  ]
}
```

The actual answer, source list, and similarity values depend on the available weather data and retrieved documents.

### Conversation history

The frontend sends recent messages as a list of objects:

```json
[
  {
    "role": "user",
    "content": "What's the weather in Bengaluru?"
  },
  {
    "role": "assistant",
    "content": "..."
  }
]
```

The supported roles are `user` and `assistant`. The backend request model limits message content to 2,000 characters and conversation history to 12 messages.

For the complete endpoint details, see [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md) and the live Swagger UI at `/docs`.

---

## Example questions and test cases

Try these from the frontend or Swagger UI.

### Current conditions

```text
What's the current weather in Bengaluru?
What's the weather like in Bangalore?
```

Expected behavior:

- Recognizes Bengaluru/Bangalore as the requested city, if it exists in the database.
- Returns available current conditions such as temperature, feels-like temperature, humidity, cloud cover, precipitation/rain, and wind.
- Clearly reports unavailable data instead of inventing values.

### Daily forecast and rainfall

```text
How much rainfall is expected in Bengaluru tomorrow?
Will it rain in Mumbai tomorrow?
```

Expected behavior:

- Uses the daily forecast for the requested date.
- Reports rainfall in millimetres when the required field is available.
- Classifies daily rainfall using the categories implemented by the backend.

### Hourly forecast

```text
Show me the hourly forecast for Bengaluru.
What will the weather be like in Mumbai at 6 PM?
```

Expected behavior:

- Uses hourly forecast records when available.
- Reports the available hourly fields for the selected city/time.
- If a requested time or data point is unavailable, the assistant should say so.

### Multi-city comparison

```text
Compare precipitation in Bengaluru and Mumbai tomorrow.
Compare rainfall in Bengaluru, Mumbai, and Delhi tomorrow.
```

Expected behavior:

- Compares cities for which usable daily data is available.
- Reports highest and lowest values, ties, and average when a meaningful comparison can be calculated.
- Identifies when requested cities are unsupported or missing data.
- Distinguishes **rain** from **precipitation**. Precipitation can include forms other than rain.

### Weather explanations

```text
Why do cyclones form?
What is the difference between a cyclone and a depression?
```

Expected behavior:

- Gives a general weather explanation.
- Uses relevant knowledge-base material when retrieval finds suitable documents.
- Does not treat unrelated safety documents as evidence for an unrelated explanation.

### Weather safety

```text
What precautions should people take during flooding?
What does an IMD orange warning mean?
What should people do during an extremely heavy rainfall warning?
```

Expected behavior:

- Uses relevant retrieved safety/warning references when available.
- Includes source references when relevant documents are retrieved.
- Encourages users to follow official alerts and local authorities during severe weather.

### Heavy-rain risk

```text
Is there a heavy-rain risk in Bengaluru right now?
```

Expected behavior:

- Requests the heavy-rain risk estimate when supported by the intent and current weather context.
- Uses the Random Forest model and its available input features.
- Treats the result as a model estimate, not an official warning or guaranteed probability.

### Out-of-scope question

```text
What is binary search?
```

Expected behavior:

- Politely explains that WeatherGPT is restricted to weather-related topics.

### Unsupported city

```text
What's the weather in a city that is not in the database?
```

Expected behavior:

- Reports that the city is not currently supported or that data is unavailable.
- Does not silently substitute another city.

---

## Weather data, RAG, and the ML model

### Weather database

The backend reads current and forecast information from the configured PostgreSQL database. The database must be populated by the project's weather-data ingestion process before live/current or forecast questions can return useful results.

WeatherGPT does not automatically fetch fresh weather data merely because the frontend or FastAPI server has started.

### Retrieval-Augmented Generation (RAG)

RAG provides reference material to the language model:

1. Documents are read from `knowledge_base/`.
2. Documents are split into chunks.
3. The configured OpenRouter embedding model converts chunks into vectors.
4. Chunks and embeddings are stored in PostgreSQL using pgvector.
5. A question is embedded and compared with stored vectors.
6. Relevant passages are supplied to the language model as supporting context.

The initial Neon setup used 1536-dimensional embeddings and a vector index. Retrieval relevance filtering and duplicate removal are applied in the chatbot retrieval flow. A retrieved passage is reference material, not an instruction and not a substitute for database weather measurements.

### Random Forest heavy-rain model

The project includes a trained Random Forest model loaded by the backend's rain-risk module. The model uses weather/time features to estimate heavy-rain risk.

Keep the model artifact available at the path expected by the backend. If the model file is missing or incompatible, the ML risk feature may fail even if ordinary chat and forecast requests work.

---

## Troubleshooting

### Frontend says “Failed to fetch”

Check the following:

1. Is FastAPI running?
2. Does http://127.0.0.1:8000/docs open?
3. Does `frontend/.env` contain the correct API URL?
   ```env
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```
4. Does root `.env` include the frontend origin?
   ```env
   FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
   ```
5. Did you restart Vite after changing `frontend/.env`?
6. Did you restart FastAPI after changing backend `.env`?
7. Check the browser Developer Tools → Console and Network tabs for the actual failed request.

If the frontend is opened at a LAN address such as `http://192.168.x.x:5173`, use a reachable backend address instead of `127.0.0.1`, and add the exact frontend origin to `FRONTEND_ORIGINS`. `127.0.0.1` always refers to the device making the request.

### API says OpenRouter key is missing or invalid

- Check `OPENROUTER_API_KEY` in the root `.env`.
- Make sure the key has not been placed in `frontend/.env`.
- Restart FastAPI after editing the root `.env`.
- Check the OpenRouter account/key and selected model configuration.

### Database connection error

- Check `DATABASE_URL` in the root `.env`.
- Use the full Neon/PostgreSQL connection string, including the correct host, database, username, password, and SSL setting required by the provider.
- Confirm the database is active and accessible.
- Confirm the required tables and extensions have been created.
- Confirm the weather tables contain records for the requested city/date.

### No RAG sources appear

- Confirm the files exist in `knowledge_base/`.
- Run the RAG setup and document ingestion commands.
- Check that the embedding model and API key are configured.
- Check the backend logs for database, embedding, or retrieval errors.
- A source list may legitimately be empty when no sufficiently relevant reference document is found.

### Frontend changes or environment changes are not appearing

- Save the files.
- Restart Vite after changing environment variables.
- Refresh the browser.
- If dependency installation is incomplete, run `npm install` inside `frontend/`.

### Port already in use

If port 8000 or 5173 is already occupied, stop the other process or configure a different port. If you change the backend port, update `VITE_API_BASE_URL` accordingly.

---

## Deployment handoff

The frontend and backend are separate applications and can be deployed independently.

### Backend deployment

The backend host needs:

- A supported Python runtime.
- Dependencies from `requirements.txt`.
- The backend source code and required model artifact.
- A reachable PostgreSQL/Neon database.
- Backend environment variables (`DATABASE_URL`, OpenRouter key/model settings, and allowed frontend origins).
- A start command appropriate for the hosting provider, for example:
  ```bash
  uvicorn backend.main:app --host 0.0.0.0 --port $PORT
  ```

The exact start command and port variable may need adjustment for the chosen host.

### Frontend deployment

1. Set `VITE_API_BASE_URL` to the deployed backend's HTTPS base URL in the frontend hosting provider's environment settings.
2. Build the Vue application:
   ```bash
   npm install
   npm run build
   ```
3. Deploy the generated `frontend/dist/` directory using a static hosting provider.
4. Add the deployed frontend origin to the backend's `FRONTEND_ORIGINS`.
5. Redeploy/restart the backend after changing CORS configuration.

Vite variables prefixed with `VITE_` are included in the browser bundle. They must never contain secrets.

### Local development versus production

| Setting | Local development | Production |
|---|---|---|
| Frontend URL | `http://localhost:5173` | Deployed frontend HTTPS URL |
| Backend URL | `http://127.0.0.1:8000` | Deployed backend HTTPS URL |
| API key | Root backend `.env` | Backend host secret/environment setting |
| Database URL | Root backend `.env` | Backend host secret/environment setting |
| CORS | Local Vite origin(s) | Exact deployed frontend origin |

---

## Security notes

- Never commit `.env` files, API keys, database passwords, or other secrets.
- Keep OpenRouter credentials on the backend only.
- Keep `frontend/.env` limited to non-secret public configuration such as the API base URL.
- Do not expose a development server to an untrusted network.
- Use HTTPS for deployed frontend and backend communication.
- Restrict production CORS to the actual frontend domain rather than allowing every origin.
- Do not commit `.venv/`, `node_modules/`, or generated build output unless the project specifically requires it.

---

## Team handoff

Suggested ownership split:

- **Backend/AI:** FastAPI routes, intent handling, database queries, OpenRouter integration, RAG, rainfall comparison, and Random Forest integration.
- **Frontend/UI:** Vue components, styling, responsive layout, chat experience, and frontend deployment.
- **Integration/deployment:** Environment variables, CORS, API URL configuration, end-to-end testing, and production deployment.

Useful files for the next developer:

- `backend/chatbot.py` — chatbot request flow and response generation.
- `backend/rag.py` — retrieval logic.
- `backend/rain_risk.py` — heavy-rain model integration.
- `backend/main.py` — FastAPI app, router registration, CORS, and health endpoint.
- `frontend/src/App.vue` — main chat interface.
- `frontend/src/components/` — reusable Vue components.
- `API_DOCUMENTATION.md` — API reference.

---

## License

Add the license selected by the project team before distributing the project publicly.
