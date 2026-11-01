import json
import logging
import os
from datetime import date as Date, datetime
from typing import Literal, Optional
from zoneinfo import ZoneInfo

import psycopg2
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError

from backend.database import get_connection
from backend.rain_risk import estimate_heavy_rain


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chatbot"])
WEATHER_TIMEZONE = ZoneInfo("Asia/Kolkata")
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str


class WeatherIntent(BaseModel):
    city: Optional[str] = None
    date: Optional[Date] = None
    query_type: Literal["current", "daily", "hourly"] = "current"
    language: str = "English"
    include_heavy_rain_risk: bool = False


def _request_openai(messages: list[dict[str, str]], json_response: bool = False) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Chatbot is not configured. Set OPENAI_API_KEY in the environment.",
        )

    payload: dict[str, object] = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": messages,
        "temperature": 0.2,
    }
    if json_response:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(
            OPENAI_CHAT_COMPLETIONS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as error:
        logger.exception("OpenAI request failed")
        raise HTTPException(
            status_code=502,
            detail="The language model could not be reached. Please try again.",
        ) from error

    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        logger.error("OpenAI returned an unexpected response structure")
        raise HTTPException(
            status_code=502,
            detail="The language model returned an invalid response.",
        ) from error

    if not isinstance(content, str) or not content.strip():
        raise HTTPException(
            status_code=502,
            detail="The language model returned an empty response.",
        )
    return content


def _understand_question(message: str) -> WeatherIntent:
    today = datetime.now(WEATHER_TIMEZONE).date().isoformat()
    content = _request_openai(
        [
            {
                "role": "system",
                "content": (
                    "Extract weather request details from the user's message. "
                    "Return JSON with city (a city name only, or null if absent), "
                    "date (YYYY-MM-DD or null), query_type (current, daily, or hourly), "
                    "language (the language to use in the answer), and "
                    "include_heavy_rain_risk (true only when the user asks about "
                    "current heavy-rain risk, never for a future forecast). "
                    f"Resolve relative dates using today's date: {today}. "
                    "Choose current for present conditions, hourly when a time of day "
                    "or hourly trend is requested, and daily for a date or daily outlook. "
                    "Do not infer a city that the user did not specify."
                ),
            },
            {"role": "user", "content": message},
        ],
        json_response=True,
    )

    try:
        return WeatherIntent.model_validate_json(content)
    except ValidationError as error:
        logger.exception("OpenAI returned invalid weather request details")
        raise HTTPException(
            status_code=502,
            detail="The language model could not understand the weather request.",
        ) from error


def _get_weather_context(intent: WeatherIntent) -> dict[str, object]:
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT location_id, city, state, country
            FROM locations
            ORDER BY city, state, country;
            """
        )
        locations = cursor.fetchall()

        if not intent.city:
            return {"available_locations": locations}

        matches = [
            location
            for location in locations
            if location[1].casefold() == intent.city.casefold()
        ]
        if not matches:
            return {
                "requested_city": intent.city,
                "error": "Location was not found.",
                "available_locations": locations,
            }
        if len(matches) > 1:
            return {
                "requested_city": intent.city,
                "error": "More than one location has this city name.",
                "matching_locations": matches,
            }

        location_id, city, state, country = matches[0]
        requested_date = intent.date or datetime.now(WEATHER_TIMEZONE).date()
        location = {"city": city, "state": state, "country": country}

        if intent.query_type == "current":
            cursor.execute(
                """
                SELECT recorded_at, temperature_c, humidity_percent,
                       apparent_temperature_c, precipitation_mm, rain_mm,
                       weather_code, cloud_cover_percent, wind_speed_kmh,
                       wind_direction_degree
                FROM weather_data
                WHERE location_id = %s
                ORDER BY recorded_at DESC
                LIMIT 1;
                """,
                (location_id,),
            )
            row = cursor.fetchone()
            columns = (
                "recorded_at", "temperature_c", "humidity_percent",
                "apparent_temperature_c", "precipitation_mm", "rain_mm",
                "weather_code", "cloud_cover_percent", "wind_speed_kmh",
                "wind_direction_degree",
            )
            weather = dict(zip(columns, row)) if row else None
            context = {
                "location": location,
                "query_type": intent.query_type,
                "requested_date": requested_date.isoformat(),
                "weather": weather,
            }
            if intent.include_heavy_rain_risk and weather is not None:
                cursor.execute(
                    """
                    SELECT rain_mm
                    FROM weather_data
                    WHERE location_id = %s AND recorded_at < %s
                    ORDER BY recorded_at DESC
                    LIMIT 1;
                    """,
                    (location_id, row[0]),
                )
                previous_row = cursor.fetchone()
                recorded_at = row[0]
                if not isinstance(recorded_at, datetime):
                    raise HTTPException(
                        status_code=503,
                        detail="Weather timestamps are unavailable for rain-risk analysis.",
                    )
                context["heavy_rain_model_estimate"] = estimate_heavy_rain(
                    temperature=row[1],
                    humidity=row[2],
                    cloud_cover=row[7],
                    wind_speed=row[8],
                    previous_rain=(
                        previous_row[0]
                        if previous_row and previous_row[0] is not None
                        else 0.0
                    ),
                    month=recorded_at.month,
                    hour=recorded_at.hour,
                )
            return context
        elif intent.query_type == "hourly":
            cursor.execute(
                """
                SELECT forecast_time, temperature_c, humidity_percent,
                       precipitation_mm, rain_mm, weather_code,
                       wind_speed_kmh, wind_direction_degree
                FROM hourly_forecast
                WHERE location_id = %s AND forecast_time::date = %s
                ORDER BY forecast_time
                LIMIT 24;
                """,
                (location_id, requested_date),
            )
            rows = cursor.fetchall()
            return {
                "location": location,
                "query_type": intent.query_type,
                "requested_date": requested_date.isoformat(),
                "weather": [
                    dict(
                        zip(
                            (
                                "forecast_time", "temperature_c",
                                "humidity_percent", "precipitation_mm",
                                "rain_mm", "weather_code", "wind_speed_kmh",
                                "wind_direction_degree",
                            ),
                            row,
                        )
                    )
                    for row in rows
                ],
            }
        else:
            cursor.execute(
                """
                SELECT forecast_date, temperature_max_c, temperature_min_c,
                       apparent_temperature_max_c, apparent_temperature_min_c,
                       precipitation_sum_mm, rain_sum_mm, weather_code
                FROM daily_forecast
                WHERE location_id = %s AND forecast_date = %s
                LIMIT 1;
                """,
                (location_id, requested_date),
            )
            row = cursor.fetchone()
            columns = (
                "forecast_date", "temperature_max_c", "temperature_min_c",
                "apparent_temperature_max_c", "apparent_temperature_min_c",
                "precipitation_sum_mm", "rain_sum_mm", "weather_code",
            )

        return {
            "location": location,
            "query_type": intent.query_type,
            "requested_date": requested_date.isoformat(),
            "weather": dict(zip(columns, row)) if row else None,
        }
    except psycopg2.Error as error:
        logger.exception("Weather database query failed")
        raise HTTPException(
            status_code=503,
            detail="Weather data is temporarily unavailable.",
        ) from error
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def _generate_answer(message: str, intent: WeatherIntent, weather_context: dict[str, object]) -> str:
    today = datetime.now(WEATHER_TIMEZONE).date().isoformat()
    content = _request_openai(
        [
            {
                "role": "system",
                "content": (
                    "You are WeatherGPT, a helpful multilingual weather assistant. "
                    "Answer in the language requested below. Today's date is "
                    f"{today}. Use only the supplied weather data; never invent "
                    "weather values or claim a forecast exists when it is missing. "
                    "If the city is missing, ask the user for it. If the city is not "
                    "available, explain that and offer the available locations. "
                    "If several matching locations are returned, ask which one they mean. "
                    "A heavy_rain_model_estimate describes current risk only; never "
                    "present it as a future forecast or treat it as measured weather. "
                    "Its score is not a calibrated chance or percentage. "
                    "Use Celsius, millimeters, percent, and km/h as supplied. Be concise."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question": message,
                        "answer_language": intent.language,
                        "weather_context": weather_context,
                    },
                    default=str,
                    ensure_ascii=False,
                ),
            },
        ]
    )
    return content.strip()


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    intent = _understand_question(request.message)
    weather_context = _get_weather_context(intent)
    answer = _generate_answer(request.message, intent, weather_context)
    return ChatResponse(answer=answer)
