# WeatherGPT knowledge base

Place trusted weather reference documents in this folder (`.md`, `.txt`, or `.csv`).
Examples include official IMD warning guidance, disaster-management preparedness
documents, weather-code explanations, and project-specific FAQs.

Use documents you have permission to use. Keep the source URL and publication/update
date in each document so WeatherGPT can show provenance. Avoid treating general
reference documents as live forecasts; live conditions and forecasts come from the
weather tables/API.

After adding documents, run:

```bash
python -m backend.setup_rag
python -m backend.ingest_documents --path knowledge_base
```
