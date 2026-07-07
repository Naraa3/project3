import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://neondb_owner:npg_MBG4insD6VQe@ep-old-recipe-atuuayxa-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

engine = create_engine(DATABASE_URL)

# Read the cleaned CSV
df = pd.read_csv("data/clean/france_osm_hotels_restaurants_clean.csv")

print(f"Rows to upload: {len(df)}")

# Upload to Neon
df.to_sql(
    name="dim_poi",
    con=engine,
    if_exists="replace",   # Replace the table each time you run the script
    index=False
)

print("Data uploaded successfully!")
print("Table name: dim_poi")