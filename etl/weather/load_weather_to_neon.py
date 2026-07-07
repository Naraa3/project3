import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://neondb_owner:npg_MBG4insD6VQe@ep-old-recipe-atuuayxa-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

engine = create_engine(DATABASE_URL)

current_df = pd.read_csv("data/clean/weather/weather_current_clean.csv")
forecast_df = pd.read_csv("data/clean/weather/weather_forecast_clean.csv")

current_df.to_sql(
    name="weather_current",
    con=engine,
    if_exists="replace",
    index=False
)

forecast_df.to_sql(
    name="weather_forecast",
    con=engine,
    if_exists="replace",
    index=False
)

print("Weather tables loaded to Neon.")