import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

#Connection with Neon db
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Read the cleaned CSV
df = pd.read_csv("data/clean/france_osm_poi_clean.csv")

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