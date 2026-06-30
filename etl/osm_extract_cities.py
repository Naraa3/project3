import time
import requests
import pandas as pd

url = "https://overpass-api.de/api/interpreter"

headers = {
    "User-Agent": "TourInsight/1.0 (student project)"
}

cities = [
    "Paris",
    "Marseille",
    "Lyon",
    "Toulouse",
    "Nice",
    "Nantes",
    "Montpellier",
    "Strasbourg",
    "Bordeaux",
    "Lille"
]

all_rows = []

for city in cities:
    print(f"Extracting data for {city}...")

    query = f"""
    [out:json];
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
        headers=headers
    )

    if response.status_code != 200:
        print(f"Request failed for {city}:", response.status_code)
        print(response.text[:500])
        continue

    data = response.json()
    elements = data.get("elements", [])

    for el in elements:
        tags = el.get("tags", {})
        all_rows.append({
            "osm_id": el.get("id"),
            "osm_type": el.get("type"),
            "city": city,
            "name": tags.get("name"),
            "category": tags.get("tourism") or tags.get("amenity"),
            "lat": el.get("lat"),
            "lon": el.get("lon")
        })

    print(f"{city}: {len(elements)} rows")
    time.sleep(2)

df = pd.DataFrame(all_rows)

print(df.head())
print("TOTAL ROWS:", len(df))

df.to_csv("etl/france_osm_hotels_restaurants.csv", index=False)
print("Saved file: etl/france_osm_hotels_restaurants.csv")
