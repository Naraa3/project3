import json
import pandas as pd
from pathlib import Path
from datetime import datetime

today = datetime.now().strftime("%Y-%m-%d")

input_file = Path(f"data/raw/weather/weather_raw_{today}.json")
output_folder = Path("data/clean/weather")
output_folder.mkdir(parents=True, exist_ok=True)

with open(input_file, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

current_rows = []
forecast_rows = []

fetched_at = datetime.now()

for item in raw_data:
    city = item["city"]
    current = item.get("current", {})

    current_rows.append({
        "city": city,
        "fetched_at": fetched_at,
        "temperature_c": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "precipitation_mm": current.get("precipitation"),
        "rain_mm": current.get("rain"),
        "weather_code": current.get("weather_code"),
        "wind_speed_kmh": current.get("wind_speed_10m")
    })

    daily = item.get("daily", {})

    for i, date in enumerate(daily.get("time", [])):
        forecast_rows.append({
            "city": city,
            "forecast_date": date,
            "temperature_max_c": daily.get("temperature_2m_max", [])[i],
            "temperature_min_c": daily.get("temperature_2m_min", [])[i],
            "precipitation_sum_mm": daily.get("precipitation_sum", [])[i],
            "precipitation_probability_max": daily.get("precipitation_probability_max", [])[i],
            "fetched_at": fetched_at
        })

current_df = pd.DataFrame(current_rows)
forecast_df = pd.DataFrame(forecast_rows)

current_df.to_csv(output_folder / "weather_current_clean.csv", index=False)
forecast_df.to_csv(output_folder / "weather_forecast_clean.csv", index=False)

print("Weather transformation complete.")