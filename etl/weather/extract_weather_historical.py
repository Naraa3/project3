import json
import requests
import time
from pathlib import Path
from datetime import date, timedelta
from cities_weather import CITIES

output_folder = Path("data/raw/weather/historical")
output_folder.mkdir(parents=True, exist_ok=True)

end_date = date.today() - timedelta(days=6)
start_date = end_date.replace(year=end_date.year - 3)

def fetch_with_retry(url, params, max_retries=5):
    """Fetch a URL, retrying with exponential backoff on 429."""
    for attempt in range(max_retries):
        response = requests.get(url, params=params)
        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 2 ** (attempt + 2)))
            print(f"  Rate limited. Waiting {wait}s before retry...")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError("Max retries exceeded due to repeated rate limiting.")

for city in CITIES:
    city_file = output_folder / f"{city['city']}.json"

    if city_file.exists():
        print(f"Skipping {city['city']} (already fetched)")
        continue

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Europe/Paris"
    }

    data = fetch_with_retry(url, params)
    data["city"] = city["city"]

    with open(city_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Fetched historical data for {city['city']}")
    time.sleep(3)  # courtesy delay between requests

print("Historical fetch complete.")