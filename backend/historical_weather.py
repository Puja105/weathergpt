import requests
import pandas as pd


def get_historical_weather(
    latitude,
    longitude,
    start_date,
    end_date
):

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "start_date": start_date,
        "end_date": end_date,

        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "cloud_cover,"
            "wind_speed_10m,"
            "wind_direction_10m"
        ),

        "timezone": "Asia/Kolkata"
    }

    response = requests.get(
        url,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(
        data["hourly"]
    )

    df["latitude"] = latitude
    df["longitude"] = longitude

    return df


if __name__ == "__main__":

    for location in [
        {
            "city": "Bengaluru",
            "latitude": 12.9716,
            "longitude": 77.5946
        },
        {
            "city": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777
        },
        {
            "city": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090
        },
        {
            "city": "Chennai",
            "latitude": 13.0827,
            "longitude": 80.2707
        },
        {
            "city": "Hyderabad",
            "latitude": 17.3850,
            "longitude": 78.4867
        }
    ]:

        print(
            f"Downloading historical data for "
            f"{location['city']}..."
        )

        df = get_historical_weather(
            latitude=location["latitude"],
            longitude=location["longitude"],
            start_date="2025-01-01",
            end_date="2025-12-31"
        )

        filename = (
            f"data/"
            f"{location['city'].lower()}_historical_weather.csv"
        )

        df.to_csv(
            filename,
            index=False
        )

        print(
            f"Saved: {filename}"
        )

    print("\nAll historical datasets downloaded.")