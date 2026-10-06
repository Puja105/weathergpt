import requests


def get_forecast(latitude: float, longitude: float):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": (
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

        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "wind_speed_10m,"
            "wind_direction_10m"
        ),

        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "apparent_temperature_max,"
            "apparent_temperature_min,"
            "precipitation_sum,"
            "rain_sum,"
            "weather_code"
        ),

        "timezone": "Asia/Kolkata",

        "forecast_days": 7
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":

    data = get_forecast(
        latitude=12.9716,
        longitude=77.5946
    )

    print("\nCURRENT WEATHER")
    print(data["current"])

    print("\nHOURLY FORECAST")

    hourly = data["hourly"]

    for i in range(5):

        print(
            hourly["time"][i],
            "|",
            hourly["temperature_2m"][i],
            "°C |",
            hourly["relative_humidity_2m"][i],
            "% humidity |",
            hourly["rain"][i],
            "mm rain"
        )

    print("\nDAILY FORECAST")

    daily = data["daily"]

    for i in range(len(daily["time"])):

        print(
            daily["time"][i],
            "| Max:",
            daily["temperature_2m_max"][i],
            "°C | Min:",
            daily["temperature_2m_min"][i],
            "°C | Rain:",
            daily["rain_sum"][i],
            "mm"
        )