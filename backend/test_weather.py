"""Manual Open-Meteo smoke test: run with `python -m backend.test_weather`."""
from backend.weather_api import get_weather
from backend.locations import LOCATIONS


def main():
    for location in LOCATIONS:
        data = get_weather(
            latitude=location["latitude"],
            longitude=location["longitude"],
        )
        current = data["current"]
        print(
            f"{location['city']}: {current['temperature_2m']} °C, "
            f"humidity {current['relative_humidity_2m']}%, "
            f"wind {current['wind_speed_10m']} km/h"
        )


if __name__ == "__main__":
    main()
