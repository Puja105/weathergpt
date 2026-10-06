import pandas as pd
from pathlib import Path


# Location of the data folder
DATA_FOLDER = Path("data")


# Historical weather files
files = {
    "Bengaluru": "bengaluru_historical_weather.csv",
    "Mumbai": "mumbai_historical_weather.csv",
    "Delhi": "delhi_historical_weather.csv",
    "Chennai": "chennai_historical_weather.csv",
    "Hyderabad": "hyderabad_historical_weather.csv"
}


all_data = []


# Read every city's CSV
for city, filename in files.items():

    file_path = DATA_FOLDER / filename

    print(f"Reading {city} data...")

    df = pd.read_csv(file_path)

    # Add city name
    df["city"] = city

    all_data.append(df)


# Combine all cities
combined_data = pd.concat(
    all_data,
    ignore_index=True
)


# Convert time column to datetime
combined_data["time"] = pd.to_datetime(
    combined_data["time"]
)


# Sort by city and time
combined_data = combined_data.sort_values(
    by=["city", "time"]
)


# Reset row numbers
combined_data = combined_data.reset_index(
    drop=True
)


# Save combined dataset
output_file = DATA_FOLDER / "historical_weather_all_cities.csv"

combined_data.to_csv(
    output_file,
    index=False
)


print("\n--------------------------------")
print("Historical data combined successfully!")
print("--------------------------------")

print(f"Total rows: {len(combined_data)}")
print(f"Total columns: {len(combined_data.columns)}")

print("\nCities:")
print(combined_data["city"].unique())

print("\nColumns:")
print(combined_data.columns.tolist())

print("\nOutput file:")
print(output_file)