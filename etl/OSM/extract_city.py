##
#   New Extract
##


import sys
import requests
import pandas as pd
from pathlib import Path

url = "https://overpass-api.de/api/interpreter"

headers = {
    "User-Agent": "TourInsight/1.0 (student project)"
}

# Get city from command line
if len(sys.argv) < 2:
    print("Please provide a city name.")
    print("Example: python etl/extract_city.py Paris")
    sys.exit()

city = sys.argv[1]

print(f"Extracting data for {city}...")

query = f"""
[out:json][timeout:180];
area["name"="{city}"]->.searchArea;

(
  node["tourism"="hotel"](area.searchArea);
  node["amenity"="restaurant"](area.searchArea);
);

out body;
"""

response = requests.post(
    url,
    data={"data": query},
    headers=headers,
    timeout=240
)

if response.status_code != 200:
    print(f"Request failed for {city}:", response.status_code)
    print(response.text[:500])
    sys.exit()

data = response.json()
elements = data.get("elements", [])

rows = []

for el in elements:
    tags = el.get("tags", {})

    category = tags.get("tourism") or tags.get("amenity")
    lat = el.get("lat")
    lon = el.get("lon")

    street_address = " ".join(filter(None, [
        tags.get("addr:housenumber"),
        tags.get("addr:street")
    ]))

    full_address = ", ".join(filter(None, [
        street_address,
        tags.get("addr:postcode"),
        tags.get("addr:city")
    ]))

    rows.append({
        "osm_id": el.get("id"),
        "osm_type": el.get("type"),
        "name": tags.get("name"),
        "category": category,
        "city": city,
        "address": full_address,
        "postcode": tags.get("addr:postcode"),
        "website": tags.get("website"),
        "lat": lat,
        "lon": lon
    })

df = pd.DataFrame(rows)

output_dir = Path("data/raw/cities")
output_dir.mkdir(parents=True, exist_ok=True)

filename = city.lower().replace(" ", "_")
output_file = output_dir / f"{filename}.csv"

df.to_csv(output_file, index=False)

print(df.head())
print(f"{city}: {len(df)} rows")
print(f"Saved file: {output_file}")