import pandas as pd

input_file = "etl/france_osm_hotels_restaurants.csv"
output_file = "etl/france_osm_hotels_restaurants_clean.csv"

df = pd.read_csv(input_file)

print("Rows before cleaning:", len(df))

# remove rows with no name
df = df.dropna(subset=["name"])

# remove rows with no coordinates
df = df.dropna(subset=["lat", "lon"])

# remove duplicates
df = df.drop_duplicates(subset=["osm_id", "city", "category"])

# standardize category names
df["category"] = df["category"].str.lower().str.strip()

# keep only hotels and restaurants
df = df[df["category"].isin(["hotel", "restaurant"])]

print("Rows after cleaning:", len(df))

df.to_csv(output_file, index=False)

print("Saved clean file:", output_file)