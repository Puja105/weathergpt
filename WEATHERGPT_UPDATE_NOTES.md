# WeatherGPT update notes

## Regional-language response fix
- The language selected in the chat language dropdown is now sent to FastAPI as `preferred_language`.
- Selecting Kannada, Hindi, Tamil, Telugu, Marathi, Bengali, or Malayalam explicitly controls the response language.
- English keeps automatic language detection enabled.
- This also handles romanized input (for example, Kannada typed using English letters) because the selected language takes precedence over model language detection.
- The dropdown now indicates that it controls both voice input and response language.

## OpenRouter free-tier efficiency and resilience
- Chat completion output is capped (350 tokens for intent JSON, 700 for the final answer).
- Only the last four conversation messages are sent to the model, with each message limited to its last 600 characters.
- Routine city-specific current/daily/hourly weather requests skip vector embedding retrieval. RAG remains enabled for general knowledge and safety/reference questions.
- RAG retrieval failures (including temporary OpenRouter errors) no longer prevent an answer from being generated without retrieved references.
- HTTP 402 and 429 from OpenRouter are returned as meaningful API errors instead of being disguised as generic 502 errors.
- The frontend displays the backend's error detail and does not mark the API offline when the backend has responded.

## Notes
- The project still uses `OPENROUTER_MODEL` from the root `.env`; keep `openrouter/free` if you want OpenRouter to route among available free chat models.
- Free model availability and quotas are controlled by OpenRouter and individual providers. These changes reduce unnecessary requests and token usage but cannot remove provider-side limits.
