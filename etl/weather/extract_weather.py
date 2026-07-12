import json
import requests
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# Get city list + coordinates directly from dim_poi (instead of cities_weather.py)
# This guarantees weather uses the EXACT same city names as your hotels/restaurants data
query = """
    SELECT city, AVG(lat) AS lat, AVG(lon) AS lon
    FROM dim_poi
    WHERE lat IS NOT NULL AND lon IS NOT NULL
    GROUP BY city
"""
CITIES = pd.read_sql(query, engine).to_dict("records")

output_folder = Path("data/raw/weather")
output_folder.mkdir(parents=True, exist_ok=True)
today = datetime.now().strftime("%Y-%m-%d")
output_file = output_folder / f"weather_raw_{today}.json"

all_weather = []

for city in CITIES:
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
        "timezone": "Europe/Paris"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    data["city"] = city["city"]
    data["lat"] = city["lat"]
    data["lon"] = city["lon"]

    all_weather.append(data)

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_weather, f, ensure_ascii=False, indent=4)

print(f"Saved raw weather file: {output_file}")