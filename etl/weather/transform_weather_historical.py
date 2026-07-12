import json
import pandas as pd
from pathlib import Path

input_folder = Path("data/raw/weather/historical")
output_folder = Path("data/clean/weather")
output_folder.mkdir(parents=True, exist_ok=True)

rows = []
for city_file in input_folder.glob("*.json"):
    with open(city_file, "r", encoding="utf-8") as f:
        item = json.load(f)

    city = item["city"]
    daily = item.get("daily", {})
    dates = daily.get("time", [])

    for i, d in enumerate(dates):
        rows.append({
            "city": city,
            "date": d,
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "precip_sum": daily["precipitation_sum"][i],
        })

df = pd.DataFrame(rows)
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.month

monthly = (
    df.groupby(["city", "month"])
    .agg(avg_temp_max=("temp_max", "mean"), avg_temp_min=("temp_min", "mean"), avg_precip=("precip_sum", "mean"))
    .reset_index()
    .round(1)
)

monthly.to_csv(output_folder / "weather_historical_monthly.csv", index=False)
print(f"Historical transformation complete. {len(monthly)} rows from {df['city'].nunique()} cities.")