from datetime import datetime

from backend.database import get_connection
from backend.forecast_api import get_forecast
from backend.locations import LOCATIONS

def save_forecast_data():

    for location in LOCATIONS:

        print(f"\nFetching forecast for {location['city']}...")

        # STEP 1: Fetch weather before connecting to Neon
        try:
            data = get_forecast(
                latitude=location["latitude"],
                longitude=location["longitude"]
            )

        except Exception as error:
            print(f"Error fetching {location['city']}: {error}")
            continue

        connection = None
        cursor = None

        try:
            # STEP 2: Open a database connection for this city
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT location_id
                FROM locations
                WHERE city = %s;
                """,
                (location["city"],)
            )

            result = cursor.fetchone()

            if result is None:
                print(f"Location not found: {location['city']}")
                continue

            location_id = result[0]

            # STEP 3: SAVE CURRENT WEATHER

            current = data["current"]

            recorded_at = datetime.fromisoformat(current["time"])

            cursor.execute(
                """
                SELECT weather_id
                FROM weather_data
                WHERE location_id = %s
                AND recorded_at = %s;
                """,
                (location_id, recorded_at)
            )

            existing_weather = cursor.fetchone()

            if existing_weather:

                cursor.execute(
                    """
                    UPDATE weather_data
                    SET
                        temperature_c = %s,
                        humidity_percent = %s,
                        apparent_temperature_c = %s,
                        precipitation_mm = %s,
                        rain_mm = %s,
                        weather_code = %s,
                        cloud_cover_percent = %s,
                        wind_speed_kmh = %s,
                        wind_direction_degree = %s
                    WHERE weather_id = %s;
                    """,
                    (
                        current["temperature_2m"],
                        current["relative_humidity_2m"],
                        current["apparent_temperature"],
                        current["precipitation"],
                        current["rain"],
                        current["weather_code"],
                        current["cloud_cover"],
                        current["wind_speed_10m"],
                        current["wind_direction_10m"],
                        existing_weather[0]
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO weather_data
                    (
                        location_id,
                        recorded_at,
                        temperature_c,
                        humidity_percent,
                        apparent_temperature_c,
                        precipitation_mm,
                        rain_mm,
                        weather_code,
                        cloud_cover_percent,
                        wind_speed_kmh,
                        wind_direction_degree
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        location_id,
                        recorded_at,
                        current["temperature_2m"],
                        current["relative_humidity_2m"],
                        current["apparent_temperature"],
                        current["precipitation"],
                        current["rain"],
                        current["weather_code"],
                        current["cloud_cover"],
                        current["wind_speed_10m"],
                        current["wind_direction_10m"]
                    )
                )

            print(f"Current weather saved for {location['city']} ({recorded_at})")

            # STEP 4: SAVE HOURLY FORECAST

            hourly = data["hourly"]

            for i in range(len(hourly["time"])):

                forecast_time = datetime.fromisoformat(hourly["time"][i])

                cursor.execute(
                    """
                    INSERT INTO hourly_forecast
                    (
                        location_id,
                        forecast_time,
                        temperature_c,
                        humidity_percent,
                        precipitation_mm,
                        rain_mm,
                        weather_code,
                        wind_speed_kmh,
                        wind_direction_degree
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (location_id, forecast_time)
                    DO UPDATE SET
                        temperature_c = EXCLUDED.temperature_c,
                        humidity_percent = EXCLUDED.humidity_percent,
                        precipitation_mm = EXCLUDED.precipitation_mm,
                        rain_mm = EXCLUDED.rain_mm,
                        weather_code = EXCLUDED.weather_code,
                        wind_speed_kmh = EXCLUDED.wind_speed_kmh,
                        wind_direction_degree = EXCLUDED.wind_direction_degree;
                    """,
                    (
                        location_id,
                        forecast_time,
                        hourly["temperature_2m"][i],
                        hourly["relative_humidity_2m"][i],
                        hourly["precipitation"][i],
                        hourly["rain"][i],
                        hourly["weather_code"][i],
                        hourly["wind_speed_10m"][i],
                        hourly["wind_direction_10m"][i]
                    )
                )

            # STEP 5: SAVE DAILY FORECAST

            daily = data["daily"]

            for i in range(len(daily["time"])):

                forecast_date = daily["time"][i]

                cursor.execute(
                    """
                    INSERT INTO daily_forecast
                    (
                        location_id,
                        forecast_date,
                        temperature_max_c,
                        temperature_min_c,
                        apparent_temperature_max_c,
                        apparent_temperature_min_c,
                        precipitation_sum_mm,
                        rain_sum_mm,
                        weather_code
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (location_id, forecast_date)
                    DO UPDATE SET
                        temperature_max_c = EXCLUDED.temperature_max_c,
                        temperature_min_c = EXCLUDED.temperature_min_c,
                        apparent_temperature_max_c = EXCLUDED.apparent_temperature_max_c,
                        apparent_temperature_min_c = EXCLUDED.apparent_temperature_min_c,
                        precipitation_sum_mm = EXCLUDED.precipitation_sum_mm,
                        rain_sum_mm = EXCLUDED.rain_sum_mm,
                        weather_code = EXCLUDED.weather_code;
                    """,
                    (
                        location_id,
                        forecast_date,
                        daily["temperature_2m_max"][i],
                        daily["temperature_2m_min"][i],
                        daily["apparent_temperature_max"][i],
                        daily["apparent_temperature_min"][i],
                        daily["precipitation_sum"][i],
                        daily["rain_sum"][i],
                        daily["weather_code"][i]
                    )
                )

            print(f"Forecast saved for {location['city']}")

            # STEP 6: COMMIT THIS CITY
            connection.commit()

            print(f"Database changes committed for {location['city']}")

        except Exception as error:

            print(f"Error processing {location['city']}: {error}")

            if connection is not None and not connection.closed:
                try:
                    connection.rollback()
                except Exception as rollback_error:
                    print(f"Rollback failed: {rollback_error}")

        finally:

            if cursor is not None:
                cursor.close()

            if connection is not None:
                connection.close()

    print("\nForecast data ingestion completed.")


if __name__ == "__main__":
    save_forecast_data()