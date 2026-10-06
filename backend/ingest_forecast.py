from datetime import datetime

from backend.database import get_connection
from backend.forecast_api import get_forecast
from backend.locations import LOCATIONS
def save_forecast_data():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        for location in LOCATIONS:

            print(
                f"\nFetching forecast for {location['city']}..."
            )

            data = get_forecast(
                latitude=location["latitude"],
                longitude=location["longitude"]
            )

            location_id = None

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
                print(
                    f"Location not found: {location['city']}"
                )
                continue

            location_id = result[0]

            # -----------------------------
            # SAVE HOURLY FORECAST
            # -----------------------------

            hourly = data["hourly"]

            for i in range(len(hourly["time"])):

                forecast_time = datetime.fromisoformat(
                    hourly["time"][i]
                )

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
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )

                    ON CONFLICT
                    (location_id, forecast_time)

                    DO UPDATE SET
                        temperature_c =
                            EXCLUDED.temperature_c,

                        humidity_percent =
                            EXCLUDED.humidity_percent,

                        precipitation_mm =
                            EXCLUDED.precipitation_mm,

                        rain_mm =
                            EXCLUDED.rain_mm,

                        weather_code =
                            EXCLUDED.weather_code,

                        wind_speed_kmh =
                            EXCLUDED.wind_speed_kmh,

                        wind_direction_degree =
                            EXCLUDED.wind_direction_degree;
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

            # -----------------------------
            # SAVE DAILY FORECAST
            # -----------------------------

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
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )

                    ON CONFLICT
                    (location_id, forecast_date)

                    DO UPDATE SET
                        temperature_max_c =
                            EXCLUDED.temperature_max_c,

                        temperature_min_c =
                            EXCLUDED.temperature_min_c,

                        apparent_temperature_max_c =
                            EXCLUDED.apparent_temperature_max_c,

                        apparent_temperature_min_c =
                            EXCLUDED.apparent_temperature_min_c,

                        precipitation_sum_mm =
                            EXCLUDED.precipitation_sum_mm,

                        rain_sum_mm =
                            EXCLUDED.rain_sum_mm,

                        weather_code =
                            EXCLUDED.weather_code;
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

            print(
                f"Forecast saved for {location['city']}"
            )

        connection.commit()

        print(
            "\nForecast data ingestion completed successfully."
        )

    except Exception as error:

        connection.rollback()

        print(
            f"\nError while inserting forecast data: {error}"
        )

    finally:

        cursor.close()
        connection.close()


if __name__ == "__main__":
    save_forecast_data()