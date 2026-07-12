import pandas as pd
from pathlib import Path

input_folder = Path("data/raw/cities")
output_folder = Path("data/clean")
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "france_osm_poi_clean.csv"

# Map raw OSM tag values -> a clean, standardized category label.
# Anything not in this dict gets dropped.
CATEGORY_MAP = {
    "hotel": "hotel",
    "restaurant": "restaurant",
    "museum": "museum",
    "attraction": "attraction",
    "viewpoint": "viewpoint",
    "artwork": "artwork",
    "gallery": "gallery",
    "zoo": "zoo",
    "theme_park": "theme_park",
    "park": "park",
    "garden": "garden",
    "monument": "historic_site",
    "castle": "historic_site",
    "memorial": "historic_site",
    "ruins": "historic_site",
    "beach": "beach",
}

csv_files = list(input_folder.glob("*.csv"))

if not csv_files:
    print("No city CSV files found in data/raw/cities")
    exit()

dataframes = []

for file in csv_files:
    print(f"Reading {file.name}")
    df = pd.read_csv(file)
    dataframes.append(df)

df = pd.concat(dataframes, ignore_index=True)

print("Rows before cleaning:", len(df))

df = df.dropna(subset=["name"])
df = df.dropna(subset=["lat", "lon"])

df = df.drop_duplicates(subset=["osm_id", "city", "category"])

df["category"] = df["category"].str.lower().str.strip()

# Keep only known categories, and standardize their labels
df = df[df["category"].isin(CATEGORY_MAP.keys())].copy()
df["category"] = df["category"].map(CATEGORY_MAP)

if "address" in df.columns:
    df["address"] = df["address"].fillna("")

if "postcode" in df.columns:
    df["postcode"] = df["postcode"].fillna("")

if "website" in df.columns:
    df["website"] = df["website"].fillna("")

print("Rows after cleaning:", len(df))
print(df["category"].value_counts())

df.to_csv(output_file, index=False)

print(f"Saved clean file: {output_file}")