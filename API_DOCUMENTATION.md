# WeatherGPT API Documentation

## 1. Overview

This API provides weather information for the WeatherGPT project.

The API retrieves weather data stored in PostgreSQL and makes it available through FastAPI endpoints.

---

## 2. Base URL

When running locally:

http://127.0.0.1:8000

Swagger API documentation:

http://127.0.0.1:8000/docs

---

# 3. Available Endpoints

## 3.1 Root

### Endpoint

GET /

### Purpose

Checks whether the WeatherGPT API is running.

### Example

GET http://127.0.0.1:8000/

### Example Response

{
    "message": "WeatherGPT API is running"
}

---

# 4. Cities

## Endpoint

GET /cities

### Purpose

Returns the list of supported cities.

### Example

GET http://127.0.0.1:8000/cities

### Example Response

[
    {
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India"
    },
    {
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India"
    },
    {
        "city": "Delhi",
        "state": "Delhi",
        "country": "India"
    },
    {
        "city": "Chennai",
        "state": "Tamil Nadu",
        "country": "India"
    },
    {
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India"
    }
]

---

# 5. Current Weather

## Endpoint

GET /weather/current/{city}

### Purpose

Returns the latest weather data available for a city.

### Example

GET /weather/current/Bengaluru

### Full URL

http://127.0.0.1:8000/weather/current/Bengaluru

### Example Response

{
    "city": "Bengaluru",
    "state": "Karnataka",
    "country": "India",
    "recorded_at": "...",
    "temperature_c": 25.0,
    "humidity_percent": 70,
    "apparent_temperature_c": 26.0,
    "precipitation_mm": 0.0,
    "rain_mm": 0.0,
    "weather_code": 1,
    "cloud_cover_percent": 20,
    "wind_speed_kmh": 10.0,
    "wind_direction_degree": 180
}

### Useful for

- Chatbot
- Frontend
- Current weather cards
- Voice assistant
- Weather summaries

---

# 6. Hourly Forecast

## Endpoint

GET /forecast/hourly/{city}

### Purpose

Returns hourly weather forecast data.

### Default

24 hours

### Example

GET /forecast/hourly/Bengaluru

### Custom number of hours

GET /forecast/hourly/Bengaluru?hours=48

### Maximum

168 hours

### Example response structure

[
    {
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "forecast_time": "...",
        "temperature_c": 25.0,
        "humidity_percent": 70,
        "precipitation_mm": 0.0,
        "rain_mm": 0.0,
        "weather_code": 1,
        "wind_speed_kmh": 10.0,
        "wind_direction_degree": 180
    }
]

### Useful for

- Hourly forecast charts
- Rain prediction
- Temperature graphs
- Frontend forecast screens
- AI weather explanations

---

# 7. Daily Forecast

## Endpoint

GET /forecast/daily/{city}

### Purpose

Returns daily forecast information.

### Default

7 days

### Example

GET /forecast/daily/Bengaluru

### Custom number of days

GET /forecast/daily/Bengaluru?days=3

### Maximum

7 days

### Example response structure

[
    {
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "forecast_date": "...",
        "temperature_max_c": 28.0,
        "temperature_min_c": 20.0,
        "apparent_temperature_max_c": 29.0,
        "apparent_temperature_min_c": 20.0,
        "precipitation_sum_mm": 5.0,
        "rain_sum_mm": 4.0,
        "weather_code": 61
    }
]

### Useful for

- 7-day forecast
- Daily weather cards
- Rain forecasts
- AI-generated daily summaries
- Frontend dashboards

---

# 8. Combined Forecast

## Endpoint

GET /forecast/{city}

### Purpose

Returns both hourly and daily forecast data.

### Example

GET /forecast/Bengaluru

### Response structure

{
    "city": "Bengaluru",

    "hourly_forecast": [
        {
            "forecast_time": "...",
            "temperature_c": 25.0,
            "humidity_percent": 70,
            "precipitation_mm": 0.0,
            "rain_mm": 0.0,
            "weather_code": 1,
            "wind_speed_kmh": 10.0,
            "wind_direction_degree": 180
        }
    ],

    "daily_forecast": [
        {
            "forecast_date": "...",
            "temperature_max_c": 28.0,
            "temperature_min_c": 20.0,
            "apparent_temperature_max_c": 29.0,
            "apparent_temperature_min_c": 20.0,
            "precipitation_sum_mm": 5.0,
            "rain_sum_mm": 4.0,
            "weather_code": 61
        }
    ]
}

### Data returned

- Up to 168 hourly records
- Up to 7 daily records

### Useful for

- Complete weather dashboard
- Chatbot
- AI processing
- Frontend
- Weather reports

---

# 9. Weather Summary

## Endpoint

GET /weather/summary/{city}

### Purpose

Returns current weather together with today's forecast.

### Example

GET /weather/summary/Bengaluru

### Response structure

{
    "city": "Bengaluru",
    "state": "Karnataka",
    "country": "India",

    "current_weather": {
        "recorded_at": "...",
        "temperature_c": 25.0,
        "humidity_percent": 70,
        "apparent_temperature_c": 26.0,
        "rain_mm": 0.0,
        "weather_code": 1,
        "wind_speed_kmh": 10.0
    },

    "today_forecast": {
        "forecast_date": "...",
        "temperature_max_c": 28.0,
        "temperature_min_c": 20.0,
        "precipitation_sum_mm": 5.0,
        "rain_sum_mm": 4.0,
        "weather_code": 61
    }
}

### Useful for

- Chatbot responses
- AI-generated summaries
- Voice assistant
- Weather overview
- Frontend summary cards

---

# 10. Supported Cities

Currently supported:

1. Bengaluru
2. Mumbai
3. Delhi
4. Chennai
5. Hyderabad

City names are case-insensitive.

Examples:

/weather/current/Bengaluru

/weather/current/bengaluru

/weather/current/BENGALURU

All refer to the same city.

---

# 11. Error Responses

## Unknown city

Example:

GET /weather/current/ABC

Response:

404

{
    "detail": "Current weather not found"
}

---

## Invalid hourly forecast range

Example:

GET /forecast/hourly/Bengaluru?hours=200

Response:

400

{
    "detail": "hours must be between 1 and 168"
}

---

## Invalid daily forecast range

Example:

GET /forecast/daily/Bengaluru?days=10

Response:

400

{
    "detail": "days must be between 1 and 7"
}

---

# 12. API Usage with Python

Example:

import requests

url = "http://127.0.0.1:8000/weather/current/Bengaluru"

response = requests.get(url)

data = response.json()

print(data)


---

# 13. Example for the Chatbot

A chatbot can request:

GET /weather/summary/Bengaluru

Then use the returned information to generate a natural-language response.

Example flow:

User:

"What is the weather in Bengaluru?"

Chatbot:

1. Identify location = Bengaluru
2. Call WeatherGPT API
3. Receive weather JSON
4. Send relevant information to AI model
5. Generate natural-language answer

---

# 14. Example for Frontend

The frontend can request:

GET /forecast/Bengaluru

The frontend can then use:

hourly_forecast

for hourly charts.

It can use:

daily_forecast

for 7-day forecast cards.

---

# 15. Important Note About Localhost

The current API uses:

http://127.0.0.1:8000

This means the API is running on the computer where FastAPI is started.

Other team members cannot access your localhost directly from their own computers.

For the final project, the API can later be deployed to a server/cloud platform.

---

# 16. Swagger Documentation

FastAPI automatically provides interactive API documentation.

Open:

http://127.0.0.1:8000/docs

From there, team members can:

- See all endpoints
- Enter city names
- Enter hours/days
- Execute API requests
- View JSON responses

---

# 17. Weather Data Flow

Open-Meteo
    ↓
Python weather API module
    ↓
PostgreSQL
    ↓
FastAPI
    ↓
WeatherGPT AI / Frontend / Analytics

---

# 18. Person 1 Responsibilities

Person 1 is responsible for:

- Weather API data collection
- Data cleaning
- Data validation
- PostgreSQL storage
- Historical weather data
- Forecast data
- FastAPI endpoints
- API documentation

Other team members should use the API rather than directly modifying the database.

---

# 19. Main API Endpoints

| Endpoint | Purpose |
|---|---|
| / | API health check |
| /cities | List supported cities |
| /weather/current/{city} | Current weather |
| /forecast/hourly/{city} | Hourly forecast |
| /forecast/daily/{city} | Daily forecast |
| /forecast/{city} | Hourly + daily forecast |
| /weather/summary/{city} | Current weather + today's forecast |

---

# 20. API Status

WeatherGPT Weather Data API

Status: Development version

Data source: Open-Meteo

Database: PostgreSQL

Backend: FastAPI

Supported locations: Bengaluru, Mumbai, Delhi, Chennai, Hyderabad