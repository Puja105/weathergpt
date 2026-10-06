from backend.weather_api import get_weather
from backend.locations import LOCATIONS


for location in LOCATIONS:

    data = get_weather(
        latitude=location["latitude"],
        longitude=location["longitude"]
    )

    current = data["current"]

    print("\n-----------------------------")
    print(f"City: {location['city']}")
    print(f"Temperature: {current['temperature_2m']} °C")
    print(f"Humidity: {current['relative_humidity_2m']} %")
    print(f"Wind Speed: {current['wind_speed_10m']} km/h")
    print(f"Rain: {current['rain']} mm")