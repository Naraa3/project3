##
#   Extract — hotels, restaurants, and tourist activities
#   Resumable: skips cities that already have a saved CSV, so you can
#   run this across multiple sessions (e.g. if Overpass rate-limits you)
#   without redoing or erasing what's already done.
#
#   Usage:
#     python etl/OSM/extract_city.py                 -> run all cities, skip ones already saved
#     python etl/OSM/extract_city.py --force          -> re-run ALL cities, overwriting saved ones
#     python etl/OSM/extract_city.py Paris Lyon        -> run only these cities (skips if saved, unless --force)
#     python etl/OSM/extract_city.py --force Paris     -> force re-run just Paris
#     python etl/OSM/extract_city.py --retry-failed    -> re-run only cities that failed last time
##

import sys
import time
import requests
import pandas as pd
from pathlib import Path

url = "https://overpass-api.de/api/interpreter"

headers = {
    "User-Agent": "TourInsight/1.0 (student project)"
}

OUTPUT_DIR = Path("data/raw/cities")
FAILED_LOG = OUTPUT_DIR / "_failed_cities.txt"

# Your full city list
CITIES = [
    "Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg",
    "Montpellier", "Bordeaux", "Lille", "Rennes", "Reims", "Le Havre",
    "Saint-Étienne", "Toulon", "Grenoble", "Dijon", "Angers", "Nîmes",
    "Aix-en-Provence", "Avignon", "Annecy", "Cannes", "Antibes", "Biarritz",
    "La Rochelle", "Colmar", "Bayonne", "Perpignan", "Carcassonne", "Arles",
    "Chamonix", "Rouen", "Tours", "Orléans", "Nancy", "Metz", "Besançon",
    "Clermont-Ferrand", "Saint-Malo", "Lourdes", "Deauville", "Blois",
    "Amboise", "Sarlat-la-Canéda", "Épernay", "Menton", "Saint-Tropez",
    "Ajaccio", "Bastia", "Mont-Saint-Michel", "Versailles", "Honfleur",
]

# Which OSM tag=value pairs count as "activities/attractions".
TAGS = {
    "tourism": ["hotel", "museum", "attraction", "viewpoint", "artwork",
                "gallery", "zoo", "theme_park"],
    "amenity": ["restaurant"],
    "leisure": ["park", "garden"],
    "historic": ["monument", "castle", "memorial", "ruins"],
    "natural": ["beach"],
}

TAG_PRIORITY = ["tourism", "amenity", "leisure", "historic", "natural"]

# Seconds to wait between cities, to stay within Overpass's fair-use limits.
DELAY_BETWEEN_REQUESTS = 5


def output_path(city):
    import unicodedata
    filename = city.lower().replace(" ", "_")
    filename = unicodedata.normalize('NFKD', filename).encode('ascii',
    'ignore').decode('ascii')
    return OUTPUT_DIR / f"{filename}.csv"


def build_query(city):
    clauses = []
    for key, values in TAGS.items():
        value_list = "|".join(values)
        clauses.append(f'  nwr["{key}"~"^({value_list})$"](area.searchArea);')

    return f"""
[out:json][timeout:180];
area["name"="{city}"]["country"="France"]->.searchArea;
"""



def extract_city(city):
    print(f"\nExtracting data for {city}...")

    query = build_query(city)

    try:
        response = requests.post(
            url,
            data={"data": query},
            headers=headers,
            timeout=240
        )
    except requests.exceptions.RequestException as e:
        print(f"Request error for {city}: {e}")
        return False

    if response.status_code != 200:
        print(f"Request failed for {city}:", response.status_code)
        print(response.text[:500])
        return False

    data = response.json()
    elements = data.get("elements", [])

    rows = []

    for el in elements:
        tags = el.get("tags", {})

        category = None
        for key in TAG_PRIORITY:
            if key in tags and tags[key] in TAGS[key]:
                category = tags[key]
                break

        if category is None:
            continue

        lat = el.get("lat")
        lon = el.get("lon")
        if lat is None or lon is None:
            center = el.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")

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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = output_path(city)
    if df.empty:
        print(f"No data found for {city}")
        return False
    else:
        df.to_csv(out_file, index=False, encoding='utf-8')

    print(f"{city}: {len(df)} rows")
    if not df.empty:
        print(df["category"].value_counts())
    print(f"Saved file: {out_file}")
    return True


def load_failed():
    if FAILED_LOG.exists():
        return [line.strip() for line in FAILED_LOG.read_text().splitlines() if line.strip()]
    return []


def save_failed(failed_cities):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if failed_cities:
        FAILED_LOG.write_text("\n".join(failed_cities))
    elif FAILED_LOG.exists():
        FAILED_LOG.unlink()  # clean up once nothing is failing anymore


if __name__ == "__main__":
    args = sys.argv[1:]

    force = "--force" in args
    retry_failed = "--retry-failed" in args
    args = [a for a in args if a not in ("--force", "--retry-failed")]

    if retry_failed:
        cities_to_run = load_failed()
        if not cities_to_run:
            print("No failed cities logged — nothing to retry.")
            sys.exit()
        force = True  # always re-run failed cities regardless of any leftover partial file
    elif args:
        cities_to_run = args
    else:
        cities_to_run = CITIES

    # Skip cities that already have a saved file, unless --force was passed
    if not force:
        already_done = [c for c in cities_to_run if output_path(c).exists()]
        cities_to_run = [c for c in cities_to_run if not output_path(c).exists()]
        if already_done:
            print(f"Skipping {len(already_done)} already-extracted cities: {', '.join(already_done)}")

    if not cities_to_run:
        print("Nothing to do — all requested cities already have saved data. Use --force to re-run anyway.")
        sys.exit()

    print(f"Running extraction for {len(cities_to_run)} cities: {', '.join(cities_to_run)}")

    succeeded = []
    failed = []

    for i, city in enumerate(cities_to_run):
        ok = extract_city(city)
        (succeeded if ok else failed).append(city)

        if i < len(cities_to_run) - 1:
            time.sleep(DELAY_BETWEEN_REQUESTS)

    save_failed(failed)

    print("\n--- Summary ---")
    print(f"Succeeded ({len(succeeded)}): {', '.join(succeeded) if succeeded else '-'}")
    print(f"Failed ({len(failed)}): {', '.join(failed) if failed else '-'}")
    if failed:
        print(f"\nFailed cities saved to {FAILED_LOG} — run with --retry-failed to retry just these.")