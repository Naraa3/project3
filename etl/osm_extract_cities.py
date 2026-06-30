import time
import requests
import pandas as pd

url = "https://overpass.kumi.systems/api/interpreter"

headers = {
    "User-Agent": "TourInsight/1.0 (student project)"
}

cities = [
    "Marseille",
    "Paris",
    "Lyon",
    "Toulouse",
    "Nice",
    "Nantes"
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

        all_rows.append({
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

    print(f"{city}: {len(elements)} rows")
    time.sleep(15)

df = pd.DataFrame(all_rows)

print(df.head())
print("TOTAL ROWS:", len(df))

df.to_csv("data/raw/france_osm_hotels_restaurants.csv", index=False)
print("Saved file: data/raw/france_osm_hotels_restaurants.csv")