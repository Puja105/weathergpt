from fastapi import FastAPI, HTTPException
from backend.database import get_connection
from backend.chatbot import router as chatbot_router


app = FastAPI(
    title="WeatherGPT Data API",
    description="Weather data API for the WeatherGPT project",
    version="1.0.0"
)

app.include_router(chatbot_router)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "WeatherGPT Data API is running"
    }


# ============================================================
# GET ALL LOCATIONS
# ============================================================

@app.get("/locations")
def get_locations():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                location_id,
                city,
                state,
                country,
                latitude,
                longitude
            FROM locations
            ORDER BY city;
            """
        )

        rows = cursor.fetchall()

        locations = []

        for row in rows:

            locations.append({
                "location_id": row[0],
                "city": row[1],
                "state": row[2],
                "country": row[3],
                "latitude": row[4],
                "longitude": row[5]
            })

        return locations

    finally:

        cursor.close()
        connection.close()


# ============================================================
# GET CITIES
# ============================================================

@app.get("/cities")
def get_cities():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                location_id,
                city,
                state,
                country
            FROM locations
            ORDER BY city;
            """
        )

        rows = cursor.fetchall()

        cities = []

        for row in rows:

            cities.append({
                "location_id": row[0],
                "city": row[1],
                "state": row[2],
                "country": row[3]
            })

        return {
            "count": len(cities),
            "cities": cities
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# GET CURRENT WEATHER
# ============================================================

@app.get("/weather/current/{city}")
def get_current_weather(city: str):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                l.city,
                l.state,
                l.country,
                w.recorded_at,
                w.temperature_c,
                w.humidity_percent,
                w.apparent_temperature_c,
                w.precipitation_mm,
                w.rain_mm,
                w.weather_code,
                w.cloud_cover_percent,
                w.wind_speed_kmh,
                w.wind_direction_degree

            FROM weather_data w

            JOIN locations l
                ON w.location_id = l.location_id

            WHERE LOWER(l.city) = LOWER(%s)

            ORDER BY w.recorded_at DESC

            LIMIT 1;
            """,
            (city,)
        )

        row = cursor.fetchone()

        if row is None:

            raise HTTPException(
                status_code=404,
                detail="Weather data not found"
            )

        return {
            "city": row[0],
            "state": row[1],
            "country": row[2],
            "recorded_at": row[3],
            "temperature_c": row[4],
            "humidity_percent": row[5],
            "apparent_temperature_c": row[6],
            "precipitation_mm": row[7],
            "rain_mm": row[8],
            "weather_code": row[9],
            "cloud_cover_percent": row[10],
            "wind_speed_kmh": row[11],
            "wind_direction_degree": row[12]
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# HOURLY FORECAST
# ============================================================

@app.get("/forecast/hourly/{city}")
def get_hourly_forecast(
    city: str,
    hours: int = 24
):

    # Validate hours

    if hours < 1 or hours > 168:

        raise HTTPException(
            status_code=400,
            detail="hours must be between 1 and 168"
        )

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                l.city,
                l.state,
                l.country,
                h.forecast_time,
                h.temperature_c,
                h.humidity_percent,
                h.precipitation_mm,
                h.rain_mm,
                h.weather_code,
                h.wind_speed_kmh,
                h.wind_direction_degree

            FROM hourly_forecast h

            JOIN locations l
                ON h.location_id = l.location_id

            WHERE LOWER(l.city) = LOWER(%s)

            ORDER BY h.forecast_time

            LIMIT %s;
            """,
            (city, hours)
        )

        rows = cursor.fetchall()

        if not rows:

            raise HTTPException(
                status_code=404,
                detail="Hourly forecast not found"
            )

        forecast = []

        for row in rows:

            forecast.append({
                "city": row[0],
                "state": row[1],
                "country": row[2],
                "forecast_time": row[3],
                "temperature_c": row[4],
                "humidity_percent": row[5],
                "precipitation_mm": row[6],
                "rain_mm": row[7],
                "weather_code": row[8],
                "wind_speed_kmh": row[9],
                "wind_direction_degree": row[10]
            })

        return forecast

    finally:

        cursor.close()
        connection.close()


# ============================================================
# DAILY FORECAST
# ============================================================

@app.get("/forecast/daily/{city}")
def get_daily_forecast(
    city: str,
    days: int = 7
):

    # Validate days

    if days < 1 or days > 7:

        raise HTTPException(
            status_code=400,
            detail="days must be between 1 and 7"
        )

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                l.city,
                l.state,
                l.country,
                d.forecast_date,
                d.temperature_max_c,
                d.temperature_min_c,
                d.apparent_temperature_max_c,
                d.apparent_temperature_min_c,
                d.precipitation_sum_mm,
                d.rain_sum_mm,
                d.weather_code

            FROM daily_forecast d

            JOIN locations l
                ON d.location_id = l.location_id

            WHERE LOWER(l.city) = LOWER(%s)

            ORDER BY d.forecast_date

            LIMIT %s;
            """,
            (city, days)
        )

        rows = cursor.fetchall()

        if not rows:

            raise HTTPException(
                status_code=404,
                detail="Daily forecast not found"
            )

        forecast = []

        for row in rows:

            forecast.append({
                "city": row[0],
                "state": row[1],
                "country": row[2],
                "forecast_date": row[3],
                "temperature_max_c": row[4],
                "temperature_min_c": row[5],
                "apparent_temperature_max_c": row[6],
                "apparent_temperature_min_c": row[7],
                "precipitation_sum_mm": row[8],
                "rain_sum_mm": row[9],
                "weather_code": row[10]
            })

        return forecast

    finally:

        cursor.close()
        connection.close()


# ============================================================
# COMBINED FORECAST
# ============================================================

@app.get("/forecast/{city}")
def get_forecast(city: str):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # GET HOURLY FORECAST
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                h.forecast_time,
                h.temperature_c,
                h.humidity_percent,
                h.precipitation_mm,
                h.rain_mm,
                h.weather_code,
                h.wind_speed_kmh,
                h.wind_direction_degree

            FROM hourly_forecast h

            JOIN locations l
                ON h.location_id = l.location_id

            WHERE LOWER(l.city) = LOWER(%s)

            ORDER BY h.forecast_time

            LIMIT 168;
            """,
            (city,)
        )

        hourly_rows = cursor.fetchall()

        if not hourly_rows:

            raise HTTPException(
                status_code=404,
                detail="Forecast not found"
            )

        hourly_forecast = []

        for row in hourly_rows:

            hourly_forecast.append({
                "forecast_time": row[0],
                "temperature_c": row[1],
                "humidity_percent": row[2],
                "precipitation_mm": row[3],
                "rain_mm": row[4],
                "weather_code": row[5],
                "wind_speed_kmh": row[6],
                "wind_direction_degree": row[7]
            })

        # ----------------------------------------------------
        # GET DAILY FORECAST
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                d.forecast_date,
                d.temperature_max_c,
                d.temperature_min_c,
                d.apparent_temperature_max_c,
                d.apparent_temperature_min_c,
                d.precipitation_sum_mm,
                d.rain_sum_mm,
                d.weather_code

            FROM daily_forecast d

            JOIN locations l
                ON d.location_id = l.location_id

            WHERE LOWER(l.city) = LOWER(%s)

            ORDER BY d.forecast_date

            LIMIT 7;
            """,
            (city,)
        )

        daily_rows = cursor.fetchall()

        daily_forecast = []

        for row in daily_rows:

            daily_forecast.append({
                "forecast_date": row[0],
                "temperature_max_c": row[1],
                "temperature_min_c": row[2],
                "apparent_temperature_max_c": row[3],
                "apparent_temperature_min_c": row[4],
                "precipitation_sum_mm": row[5],
                "rain_sum_mm": row[6],
                "weather_code": row[7]
            })

        return {
            "city": city,
            "hourly_forecast": hourly_forecast,
            "daily_forecast": daily_forecast
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# WEATHER SUMMARY
# ============================================================

@app.get("/weather/summary/{city}")
def get_weather_summary(city: str):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # GET CURRENT WEATHER
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                l.city,
                l.state,
                l.country,
                w.recorded_at,
                w.temperature_c,
                w.humidity_percent,
                w.apparent_temperature_c,
                w.rain_mm,
                w.weather_code,
                w.wind_speed_kmh

            FROM weather_data w

            JOIN locations l
                ON w.location_id = l.location_id

            WHERE LOWER(l.city) = LOWER(%s)

            ORDER BY w.recorded_at DESC

            LIMIT 1;
            """,
            (city,)
        )

        current = cursor.fetchone()

        if current is None:

            raise HTTPException(
                status_code=404,
                detail="Current weather not found"
            )

        # ----------------------------------------------------
        # GET TODAY'S FORECAST
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                d.forecast_date,
                d.temperature_max_c,
                d.temperature_min_c,
                d.precipitation_sum_mm,
                d.rain_sum_mm,
                d.weather_code

            FROM daily_forecast d

            JOIN locations l
                ON d.location_id = l.location_id

            WHERE LOWER(l.city) = LOWER(%s)

            ORDER BY d.forecast_date

            LIMIT 1;
            """,
            (city,)
        )

        today = cursor.fetchone()

        # ----------------------------------------------------
        # RETURN SUMMARY
        # ----------------------------------------------------

        return {
            "city": current[0],
            "state": current[1],
            "country": current[2],

            "current_weather": {
                "recorded_at": current[3],
                "temperature_c": current[4],
                "humidity_percent": current[5],
                "apparent_temperature_c": current[6],
                "rain_mm": current[7],
                "weather_code": current[8],
                "wind_speed_kmh": current[9]
            },

            "today_forecast": {
                "forecast_date": today[0] if today else None,
                "temperature_max_c": today[1] if today else None,
                "temperature_min_c": today[2] if today else None,
                "precipitation_sum_mm": today[3] if today else None,
                "rain_sum_mm": today[4] if today else None,
                "weather_code": today[5] if today else None
            }
        }

    finally:

        cursor.close()
        connection.close()