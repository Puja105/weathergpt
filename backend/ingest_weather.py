from datetime import datetime

from backend.database import get_connection
from backend.weather_api import get_weather
from backend.locations import LOCATIONS


def save_weather_data():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        for location in LOCATIONS:

            print(
                f"Fetching weather for {location['city']}..."
            )

            # Get weather data from the API
            data = get_weather(
                latitude=location["latitude"],
                longitude=location["longitude"]
            )

            # Get current weather information
            current = data["current"]

            # Convert API timestamp into Python datetime
            recorded_at = datetime.fromisoformat(
                current["time"]
            )

            # Insert new record or update existing record
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
                SELECT
                    location_id,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                FROM locations
                WHERE city = %s

                ON CONFLICT (location_id, recorded_at)
                DO UPDATE SET
                    temperature_c = EXCLUDED.temperature_c,
                    humidity_percent = EXCLUDED.humidity_percent,
                    apparent_temperature_c = EXCLUDED.apparent_temperature_c,
                    precipitation_mm = EXCLUDED.precipitation_mm,
                    rain_mm = EXCLUDED.rain_mm,
                    weather_code = EXCLUDED.weather_code,
                    cloud_cover_percent = EXCLUDED.cloud_cover_percent,
                    wind_speed_kmh = EXCLUDED.wind_speed_kmh,
                    wind_direction_degree = EXCLUDED.wind_direction_degree
                """,
                (
                    recorded_at,
                    current.get("temperature_2m"),
                    current.get("relative_humidity_2m"),
                    current.get("apparent_temperature"),
                    current.get("precipitation"),
                    current.get("rain"),
                    current.get("weather_code"),
                    current.get("cloud_cover"),
                    current.get("wind_speed_10m"),
                    current.get("wind_direction_10m"),
                    location["city"]
                )
            )

            print(
                f"Saved weather for {location['city']}"
            )

        # Save all changes
        connection.commit()

        print(
            "\nWeather data ingestion completed successfully."
        )

    except Exception as error:

        # Undo changes if something goes wrong
        connection.rollback()

        print(
            f"\nError while inserting weather data: {error}"
        )

    finally:

        cursor.close()
        connection.close()


if __name__ == "__main__":
    save_weather_data()